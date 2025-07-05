# app.py
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_tres_securisee' # Changez ceci pour une clé secrète forte en production

# Chemins des fichiers et dossiers
DATA_FILE = 'data.json'
UPLOAD_FOLDER = 'uploads'

# --- DÉBUT DE LA CORRECTION : Création des dossiers et fichiers au démarrage de l'application ---
# Créer le dossier d'uploads s'il n'existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Dossier '{UPLOAD_FOLDER}' créé.") # Message de débogage

# Créer le fichier de données JSON s'il n'existe pas et l'initialiser
if not os.path.exists(DATA_FILE):
    initial_data = {'users': {}, 'theses': []}
    with open(DATA_FILE, 'w') as f:
        json.dump(initial_data, f, indent=4)
    print(f"Fichier '{DATA_FILE}' créé et initialisé.") # Message de débogage
# --- FIN DE LA CORRECTION ---


def load_data():
    """Charge les données des utilisateurs et thèses depuis le fichier JSON."""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Ceci ne devrait normalement plus se produire avec la correction ci-dessus,
        # mais c'est une bonne pratique de garder la gestion d'erreur.
        print(f"Erreur: Le fichier '{DATA_FILE}' est introuvable lors du chargement. Initialisation vide.")
        return {'users': {}, 'theses': []}
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier '{DATA_FILE}' est corrompu ou vide. Initialisation vide.")
        return {'users': {}, 'theses': []}


def save_data(data):
    """Sauvegarde les données des utilisateurs et thèses dans le fichier JSON."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    """Route pour la page d'accueil."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Route pour l'inscription des utilisateurs."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = load_data()

        if username in data['users']:
            flash('Ce nom d\'utilisateur existe déjà. Veuillez en choisir un autre.', 'error')
            return redirect(url_for('register'))

        # Hachage du mot de passe avant de le stocker
        hashed_password = generate_password_hash(password)
        data['users'][username] = {'password': hashed_password}
        save_data(data)
        flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route pour la connexion des utilisateurs."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        data = load_data()

        user = data['users'].get(username)
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Connexion réussie !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Route pour la déconnexion des utilisateurs."""
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Route pour le tableau de bord de l'utilisateur."""
    if not session.get('logged_in'):
        flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
        return redirect(url_for('login'))

    username = session['username']
    data = load_data()
    # Filtrer les thèses téléchargées par l'utilisateur actuel
    user_theses = [thesis for thesis in data['theses'] if thesis['uploader'] == username]
    return render_template('dashboard.html', username=username, theses=user_theses)

@app.route('/upload', methods=['GET', 'POST'])
def upload_thesis():
    """Route pour le téléchargement de thèses."""
    if not session.get('logged_in'):
        flash('Veuillez vous connecter pour télécharger une thèse.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        abstract = request.form['abstract']
        file = request.files['thesis_file']

        if file and file.filename.endswith('.pdf'):
            # Générer un nom de fichier unique pour éviter les conflits
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            data = load_data()
            new_thesis = {
                'id': len(data['theses']) + 1, # Simple ID incrémental
                'title': title,
                'author': author,
                'abstract': abstract,
                'filename': filename,
                'uploader': session['username'],
                'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            data['theses'].append(new_thesis)
            save_data(data)
            flash('Thèse téléchargée avec succès !', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Veuillez sélectionner un fichier PDF valide.', 'error')
            return redirect(url_for('upload_thesis'))
    return render_template('upload.html')

@app.route('/theses')
def browse_theses():
    """Route pour parcourir toutes les thèses disponibles."""
    data = load_data()
    return render_template('theses.html', theses=data['theses'])

@app.route('/download/<filename>')
def download_file(filename):
    """Route pour télécharger un fichier PDF."""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        flash('Le fichier demandé n\'existe pas.', 'error')
        return redirect(url_for('browse_theses'))

if __name__ == '__main__':
    app.run(debug=True) # Mettez debug=False en production

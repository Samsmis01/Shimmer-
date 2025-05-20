from flask import Flask, request, redirect, url_for, render_template, jsonify
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# Configuration de l'application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'user_uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max par fichier
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Création du dossier de stockage
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # Vérification de la présence de fichiers
    if 'photos' not in request.files:
        print("❌ Aucun fichier reçu dans la requête")
        return jsonify({'error': 'Aucun fichier sélectionné'}), 400
    
    files = request.files.getlist('photos')
    if len(files) == 0:
        print("❌ Liste de fichiers vide")
        return jsonify({'error': 'Aucun fichier valide'}), 400
    
    print(f"\n📤 Réception de {len(files)} fichier(s)...")
    
    # Traitement des fichiers
    uploaded_files = []
    for i, file in enumerate(files, 1):
        # Validation du fichier
        if file.filename == '':
            continue
            
        if not allowed_file(file.filename):
            print(f"❌ Format non autorisé: {file.filename}")
            continue
            
        # Sécurisation du nom de fichier
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{timestamp}_{original_filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(save_path)
            uploaded_files.append(original_filename)
            print(f"✅ [{i}/{len(files)}] {original_filename} sauvegardé sous {filename}")
        except Exception as e:
            error_msg = f"Erreur lors de l'enregistrement de {filename}: {str(e)}"
            app.logger.error(error_msg)
            print(f"❌ {error_msg}")
    
    if not uploaded_files:
        print("❌ Aucun fichier n'a pu être enregistré")
        return jsonify({'error': 'Aucun fichier n\'a pu être enregistré'}), 400
    
    print(f"🎉 Transfert réussi - {len(uploaded_files)}/{len(files)} fichier(s) enregistrés\n")
    return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    return """
    <!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmation de réception</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500&family=Playfair+Display:wght@400;500&display=swap');
        
        body {
            font-family: 'Montserrat', sans-serif;
            text-align: center;
            padding: 0;
            margin: 0;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4efe9 100%);
            color: #333;
        }
        
        .container {
            max-width: 600px;
            padding: 40px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            transform: translateY(0);
            opacity: 1;
            animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        
        .success-icon {
            font-size: 80px;
            color: #4CAF50;
            margin-bottom: 20px;
            display: inline-block;
            animation: bounceIn 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        
        h1 {
            font-family: 'Playfair Display', serif;
            font-weight: 500;
            font-size: 32px;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        
        p {
            font-size: 18px;
            line-height: 1.6;
            margin-bottom: 30px;
            color: #7f8c8d;
        }
        
        .divider {
            height: 1px;
            background: linear-gradient(to right, transparent, #e0e0e0, transparent);
            margin: 25px 0;
        }
        
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 50px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            background: #43a047;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes bounceIn {
            0% {
                opacity: 0;
                transform: scale(0.3);
            }
            50% {
                opacity: 1;
                transform: scale(1.05);
            }
            70% {
                transform: scale(0.9);
            }
            100% {
                transform: scale(1);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✓</div>
        <h1>Vos photos ont bien été reçues !</h1>
        <p>Merci pour votre participation. Nous avons pris en compte votre envoi et vous contacterons si nécessaire.</p>
        
        <div class="divider"></div>
        
        <a href="https://t.mehextechcar" class="btn">HEX-TECH</a>
    </div>
</body>
</html>
    """

@app.errorhandler(413)
def request_entity_too_large(error):
    print("❌ Fichier trop volumineux (max 10MB)")
    return jsonify({'error': 'Fichier trop volumineux (max 10MB)'}), 413

@app.errorhandler(404)
def page_not_found(error):
    print("❌ Page non trouvée")
    return jsonify({'error': 'Page non trouvée'}), 404

if __name__ == '__main__':
    print("""\n
    ====================================
    🚀 Serveur Flask en écoute sur http://0.0.0.0:8080
    📁 Dossier de stockage: {}/user_uploads
    🔒 Formats autorisés: {}
    ====================================
    """.format(os.getcwd(), ', '.join(app.config['ALLOWED_EXTENSIONS'])))
    
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=True
    )

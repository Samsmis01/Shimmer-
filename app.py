from flask import Flask, request, redirect
import os
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'user_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload():
    if 'photos' not in request.files:
        return "Aucun fichier reçu", 400
    
    files = request.files.getlist('photos')
    for file in files:
        if file.filename == '':
            continue
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    return redirect('/confirmation')

@app.route('/confirmation')
def confirmation():
    return "Vos photos ont bien été reçues !", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080

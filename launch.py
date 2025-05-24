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

TELEGRAM_LINK = "https://t.me/hextechcar"
LOCAL_PORT = 8080

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def run_server():
    @APP.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return "Aucun fichier", 400
            
        file = request.files['file']
        if file.filename == '':
            return "Nom de fichier invalide", 400
            
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            # Écriture par chunks pour les gros fichiers
            with open(save_path, 'wb') as f:
                chunk_size = 4096
                while True:
                    chunk = file.stream.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
            
            return f"Fichier {filename} reçu", 200
        except Exception as e:
            return f"Erreur: {str(e)}", 500

    @APP.route('/')
    def index():
        return """
        <html>
        <body>
            <h1>Partagez vos médias</h1>
            <form method="post" enctype="multipart/form-data" action="/upload">
                <input type="file" name="file" multiple>
                <input type="submit" value="Envoyer">
            </form>
        </body>
        </html>
        """

    APP.run(host='0.0.0.0', port=LOCAL_PORT, threaded=True)

def start_serveo():
    print(f"\n{Colors.BLUE}[*] Initialisation du tunnel Serveo...{Colors.END}")
    try:
        # Nettoyage des anciens processus
        subprocess.run(["pkill", "-f", "serveo"], stderr=subprocess.DEVNULL)
        
        # Lancement avec timeout étendu
        cmd = [
            "timeout", "60",
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=30",
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
                print(f"\n{Colors.GREEN}╔════════════════════════════════════╗")
                print(f"║  Lien actif pour transfert fichiers  ║")
                print(f"║  {url.ljust(34)}  ║")
                print(f"╚════════════════════════════════════╝{Colors.END}")
                print(f"\n{Colors.YELLOW}[•] Accepte les fichiers jusqu'à 500MB")
                print(f"[•] Restez connecté pendant le transfert{Colors.END}")
                return url
            sleep(1)

        if not url:
            error = process.stderr.read()
            print(f"{Colors.RED}[!] Échec: {error}{Colors.END}")
            return None

    except Exception as e:
        print(f"{Colors.RED}[!] Erreur: {str(e)}{Colors.END}")
        return None

def main_menu():
    os.system('clear')
    print(f"""{Colors.GREEN}
    ██████╗ ███████╗███╗   ██╗ █████╗ ██████╗ ██████╗ 
    ██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔══██╗██╔══██╗
    ██████╔╝█████╗  ██╔██╗ ██║███████║██████╔╝██║  ██║
    ██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║██╔══██╗██║  ██║
    ██║  ██║███████╗██║ ╚████║██║  ██║██║  ██║██████╔╝
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
    {Colors.END}""")
    print(f"[✓] Version: 3.0 | Fichiers lourds supportés\n")

    print(f"""
    {Colors.GREEN}[1]{Colors.END} Rejoindre notre canal Telegram
    {Colors.GREEN}[2]{Colors.END} Générer un lien de transfert
    {Colors.RED}[0]{Colors.END} Quitter
    """)

    try:
        return input(f"{Colors.YELLOW}[?] Choix: {Colors.END}")
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Interrompu{Colors.END}")
        sys.exit(0)

def main():
    # Démarrer le serveur
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    while True:
        choice = main_menu()

        if choice == "1":
            print(f"\n{Colors.GREEN}[+] Ouverture Telegram...{Colors.END}")
            print(f"{Colors.BLUE}Lien: {TELEGRAM_LINK}{Colors.END}")
            webbrowser.open(TELEGRAM_LINK)
            sleep(2)

        elif choice == "2":
            print(f"\n{Colors.BLUE}[*] Préparation du transfert...{Colors.END}")
            url = start_serveo()
            if url:
                print(f"\n{Colors.GREEN}[✓] Prêt à recevoir des fichiers lourds{Colors.END}")
            input("\nAppuyez sur Entrée...")

        elif choice == "0":
            print(f"\n{Colors.RED}[!] Fermeture{Colors.END}")
            sys.exit(0)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"{Colors.RED}[!] Crash: {str(e)}{Colors.END}")
        sys.exit(1

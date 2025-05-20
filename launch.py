#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import time
import webbrowser
from app import app

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def show_banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"""{Colors.GREEN}
      ██╗  ██╗███████╗██╗  ██╗████████╗███████╗ ██████╗██╗  ██╗
██║  ██║██╔════╝╚██╗██╔╝╚══██╔══╝██╔════╝██╔════╝██║  ██║
███████║█████╗   ╚███╔╝    ██║   █████╗  ██║     ███████║
██╔══██║██╔══╝   ██╔██╗    ██║   ██╔══╝  ██║     ██╔══██║
██║  ██║███████╗██╔╝ ██╗   ██║   ███████╗╚██████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝

    {Colors.END}
    [✓] Version: 2.2.0
    [✓] GitHub: SAMSMIS01
    [✓] Telegram: https://t.me/hextechcar
    [✓] Instagram: SAMSMIS01
    [✓] Email: hextech243@gmail.com
    ---------------------------------------------------
    """)

def show_menu():
    print(f"""
    {Colors.GREEN}[1]{Colors.END} Rejoindre le canal Telegram
    {Colors.GREEN}[2]{Colors.END} Générer un lien Serveo
    {Colors.RED}[0]{Colors.END} Quitter
    """)
    try:
        return input(f"{Colors.YELLOW}[?] Choisis une option: {Colors.END}")
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Interruption{Colors.END}")
        sys.exit(0)

def start_serveo():
    print(f"\n{Colors.BLUE}[*] Initialisation du tunnel Serveo...{Colors.END}")
    try:
        process = subprocess.Popen(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:8080", "serveo.net"],
            stderr=subprocess.PIPE,
            text=True
        )

        for _ in range(30):
            line = process.stderr.readline()
            if "Forwarding" in line:
                parts = line.strip().split()
                url = next((p for p in parts if p.startswith("http://")), None)
                if url:
                    print(f"\n{Colors.GREEN}╔══════════════════════════════════╗")
                    print(f"║  Lien Serveo généré avec succès  ║")
                    print(f"║  {url.ljust(32)}  ║")
                    print(f"╚══════════════════════════════════╝{Colors.END}")
                    return url
            time.sleep(1)
        
        print(f"{Colors.RED}[!] Échec après 30 secondes{Colors.END}")
        return None
    except Exception as e:
        print(f"{Colors.RED}[!] Erreur Serveo: {str(e)}{Colors.END}")
        return None

def main():
    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=8080),
        daemon=True
    )
    flask_thread.start()

    while True:
        show_banner()
        choice = show_menu()

        if choice == "1":
            webbrowser.open("https://t.me/hextechcar")
        elif choice == "2":
            url = start_serveo()
            if url:
                webbrowser.open(url)
            input("\nAppuyez sur Entrée pour continuer...")
        elif choice == "0":
            sys.exit(0)
        else:
            print(f"{Colors.RED}[!] Option invalide{Colors.END}")
            time.sleep(1)

if __name__ == '__main__':
    if subprocess.run(["which", "ssh"], capture_output=True).returncode != 0:
        print(f"{Colors.RED}[!] Installez SSH: pkg install openssh{Colors.END}")
        sys.exit(1)
    main()

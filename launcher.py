#!/usr/bin/env python3
"""
StemPlay Library - Launcher
Dois servidores (portas diferentes) + animacao ASCII DEDNEVES
"""
import os, sys, time, socket, subprocess, threading, functools
import http.server, socketserver

# UTF-8 + ANSI no Windows
if sys.platform == 'win32':
    os.system('')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORTA_LOCAL = 8000
PORTA_REDE = 8080
DIRETORIO = os.path.dirname(os.path.abspath(__file__))
HTML = "stemplay_library.html"
PDFS = "pdfs_found.txt"

# ---- ASCII art (estilo ANSI Shadow) ----
LETRAS = {
    'D': ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    'E': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    'N': ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    'V': ["██╗   ██╗", "██║   ██║", "██║   ██║", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚═══╝  "],
    'S': ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    ' ': ["   ", "   ", "   ", "   ", "   ", "   "],
}

def ascii_art(texto):
    linhas = [""] * 6
    for ch in texto.upper():
        for i in range(6):
            linhas[i] += LETRAS.get(ch, LETRAS[' '])[i]
    return linhas

def limpar():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner_animado():
    limpar()
    print()
    for linha in ascii_art("DEDNEVES"):
        print("    " + linha)
        time.sleep(0.09)
    print()
    print("    StemPlay Library  ·  Servidor Local")
    print("    " + "─" * 44)
    print()

def spinner(mensagem):
    frames = ['|', '/', '-', '\\']
    i = 0
    while True:
        sys.stdout.write(f'\r    [{frames[i % 4]}] {mensagem}')
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)

def rodar_script(script, mensagem):
    proc = subprocess.Popen(
        [sys.executable, script],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=DIRETORIO
    )
    sp = threading.Thread(target=spinner, args=(mensagem,), daemon=True)
    sp.start()
    stdout, stderr = proc.communicate()
    if proc.returncode == 0:
        sys.stdout.write(f'\r    [ OK ] {mensagem}              \n')
        return True
    else:
        sys.stdout.write(f'\r    [ERRO] {mensagem}              \n')
        print("\n    Detalhes:")
        print("    " + stderr.decode('utf-8', errors='replace').replace('\n', '\n    '))
        return False

def animacao_subida():
    alturas = ["      /\\      ", "     /  \\     ", "    /    \\    ", "   /______\\   ", "      ||      ", "     ||||     "]
    for i in range(6):
        sys.stdout.write('\r    ' + alturas[i])
        sys.stdout.flush()
        time.sleep(0.08)
    sys.stdout.write('\r' + ' ' * 30 + '\r')

# ---- Servidores HTTP (threads + diretorio explicito) ----
class ServidorHTTP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def criar_handler(diretorio):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=diretorio, **kwargs)
        def log_message(self, *args):
            pass  # suprime logs
    return Handler

def rodar_servidor(porta):
    handler = criar_handler(DIRETORIO)
    try:
        with ServidorHTTP(("0.0.0.0", porta), handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print(f"\n    [ERRO] Porta {porta}: {e}")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def mostrar_qr(url):
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(url)
        qr.print_ascii(invert=True)
    except ImportError:
        print("    [AVISO] Instale 'qrcode' para ver o QR:  pip install qrcode")
        print(f"    Ou acesse: {url}")

def main():
    os.chdir(DIRETORIO)
    banner_animado()

    if not os.path.exists(PDFS):
        print("    Primeira execucao: gerando lista de PDFs...")
        if not rodar_script("s3_god_mode.py", "Gerando lista de PDFs"):
            input("\n    Pressione Enter para sair...")
            sys.exit(1)
    else:
        print("    [ OK ] Lista de PDFs encontrada")

    if not os.path.exists(HTML):
        if not rodar_script("generate_library_premium.py", "Gerando biblioteca HTML"):
            input("\n    Pressione Enter para sair...")
            sys.exit(1)
    else:
        print("    [ OK ] Biblioteca HTML encontrada")

    print()
    animacao_subida()
    print("    Subindo servidores...")
    time.sleep(0.4)

    ip = get_ip()
    url_local = f"http://localhost:{PORTA_LOCAL}/{HTML}"
    url_rede = f"http://{ip}:{PORTA_REDE}/{HTML}"

    threading.Thread(target=rodar_servidor, args=(PORTA_LOCAL,), daemon=True).start()
    threading.Thread(target=rodar_servidor, args=(PORTA_REDE,), daemon=True).start()
    time.sleep(0.5)

    print()
    print("    Servidores no ar!")
    print("    " + "─" * 44)
    print(f"    Local  :  {url_local}")
    print(f"    Rede   :  {url_rede}")
    print(f"    Pasta  :  {DIRETORIO}")
    print("    " + "─" * 44)
    print()
    print("    Escaneie o QR Code com o celular:")
    print()
    mostrar_qr(url_rede)
    print()
    print("    Pressione Ctrl+C para encerrar.")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n    Encerrando servidores...")
        print("    Ate logo!\n")

if __name__ == "__main__":
    main()

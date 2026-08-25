#!/usr/bin/env python3
"""
StemPlay Library - Launcher
Dois servidores em portas livres + animacao ASCII + spinners controlados
"""
import os, sys, time, socket, subprocess, threading
import http.server, socketserver

# UTF-8 no Windows
if sys.platform == 'win32':
    os.system('')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORTA_LOCAL_PREFERIDA = 8000
PORTA_REDE_PREFERIDA = 8081  # 8080 geralmente e bloqueada no Windows
DIRETORIO = os.path.dirname(os.path.abspath(__file__))
HTML = "stemplay_library.html"
PDFS = "pdfs_found.txt"

# ---- ASCII art ----
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

def banner():
    limpar()
    print()
    for linha in ascii_art("DEDNEVES"):
        print("    " + linha)
    print()
    print("    StemPlay Library  ·  Servidor Local")
    print("    " + "─" * 44)
    print()

def encontrar_porta_livre(preferida):
    """Tenta a porta preferida; se ocupada, busca uma livre"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", preferida))
        s.close()
        return preferida
    except OSError:
        s.close()
        # Busca porta livre
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind(("0.0.0.0", 0))
        porta = s2.getsockname()[1]
        s2.close()
        return porta

def spinner(mensagem, parar_event):
    """Spinner que pode ser interrompido"""
    frames = ['|', '/', '-', '\\']
    i = 0
    while not parar_event.is_set():
        sys.stdout.write(f'\r    [{frames[i % 4]}] {mensagem}')
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(mensagem) + 10) + '\r')
    sys.stdout.flush()

def rodar_script(script, mensagem):
    proc = subprocess.Popen(
        [sys.executable, script],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=DIRETORIO
    )
    parar = threading.Event()
    sp = threading.Thread(target=spinner, args=(mensagem, parar), daemon=True)
    sp.start()
    stdout, stderr = proc.communicate()
    parar.set()  # sinaliza pro spinner parar
    sp.join(timeout=1)  # espera o spinner terminar
    if proc.returncode == 0:
        print(f'\r    [ OK ] {mensagem}              ')
        return True
    else:
        print(f'\r    [ERRO] {mensagem}              ')
        print("\n    Detalhes:")
        print("    " + stderr.decode('utf-8', errors='replace').replace('\n', '\n    '))
        return False

def animacao_subida():
    alturas = [
        "      /\\      ",
        "     /  \\     ",
        "    /    \\    ",
        "   /______\\   ",
        "      ||      ",
        "     ||||     "
    ]
    for frame in alturas:
        sys.stdout.write('\r    ' + frame)
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * 30 + '\r')
    sys.stdout.flush()

# ---- Servidor HTTP ----
class ServidorHTTP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def criar_handler(diretorio):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=diretorio, **kwargs)
        def log_message(self, *args):
            pass
    return Handler

def rodar_servidor(porta, event_parar):
    handler = criar_handler(DIRETORIO)
    try:
        with ServidorHTTP(("0.0.0.0", porta), handler) as httpd:
            while not event_parar.is_set():
                httpd.handle_request()
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
    banner()

    # Gera PDFs se necessario
    if not os.path.exists(PDFS):
        print("    Primeira execucao: gerando lista de PDFs...")
        if not rodar_script("s3_god_mode.py", "Gerando lista de PDFs"):
            input("\n    Pressione Enter para sair...")
            sys.exit(1)
    else:
        print("    [ OK ] Lista de PDFs encontrada")

    # Gera HTML se necessario
    if not os.path.exists(HTML):
        if not rodar_script("generate_library_premium.py", "Gerando biblioteca HTML"):
            input("\n    Pressione Enter para sair...")
            sys.exit(1)
    else:
        print("    [ OK ] Biblioteca HTML encontrada")

    print()
    animacao_subida()
    print("    Subindo servidores...")
    time.sleep(0.5)

    # Encontra portas livres
    porta_local = encontrar_porta_livre(PORTA_LOCAL_PREFERIDA)
    porta_rede = encontrar_porta_livre(PORTA_REDE_PREFERIDA)

    ip = get_ip()
    url_local = f"http://localhost:{porta_local}/{HTML}"
    url_rede = f"http://{ip}:{porta_rede}/{HTML}"

    # Event para parar servidores graciosamente
    parar_event = threading.Event()

    # Inicia servidores em threads
    t_local = threading.Thread(target=rodar_servidor, args=(porta_local, parar_event), daemon=True)
    t_rede = threading.Thread(target=rodar_servidor, args=(porta_rede, parar_event), daemon=True)
    t_local.start()
    t_rede.start()
    time.sleep(0.5)

    # Limpa tela antes do QR
    limpar()
    banner()

    print("    Servidores no ar!")
    print("    " + "─" * 44)
    print(f"    Local  :  {url_local}")
    print(f"    Rede   :  {url_rede}")
    print(f"    Pasta  :  {DIRETORIO}")
    if porta_local != PORTA_LOCAL_PREFERIDA:
        print(f"    [INFO] Porta local ajustada: {porta_local}")
    if porta_rede != PORTA_REDE_PREFERIDA:
        print(f"    [INFO] Porta rede ajustada: {porta_rede}")
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
        parar_event.set()
        time.sleep(0.3)
        print("    Ate logo!\n")

if __name__ == "__main__":
    main()

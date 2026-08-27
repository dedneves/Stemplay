#!/usr/bin/env python3
"""
AQUI E O DED, SOMENTE O LAUNCHER SAI DAQUI VLEHO 
"""
import os, sys, time, socket, subprocess, threading, json
from datetime import datetime, timedelta
import http.server, socketserver
from urllib.request import urlopen, Request
from urllib.error import URLError

if sys.platform == 'win32':
    os.system('')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORTA_LOCAL_PREF = 8000
PORTA_REDE_PREF = 8081
DIRETORIO = os.path.dirname(os.path.abspath(__file__))
HTML = "stemplay_library.html"
PDFS = "pdfs_found.txt"
REPO_API = "https://api.github.com/repos/dedneves/Stemplay/commits?per_page=1"
SHA_FILE = os.path.join(DIRETORIO, ".last_commit")
TEMPO_ATIVO = 60
LARGURA = 60  # largura fixa pra padding

CORES = ["\033[91m", "\033[92m", "\033[93m", "\033[94m",
         "\033[95m", "\033[96m", "\033[97m"]
VERDE = "\033[92m"
CIANO = "\033[96m"
AMARELO = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

LETRAS = {
    'D': ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    'E': ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    'N': ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    'V': ["██╗   ██╗", "██║   ██║", "██║   ██║", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚═══╝  "],
    'S': ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    ' ': ["   ", "   ", "   ", "   ", "   ", "   "],
}

class RastreadorVisitantes:
    def __init__(self):
        self.visitantes = {}
        self.lock = threading.Lock()
        self.total_visitas = 0

    def registrar(self, ip, pagina):
        if pagina in ('/favicon.ico', '/robots.txt'):
            return
        with self.lock:
            agora = datetime.now()
            if ip not in self.visitantes:
                self.total_visitas += 1
            self.visitantes[ip] = {
                'ultimo': agora,
                'requests': self.visitantes.get(ip, {}).get('requests', 0) + 1,
                'pagina': pagina,
                'primeiro': self.visitantes.get(ip, {}).get('primeiro', agora)
            }

    def ativos(self):
        with self.lock:
            agora = datetime.now()
            limite = timedelta(seconds=TEMPO_ATIVO)
            return {
                ip: dados for ip, dados in self.visitantes.items()
                if agora - dados['ultimo'] < limite
            }

rastreador = RastreadorVisitantes()

def ascii_art(texto):
    linhas = [""] * 6
    for ch in texto.upper():
        for i in range(6):
            linhas[i] += LETRAS.get(ch, LETRAS[' '])[i]
    return linhas

def limpar():
    os.system('cls' if os.name == 'nt' else 'clear')

def pad(linha, largura=LARGURA):
    """Adiciona espacos ate completar a largura (pra sobrescrever texto antigo)"""
    # Remove codigos ANSI pra contar tamanho real
    import re
    texto_limpo = re.sub(r'\033\[[0-9;]*m', '', linha)
    faltam = max(0, largura - len(texto_limpo))
    return linha + ' ' * faltam

def banner_piscante():
    import random
    art = ascii_art("DEDNEVES")
    duracao = 2.0
    intervalo = 0.08
    frames = int(duracao / intervalo)

    limpar()
    print()
    for i in range(frames):
        cor = random.choice(CORES)
        print("\033[6A", end="")
        for linha in art:
            print("    " + cor + BOLD + linha + RESET)
        sys.stdout.flush()
        time.sleep(intervalo)

    print("\033[6A", end="")
    for linha in art:
        print("    " + VERDE + BOLD + linha + RESET)

    print()
    print("    StemPlay Library  ·  Servidor Local")
    print("    " + "─" * 44)
    print()

def banner_estatico():
    print()
    art = ascii_art("DEDNEVES")
    for linha in art:
        print("    " + VERDE + BOLD + linha + RESET)
    print()
    print("    StemPlay Library  ·  Servidor Local")
    print("    " + "─" * 44)
    print()

def checar_updates():
    print("    [CHECK] Verificando atualizacoes do repositorio...")

    sha_local = None
    if os.path.exists(SHA_FILE):
        try:
            with open(SHA_FILE, "r") as f:
                sha_local = f.read().strip()
        except Exception:
            pass

    try:
        req = Request(REPO_API, headers={"User-Agent": "StemPlay-Launcher"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if not data:
                print("    [INFO] Repositorio vazio ou sem commits")
                return
            sha_remoto = data[0]["sha"]
            mensagem = data[0]["commit"]["message"].split("\n")[0][:60]
            data_commit = data[0]["commit"]["author"]["date"][:10]
    except (URLError, json.JSONDecodeError, KeyError, OSError):
        print("    [INFO] Sem internet ou repo indisponivel - modo offline")
        return

    try:
        with open(SHA_FILE, "w") as f:
            f.write(sha_remoto)
    except Exception:
        pass

    if sha_local is None:
        print(f"    [INFO] Primeira checagem. Commit: {sha_remoto[:8]} ({data_commit})")
        print(f"    [INFO] \"{mensagem}\"")
    elif sha_local != sha_remoto:
        print(f"    [UPDATE] Nova versao disponivel!")
        print(f"    [UPDATE] Commit: {sha_remoto[:8]} ({data_commit})")
        print(f"    [UPDATE] \"{mensagem}\"")
        print()
        print("    Deseja baixar a nova versao? (s/N): ", end="", flush=True)
        try:
            resp = input().strip().lower()
        except EOFError:
            resp = 'n'

        if resp in ('s', 'sim', 'y', 'yes'):
            baixar_atualizacao()
    else:
        print(f"    [ OK ] Versao atualizada (commit {sha_remoto[:8]})")

def baixar_atualizacao():
    print()
    print("    [DL] Baixando arquivos atualizados...")
    arquivos = [
        ("launcher.py", "https://raw.githubusercontent.com/dedneves/Stemplay/main/launcher.py"),
        ("s3_god_mode.py", "https://raw.githubusercontent.com/dedneves/Stemplay/main/s3_god_mode.py"),
        ("generate_library_premium.py", "https://raw.githubusercontent.com/dedneves/Stemplay/main/generate_library_premium.py"),
        ("start.bat", "https://raw.githubusercontent.com/dedneves/Stemplay/main/start.bat"),
        ("README.md", "https://raw.githubusercontent.com/dedneves/Stemplay/main/README.md"),
    ]

    for nome, url in arquivos:
        try:
            req = Request(url, headers={"User-Agent": "StemPlay-Launcher"})
            with urlopen(req, timeout=10) as resp:
                conteudo = resp.read()
            caminho = os.path.join(DIRETORIO, nome)
            with open(caminho, "wb") as f:
                f.write(conteudo)
            print(f"    [ OK ] {nome}")
        except Exception as e:
            print(f"    [ERRO] {nome}: {e}")

    print()
    print("    [INFO] Atualizacao concluida. Reinicie o launcher.")
    input("    Pressione Enter para sair...")
    sys.exit(0)

def spinner(mensagem, parar_event):
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
    parar.set()
    sp.join(timeout=1)
    if proc.returncode == 0:
        print(f'\r    [ OK ] {mensagem}              ')
        return True
    else:
        print(f'\r    [ERRO] {mensagem}              ')
        print("\n    Detalhes:")
        print("    " + stderr.decode('utf-8', errors='replace').replace('\n', '\n    '))
        return False

def encontrar_porta_livre(preferida):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", preferida))
        s.close()
        return preferida
    except OSError:
        s.close()
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind(("0.0.0.0", 0))
        porta = s2.getsockname()[1]
        s2.close()
        return porta

def criar_handler(diretorio):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=diretorio, **kwargs)

        def log_message(self, *args):
            pass

        def do_GET(self):
            ip = self.client_address[0]
            pagina = self.path.split('?')[0]
            rastreador.registrar(ip, pagina)
            super().do_GET()
    return Handler

class ServidorHTTP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

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
        print("    [AVISO] Instale 'qrcode':  pip install qrcode")
        print(f"    Ou acesse: {url}")

def gerar_linhas_visitantes():
    """Gera lista de strings com padding fixo"""
    ativos = rastreador.ativos()
    linhas = []
    linhas.append(pad("    " + "─" * 44))
    linhas.append(pad(f"    {CIANO}{BOLD}Visitantes conectados: {len(ativos)}{RESET}"))
    linhas.append(pad("    " + "─" * 44))

    if not ativos:
        linhas.append(pad(f"    {DIM}(ninguem conectado no momento){RESET}"))
    else:
        for ip, dados in sorted(ativos.items(), key=lambda x: x[1]['ultimo'], reverse=True):
            tempo_atras = int((datetime.now() - dados['ultimo']).total_seconds())
            status = "agora" if tempo_atras < 5 else f"{tempo_atras}s atras"
            origem = "LOCAL" if ip.startswith("127.") or ip == "localhost" else "REDE "
            linhas.append(pad(f"    {VERDE}*{RESET} {ip:<15} {AMARELO}[{origem}]{RESET} {DIM}{status:<10}{RESET} {DIM}{dados['pagina'][:20]}{RESET}"))

    linhas.append(pad(""))
    linhas.append(pad(f"    {DIM}Total de visitas: {rastreador.total_visitas}{RESET}"))
    linhas.append(pad(""))
    linhas.append(pad("    Pressione Ctrl+C para encerrar."))
    linhas.append(pad(""))
    return linhas

# Tamanho MAXIMO de linhas que ja imprimimos (pra saber quantas subir)
MAX_LINHAS_VISITANTES = 20

def loop_visitantes(event_parar):
    """Atualiza visitantes subindo N linhas fixas e reescrevendo com padding"""
    while not event_parar.is_set():
        time.sleep(3)
        if event_parar.is_set():
            break

        # Sobe MAX_LINHAS_VISITANTES linhas
        sys.stdout.write(f"\033[{MAX_LINHAS_VISITANTES}A")
        sys.stdout.flush()

        # Reescreve todas as linhas com padding (sobrescreve texto antigo)
        linhas = gerar_linhas_visitantes()
        for linha in linhas:
            print(linha)

        # Se gerou menos linhas que o maximo, preenche com linhas vazias
        for _ in range(MAX_LINHAS_VISITANTES - len(linhas)):
            print(' ' * LARGURA)

        # Volta o cursor pra posicao correta (sobe o excesso de linhas preenchidas)
        excesso = MAX_LINHAS_VISITANTES - len(linhas)
        if excesso > 0:
            sys.stdout.write(f"\033[{excesso}A")
        sys.stdout.flush()

def main():
    os.chdir(DIRETORIO)
    limpar()

    checar_updates()
    banner_piscante()

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
    print("    Subindo servidores...")
    time.sleep(0.5)

    porta_local = encontrar_porta_livre(PORTA_LOCAL_PREF)
    porta_rede = encontrar_porta_livre(PORTA_REDE_PREF)

    ip = get_ip()
    url_local = f"http://localhost:{porta_local}/{HTML}"
    url_rede = f"http://{ip}:{porta_rede}/{HTML}"

    parar_event = threading.Event()
    t_local = threading.Thread(target=rodar_servidor, args=(porta_local, parar_event), daemon=True)
    t_rede = threading.Thread(target=rodar_servidor, args=(porta_rede, parar_event), daemon=True)
    t_local.start()
    t_rede.start()
    time.sleep(0.5)

    limpar()
    banner_estatico()
    print("    Servidores no ar!")
    print("    " + "─" * 44)
    print(f"    Local  :  {url_local}")
    print(f"    Rede   :  {url_rede}")
    print(f"    Pasta  :  {DIRETORIO}")
    if porta_local != PORTA_LOCAL_PREF:
        print(f"    [INFO] Porta local ajustada: {porta_local}")
    if porta_rede != PORTA_REDE_PREF:
        print(f"    [INFO] Porta rede ajustada: {porta_rede}")
    print("    " + "─" * 44)
    print()
    print("    Escaneie o QR Code com o celular:")
    print()
    mostrar_qr(url_rede)
    print()

    # Imprime bloco inicial com padding
    linhas_iniciais = gerar_linhas_visitantes()
    for linha in linhas_iniciais:
        print(linha)
    # Preenche ate MAX_LINHAS_VISITANTES
    for _ in range(MAX_LINHAS_VISITANTES - len(linhas_iniciais)):
        print(' ' * LARGURA)
    # Volta cursor pro final do bloco
    excesso = MAX_LINHAS_VISITANTES - len(linhas_iniciais)
    if excesso > 0:
        sys.stdout.write(f"\033[{excesso}A")
    sys.stdout.flush()

    # Inicia thread de atualizacao
    t_visitantes = threading.Thread(target=loop_visitantes, args=(parar_event,), daemon=True)
    t_visitantes.start()

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

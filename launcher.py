#!/usr/bin/env python3
"""
TA LENDO, EU SEI 

QUEM SE MEXER E GAY
"""
import os, sys, time, socket, subprocess, threading, json, re
from datetime import datetime, timedelta
import http.server, socketserver
from urllib.request import urlopen, Request
from urllib.error import URLError

# Forca UTF-8 no Windows
if sys.platform == 'win32':
    os.system('')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Silencia warnings do urllib
import logging
logging.getLogger('urllib3').setLevel(logging.ERROR)

PORTA_LOCAL_PREF = 8000
PORTA_REDE_PREF = 8081
DIRETORIO = os.path.dirname(os.path.abspath(__file__))
HTML = "stemplay_library.html"
PDFS = "pdfs_found.txt"
REPO_API = "https://api.github.com/repos/dedneves/Stemplay/commits?per_page=1"
SHA_FILE = os.path.join(DIRETORIO, ".last_commit")
TEMPO_ATIVO = 60

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


def tamanho_visivel(texto):
    """Conta caracteres visiveis ignorando codigos ANSI"""
    return len(re.sub(r'\033\[[0-9;]*m', '', texto))


def banner_piscante():
    import random
    art = ascii_art("DEDNEVES")
    duracao = 2.0
    intervalo = 0.08
    frames = int(duracao / intervalo)

    limpar()
    sys.stdout.write("\n")
    for i in range(frames):
        cor = random.choice(CORES)
        sys.stdout.write("\033[6A")
        for linha in art:
            sys.stdout.write("    " + cor + BOLD + linha + RESET + "\n")
        sys.stdout.flush()
        time.sleep(intervalo)

    sys.stdout.write("\033[6A")
    for linha in art:
        sys.stdout.write("    " + VERDE + BOLD + linha + RESET + "\n")

    sys.stdout.write("\n")
    sys.stdout.write("    StemPlay Library  ·  Servidor Local\n")
    sys.stdout.write("    " + "─" * 44 + "\n")
    sys.stdout.write("\n")
    sys.stdout.flush()


def banner_estatico():
    art = ascii_art("DEDNEVES")
    for linha in art:
        sys.stdout.write("    " + VERDE + BOLD + linha + RESET + "\n")
    sys.stdout.write("\n")
    sys.stdout.write("    StemPlay Library  ·  Servidor Local\n")
    sys.stdout.write("    " + "─" * 44 + "\n")
    sys.stdout.write("\n")
    sys.stdout.flush()


def checar_updates():
    sys.stdout.write("    [CHECK] Verificando atualizacoes do repositorio...\n")
    sys.stdout.flush()

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
                sys.stdout.write("    [INFO] Repositorio vazio ou sem commits\n")
                sys.stdout.flush()
                return
            sha_remoto = data[0]["sha"]
            mensagem = data[0]["commit"]["message"].split("\n")[0][:60]
            data_commit = data[0]["commit"]["author"]["date"][:10]
    except (URLError, json.JSONDecodeError, KeyError, OSError):
        sys.stdout.write("    [INFO] Sem internet ou repo indisponivel - modo offline\n")
        sys.stdout.flush()
        return

    try:
        with open(SHA_FILE, "w") as f:
            f.write(sha_remoto)
    except Exception:
        pass

    if sha_local is None:
        sys.stdout.write(f"    [INFO] Primeira checagem. Commit: {sha_remoto[:8]} ({data_commit})\n")
        sys.stdout.write(f"    [INFO] \"{mensagem}\"\n")
    elif sha_local != sha_remoto:
        sys.stdout.write(f"    [UPDATE] Nova versao disponivel!\n")
        sys.stdout.write(f"    [UPDATE] Commit: {sha_remoto[:8]} ({data_commit})\n")
        sys.stdout.write(f"    [UPDATE] \"{mensagem}\"\n")
        sys.stdout.write("\n")
        sys.stdout.write("    Deseja baixar a nova versao? (s/N): ", )
        sys.stdout.flush()
        try:
            resp = input().strip().lower()
        except EOFError:
            resp = 'n'

        if resp in ('s', 'sim', 'y', 'yes'):
            baixar_atualizacao()
    else:
        sys.stdout.write(f"    [ OK ] Versao atualizada (commit {sha_remoto[:8]})\n")
    sys.stdout.flush()


def baixar_atualizacao():
    sys.stdout.write("\n")
    sys.stdout.write("    [DL] Baixando arquivos atualizados...\n")
    sys.stdout.flush()
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
            sys.stdout.write(f"    [ OK ] {nome}\n")
        except Exception as e:
            sys.stdout.write(f"    [ERRO] {nome}: {e}\n")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.write("    [INFO] Atualizacao concluida. Reinicie o launcher.\n")
    sys.stdout.flush()
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
    # Suprime completamente stdout/stderr do subprocesso
    proc = subprocess.Popen(
        [sys.executable, script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=DIRETORIO
    )
    parar = threading.Event()
    sp = threading.Thread(target=spinner, args=(mensagem, parar), daemon=True)
    sp.start()
    proc.communicate()
    parar.set()
    sp.join(timeout=1)
    if proc.returncode == 0:
        sys.stdout.write(f'\r    [ OK ] {mensagem}              \n')
        sys.stdout.flush()
        return True
    else:
        sys.stdout.write(f'\r    [ERRO] {mensagem}              \n')
        sys.stdout.flush()
        # Tenta rodar de novo mostrando erro
        sys.stdout.write("    Rodando novamente para capturar erro...\n")
        sys.stdout.flush()
        proc2 = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, cwd=DIRETORIO
        )
        if proc2.stderr:
            sys.stdout.write("\n    Detalhes:\n")
            for linha in proc2.stderr.split('\n')[:10]:
                sys.stdout.write("    " + linha + "\n")
        sys.stdout.flush()
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
            pass  # Silencia logs HTTP

        def do_GET(self):
            ip = self.client_address[0]
            pagina = self.path.split('?')[0]
            rastreador.registrar(ip, pagina)
            super().do_GET()

        def log_error(self, *args):
            pass  # Silencia erros HTTP tambem
    return Handler


class ServidorHTTP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def rodar_servidor(porta, event_parar):
    handler = criar_handler(DIRETORIO)
    try:
        with ServidorHTTP(("0.0.0.0", porta), handler) as httpd:
            httpd.timeout = 1
            while not event_parar.is_set():
                httpd.handle_request()
    except OSError:
        pass


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
        sys.stdout.write("    [AVISO] Instale 'qrcode':  pip install qrcode\n")
        sys.stdout.write(f"    Ou acesse: {url}\n")
    sys.stdout.flush()


def gerar_linhas_visitantes():
    """Gera lista de strings da secao de visitantes"""
    ativos = rastreador.ativos()
    linhas = []
    linhas.append("    " + "─" * 44)
    linhas.append(f"    {CIANO}{BOLD}Visitantes conectados: {len(ativos)}{RESET}")
    linhas.append("    " + "─" * 44)

    if not ativos:
        linhas.append(f"    {DIM}(ninguem conectado no momento){RESET}")
    else:
        for ip, dados in sorted(ativos.items(), key=lambda x: x[1]['ultimo'], reverse=True):
            tempo_atras = int((datetime.now() - dados['ultimo']).total_seconds())
            status = "agora" if tempo_atras < 5 else f"{tempo_atras}s atras"
            origem = "LOCAL" if ip.startswith("127.") or ip == "localhost" else "REDE "
            linhas.append(f"    {VERDE}*{RESET} {ip:<15} {AMARELO}[{origem}]{RESET} {DIM}{status:<10}{RESET} {DIM}{dados['pagina'][:20]}{RESET}")

    linhas.append("")
    linhas.append(f"    {DIM}Total de visitas: {rastreador.total_visitas}{RESET}")
    linhas.append("")
    linhas.append("    Pressione Ctrl+C para encerrar.")
    return linhas


def loop_visitantes(event_parar):
    """
    Thread responsavel por TODA a exibicao de visitantes.
    Faz a primeira impressao E todas as atualizacoes.
    Nao usa print() - usa sys.stdout.write com controle total.
    """
    linhas_anteriores = 0
    max_len = 0
    primeira_vez = True

    while not event_parar.is_set():
        # Espera 3s antes da proxima atualizacao
        for _ in range(30):
            if event_parar.is_set():
                return
            time.sleep(0.1)

        if event_parar.is_set():
            return

        # Gera novas linhas
        novas_linhas = gerar_linhas_visitantes()

        # Se nao e a primeira vez, sobe o cursor
        if not primeira_vez and linhas_anteriores > 0:
            sys.stdout.write(f"\033[{linhas_anteriores}A")

        # Imprime cada linha com padding
        for linha in novas_linhas:
            tam = tamanho_visivel(linha)
            faltam = max(0, max_len - tam)
            sys.stdout.write(linha + ' ' * faltam + "\n")

        # Se tem menos linhas que antes, apaga as extras
        if len(novas_linhas) < linhas_anteriores:
            diferenca = linhas_anteriores - len(novas_linhas)
            for _ in range(diferenca):
                sys.stdout.write(' ' * max_len + "\n")
            # Volta cursor pras linhas extras
            sys.stdout.write(f"\033[{diferenca}A")

        sys.stdout.flush()

        # Atualiza contadores
        linhas_anteriores = len(novas_linhas)
        max_len = max(tamanho_visivel(l) for l in novas_linhas) if novas_linhas else 0
        primeira_vez = False


def main():
    os.chdir(DIRETORIO)
    limpar()

    # Verifica updates
    checar_updates()

    # Banner piscante
    banner_piscante()

    # Gera PDFs se necessario
    if not os.path.exists(PDFS):
        sys.stdout.write("    Primeira execucao: gerando lista de PDFs...\n")
        sys.stdout.flush()
        if not rodar_script("s3_god_mode.py", "Gerando lista de PDFs"):
            input("\n    Pressione Enter para sair...")
            sys.exit(1)
    else:
        sys.stdout.write("    [ OK ] Lista de PDFs encontrada\n")
        sys.stdout.flush()

    # Gera HTML se necessario
    if not os.path.exists(HTML):
        if not rodar_script("generate_library_premium.py", "Gerando biblioteca HTML"):
            input("\n    Pressione Enter para sair...")
            sys.exit(1)
    else:
        sys.stdout.write("    [ OK ] Biblioteca HTML encontrada\n")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.write("    Subindo servidores...\n")
    sys.stdout.flush()
    time.sleep(0.5)

    # Encontra portas
    porta_local = encontrar_porta_livre(PORTA_LOCAL_PREF)
    porta_rede = encontrar_porta_livre(PORTA_REDE_PREF)

    ip = get_ip()
    url_local = f"http://localhost:{porta_local}/{HTML}"
    url_rede = f"http://{ip}:{porta_rede}/{HTML}"

    # Inicia servidores
    parar_event = threading.Event()
    t_local = threading.Thread(target=rodar_servidor, args=(porta_local, parar_event), daemon=True)
    t_rede = threading.Thread(target=rodar_servidor, args=(porta_rede, parar_event), daemon=True)
    t_local.start()
    t_rede.start()
    time.sleep(0.5)

    # Limpa e redesenha tudo
    limpar()
    banner_estatico()
    sys.stdout.write("    Servidores no ar!\n")
    sys.stdout.write("    " + "─" * 44 + "\n")
    sys.stdout.write(f"    Local  :  {url_local}\n")
    sys.stdout.write(f"    Rede   :  {url_rede}\n")
    sys.stdout.write(f"    Pasta  :  {DIRETORIO}\n")
    if porta_local != PORTA_LOCAL_PREF:
        sys.stdout.write(f"    [INFO] Porta local ajustada: {porta_local}\n")
    if porta_rede != PORTA_REDE_PREF:
        sys.stdout.write(f"    [INFO] Porta rede ajustada: {porta_rede}\n")
    sys.stdout.write("    " + "─" * 44 + "\n")
    sys.stdout.write("\n")
    sys.stdout.write("    Escaneie o QR Code com o celular:\n")
    sys.stdout.write("\n")
    sys.stdout.flush()
    mostrar_qr(url_rede)
    sys.stdout.write("\n")
    sys.stdout.flush()

    # Inicia thread de visitantes (ela faz a primeira impressao tambem)
    t_visitantes = threading.Thread(target=loop_visitantes, args=(parar_event,), daemon=True)
    t_visitantes.start()

    # Loop principal so fica vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.stdout.write("\n\n    Encerrando servidores...\n")
        sys.stdout.flush()
        parar_event.set()
        time.sleep(0.3)
        sys.stdout.write("    Ate logo!\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

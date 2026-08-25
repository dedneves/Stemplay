#!/usr/bin/env python3
"""
Launcher - inicia DOIS servidores (portas diferentes) e mostra QR Code
Porta 8000: acesso local (localhost)
Porta 8080: acesso pela rede (QR Code aponta aqui)
"""
import socket, subprocess, sys, time, os

PORTA_LOCAL = 8000
PORTA_REDE = 8080

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def print_qr(data):
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(data)
        qr.print_ascii(invert=True)
    except ImportError:
        print("  ⚠️  Instale 'qrcode' para ver o QR: pip install qrcode")
        print(f"  📱 Ou acesse manualmente: {data}")

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Verifica se o HTML existe
    if not os.path.exists("stemplay_library.html"):
        print("❌ stemplay_library.html não encontrado!")
        print("   Rode: python generate_library_premium.py")
        sys.exit(1)

    ip = get_ip()
    url_local = f"http://localhost:{PORTA_LOCAL}/stemplay_library.html"
    url_rede = f"http://{ip}:{PORTA_REDE}/stemplay_library.html"

    print()
    print("  ╔════════════════════════════════════════════╗")
    print("  ║        🚀 SERVIDORES INICIADOS!           ║")
    print("  ╠════════════════════════════════════════════╣")
    print(f"  ║  💻 Local: {url_local:<35}║")
    print(f"  ║  📱 Rede:  {url_rede:<35}║")
    print("  ╚════════════════════════════════════════════╝")
    print()
    print("  📱 Escaneie o QR Code com o celular:")
    print("  ─────────────────────────────────────────")
    print_qr(url_rede)
    print("  ─────────────────────────────────────────")
    print()

    # Inicia os DOIS servidores
    procs = []
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORTA_LOCAL)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ))
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORTA_REDE), "--bind", "0.0.0.0"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    ))

    print("  ✅ Servidores rodando!")
    print("  💡 Local  → porta", PORTA_LOCAL)
    print("  💡 Rede   → porta", PORTA_REDE, "(QR Code)")
    print()
    print("  Pressione Ctrl+C para encerrar.")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  🛑 Encerrando servidores...")
        for p in procs:
            p.terminate()
        print("  👋 Até logo!")

if __name__ == "__main__":
    main()

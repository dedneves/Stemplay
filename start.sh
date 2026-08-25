#!/bin/bash
cd "$(dirname "$0")"

echo ""
echo "  =============================================="
echo "     StemPlay Library - Inicialização"
echo "  =============================================="
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "  [ERRO] Python3 não encontrado!"
    echo "  Instale: sudo apt install python3 python3-pip"
    exit 1
fi
echo "  [OK] Python detectado"

# Instala dependências
echo "  [1/3] Instalando dependências..."
pip3 install --break-system-packages aiohttp tqdm qrcode 2>/dev/null || \
pip3 install aiohttp tqdm qrcode 2>/dev/null
echo "  [OK] Dependências prontas"

# Gera lista de PDFs se não existir
if [ ! -f pdfs_found.txt ]; then
    echo "  [2/3] Gerando lista de PDFs do S3..."
    python3 s3_god_mode.py
else
    echo "  [2/3] Lista de PDFs já existe"
fi

# Gera HTML se não existir
if [ ! -f stemplay_library.html ]; then
    echo "  [3/3] Gerando biblioteca HTML..."
    python3 generate_library_premium.py
else
    echo "  [3/3] Biblioteca HTML já existe"
fi

echo ""
echo "  =============================================="
echo "     Tudo pronto! Iniciando servidores..."
echo "  =============================================="
echo ""

# Chama o launcher (2 servidores + QR Code)
python3 launcher.py

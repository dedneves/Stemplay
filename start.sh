#!/bin/bash
cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo ""
    echo "  [ERRO] Python3 nao encontrado!"
    echo "  Instale:  sudo apt install python3 python3-pip"
    echo ""
    exit 1
fi

pip3 install --break-system-packages aiohttp tqdm qrcode 2>/dev/null || \
pip3 install aiohttp tqdm qrcode 2>/dev/null

python3 launcher.py

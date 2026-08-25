# Stemplay

Como usar tudo (TL;DR)
Instala dependências:
bash
1
2
pip3 install --break-system-packages aiohttp tqdm
sudo apt install megatools  # Só se quiser MEGA
Pipeline completo:
bash
1
2
3
4
5
6
7
8
9
10
11
12
# 1. Descobre PDFs
python3 s3_god_mode.py

# 2. Gera biblioteca web
python3 generate_library_premium.py

# 3. Inicia servidor
python3 -m http.server 8000 --bind 0.0.0.0

# 4. Acessa
# Local: http://localhost:8000/stemplay_library.html
# Rede:  http://SEU_IP:8000/stemplay_library.html
Descobre seu IP:
bash
1
2
3
4
# Linux
hostname -I
# Windows (PowerShell)
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object

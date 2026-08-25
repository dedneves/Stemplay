@echo off
chcp 65001 >nul 2>&1
title StemPlay Library - Server
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       📚 StemPlay Library Setup         ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python nao encontrado!
    echo  📥 Baixe em: https://www.python.org/downloads/
    echo  ⚠️  Marque "Add Python to PATH" na instalacao
    pause
    exit /b 1
)
echo  ✅ Python detectado

:: Instala dependencias
echo  📦 Verificando dependencias...
pip install aiohttp tqdm qrcode[pil] >nul 2>&1
echo  ✅ Dependencias instaladas

:: Gera lista de PDFs se nao existir
if not exist "pdfs_found.txt" (
    echo  🔍 Gerando lista de PDFs do S3...
    echo  ⏳ Isso pode levar alguns minutos...
    python s3_god_mode.py
    if errorlevel 1 (
        echo  ❌ Erro ao gerar lista de PDFs
        pause
        exit /b 1
    )
)
echo  ✅ Lista de PDFs pronta

:: Gera HTML se nao existir ou se pdfs_found.txt for mais novo
if not exist "stemplay_library.html" (
    echo  🎨 Gerando biblioteca HTML...
    python generate_library_premium.py
    if errorlevel 1 (
        echo  ❌ Erro ao gerar biblioteca
        pause
        exit /b 1
    )
)
echo  ✅ Biblioteca HTML pronta

:: Pega IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "IP=%%a"
    goto :gotip
)
:gotip
set "IP=%IP: =%"
set "PORT=8000"
set "URL=http://%IP%:%PORT%/stemplay_library.html"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║         🚀 SERVIDOR INICIADO!           ║
echo  ╠══════════════════════════════════════════╣
echo  ║                                          ║
echo  ║  💻 Local:                               ║
echo  ║  http://localhost:%PORT%/stemplay_library.html║
echo  ║                                          ║
echo  ║  📱 Rede (celular/outros PCs):           ║
echo  ║  %URL%
echo  ║                                          ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Gera QR Code no terminal
echo  📱 QR Code para acessar pelo celular:
echo.
python -c "import qrcode;qr=qrcode.QRCode(box_size=1,border=1);qr.add_data('%URL%');qr.print_ascii(invert=True)" 2>nul
if errorlevel 1 (
    echo  ⚠️  QR Code nao disponivel. Acesse manualmente:
    echo  %URL%
)
echo.
echo  ⏹️  Pressione Ctrl+C para parar o servidor
echo  ──────────────────────────────────────────
echo.

python -m http.server %PORT% --bind 0.0.0.0

pause

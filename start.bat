@echo off
chcp 65001 >nul
title StemPlay Library
cd /d "%~dp0"

echo.
echo   ==============================================
echo      StemPlay Library - Inicializacao
echo   ==============================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERRO] Python nao encontrado!
    echo   Baixe em: https://www.python.org/downloads/
    echo   IMPORTANTE: marque "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo   [OK] Python detectado
python --version

:: Instala dependencias com python -m pip (GARANTE o Python certo)
echo.
echo   [1/3] Instalando dependencias...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install aiohttp tqdm qrcode
if errorlevel 1 (
    echo.
    echo   [ERRO] Falha ao instalar dependencias!
    echo   Tente manualmente: python -m pip install aiohttp tqdm qrcode
    pause
    exit /b 1
)

:: Verifica se instalou de verdade
python -c "import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERRO] aiohttp nao instalou corretamente!
    echo   Tente: python -m pip install aiohttp
    pause
    exit /b 1
)
echo   [OK] Dependencias prontas

:: Gera lista de PDFs se nao existir
if not exist pdfs_found.txt (
    echo   [2/3] Gerando lista de PDFs do S3...
    echo   Isso pode levar alguns minutos...
    python s3_god_mode.py
    if errorlevel 1 (
        echo   [ERRO] Falha ao gerar lista de PDFs
        pause
        exit /b 1
    )
) else (
    echo   [2/3] Lista de PDFs ja existe
)

:: Gera HTML se nao existir
if not exist stemplay_library.html (
    echo   [3/3] Gerando biblioteca HTML...
    python generate_library_premium.py
    if errorlevel 1 (
        echo   [ERRO] Falha ao gerar biblioteca
        pause
        exit /b 1
    )
) else (
    echo   [3/3] Biblioteca HTML ja existe
)

echo.
echo   ==============================================
echo      Tudo pronto! Iniciando servidores...
echo   ==============================================
echo.

python launcher.py

pause

@echo off
chcp 65001 >nul
title StemPlay Library
cd /d "%~dp0"

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERRO] Python nao encontrado!
    echo   Baixe em: https://www.python.org/downloads/
    echo   Marque "Add Python to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)

:: Instala dependencias
python -m pip install --upgrade pip >nul 2>&1
python -m pip install aiohttp tqdm qrcode >nul 2>&1

:: Verifica se instalou
python -c "import aiohttp" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [ERRO] Falha ao instalar dependencias.
    echo   Tente manualmente:  python -m pip install aiohttp tqdm qrcode
    echo.
    pause
    exit /b 1
)

:: Chama o launcher (faz tudo sozinho)
python launcher.py

pause

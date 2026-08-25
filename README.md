<div align="center">

# 📚 StemPlay Library

### Biblioteca digital completa com 7652+ materiais educacionais

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)]()
[![Platform](https://img.shields.io/badge/Platform-Linux%20|%20Windows-orange?style=for-the-badge)]()

*Acesse cursos de programação, idiomas, finanças e muito mais — direto no navegador*

</div>

---

## ✨ Features

| Feature | Descrição |
|---------|-----------|
| 🌐 **Acesso Online** | Leia PDFs direto no reader da StemPlay |
| ⬇️ **Download** | Baixe qualquer PDF com um clique |
| 🔍 **Busca Inteligente** | Encontre por curso, aula, módulo ou unidade |
| 🏷️ **Filtros** | Filtre por tipo: Padrão, Teacher, Workbook, Student |
| ⭐ **Favoritos** | Salve seus materiais favoritos (persiste no navegador) |
| 🌓 **Dark/Light Mode** | Alterne entre temas claro e escuro |
| 📱 **Mobile-First** | Interface otimizada para celular com bottom nav |
| 📲 **PWA** | Instale como app no celular |
| 🖥️ **Responsivo** | Funciona perfeitamente em PC, tablet e celular |
| 🔗 **Rede Local** | Acesse de qualquer dispositivo no mesmo Wi-Fi |
| 📱 **QR Code** | Escaneie e acesse instantaneamente pelo celular |

---

## 🚀 Início Rápido

### Windows

> **Dica:** Basta dar duplo clique no `start.bat`! Ele faz tudo automaticamente.

1. Instale o [Python 3.8+](https://www.python.org/downloads/) (marque **"Add Python to PATH"**)
2. Baixe este repositório
3. Dê duplo clique em **`start.bat`**
4. O terminal vai mostrar:
   - ✅ Etapas de inicialização
   - 🌐 URL local e de rede
   - 📱 QR Code para escanear com o celular
5. Acesse pelo navegador ou escaneie o QR Code

### Linux

```bash
# 1. Clone o repositório
git clone https://github.com/dedneves/stemplay-library.git
cd stemplay-library

# 2. Instale dependências
pip3 install aiohttp tqdm qrcode[pil]

# 3. Gere a lista de PDFs (primeira vez apenas)
python3 s3_god_mode.py

# 4. Gere a biblioteca HTML
python3 generate_library_premium.py

# 5. Inicie o servidor
python3 -m http.server 8000 --bind 0.0.0.0
```

Acesse:
- **Local:** `http://localhost:8000/stemplay_library.html`
- **Rede:** `http://SEU_IP:8000/stemplay_library.html`

Para descobrir seu IP:
```bash
hostname -I
# ou
ip route get 1.1.1.1 | awk '{print $7; exit}'
```

---

## 

#!/bin/bash
# ============================================================
# antimustafamir12 Bot - Güncelleme Scripti
# GitHub'dan son kodu çeker, bağımlılıkları günceller, botu yeniden başlatır.
# Kullanım: bot-update   (veya: bash update.sh)
# Otomatik: systemd timer ile her 30 dakikada bir çalışır
# ============================================================

set -e
# Sembolik link güvenli yol çözümü (/usr/local/bin/bot-update linkiyle de çalışır)
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BOT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
SERVICE_NAME="antimustafamir12"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Güncelleme başlıyor..."

cd "$BOT_DIR"

# Git güncellemesi
if [ -d ".git" ]; then
    echo "Git pull yapılıyor..."
    LOCAL=$(git rev-parse HEAD)
    git pull --ff-only
    REMOTE=$(git rev-parse HEAD)
    
    if [ "$LOCAL" == "$REMOTE" ]; then
        echo "Zaten güncel. Değişiklik yok."
        exit 0
    fi
    
    echo "Yeni güncelleme bulundu: $LOCAL -> $REMOTE"
else
    echo "Git deposu bulunamadı, güncelleme atlanıyor."
    exit 1
fi

# Bağımlılıkları güncelle
echo "Bağımlılıklar güncelleniyor..."
source venv/bin/activate
pip install -r requirements.txt -q

# Servisi yeniden başlat
echo "Bot yeniden başlatılıyor..."
sudo systemctl restart ${SERVICE_NAME}.service

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Güncelleme tamamlandı!"

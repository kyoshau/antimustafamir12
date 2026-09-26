#!/bin/bash
# ============================================================
# antimustafamir12 Bot - Raspberry Pi Tek Komut Kurulum Scripti
# Kullanım: curl -sL https://raw.githubusercontent.com/kyoshau/antimustafamir12/main/setup.sh | bash
# veya:    bash setup.sh
# ============================================================

set -e

BOT_DIR="$HOME/antimustafamir12"
SERVICE_NAME="antimustafamir12"
TIMER_NAME="antimustafamir12-update"
REPO_URL="https://github.com/kyoshau/antimustafamir12.git"
UPDATE_INTERVAL="30min"  # Otomatik güncelleme sıklığı

echo ""
echo "=========================================="
echo "  antimustafamir12 Bot - Kurulum Başlıyor"
echo "=========================================="
echo ""

# 1. Sistem güncellemesi ve bağımlılıklar
echo "[1/7] Sistem güncelleniyor ve bağımlılıklar kuruluyor..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv git > /dev/null 2>&1
echo "       Tamam."

# 2. Proje klasörü
if [ -d "$BOT_DIR" ]; then
    echo "[2/7] Mevcut kurulum bulundu: $BOT_DIR"
    cd "$BOT_DIR"
    if [ -d ".git" ]; then
        echo "       Git pull ile güncelleniyor..."
        git pull --ff-only || true
    fi
else
    echo "[2/7] Repo klonlanıyor: $REPO_URL"
    git clone "$REPO_URL" "$BOT_DIR"
    cd "$BOT_DIR"
fi

# 3. Python sanal ortam (venv)
echo "[3/7] Python sanal ortamı oluşturuluyor..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "       Tamam."

# 4. .env dosyası kontrolü
echo "[4/7] .env dosyası kontrol ediliyor..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo ""
        echo "       .env dosyası .env.example'dan oluşturuldu."
        echo "       LÜTFEN .env dosyasını düzenleyip DISCORD_TOKEN'ınızı girin:"
        echo ""
        echo "       nano $BOT_DIR/.env"
        echo ""
    else
        echo "       .env.example bulunamadı. Manuel olarak .env oluşturmanız gerekiyor."
    fi
else
    echo "       .env dosyası zaten mevcut."
fi

# 5. systemd servis dosyası oluştur
echo "[5/7] systemd servisi ayarlanıyor..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=antimustafamir12 Discord Troll Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_DIR
ExecStart=$BOT_DIR/venv/bin/python $BOT_DIR/bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
echo "       Servis oluşturuldu ve açılışta otomatik başlatma etkinleştirildi."

# 6. Otomatik güncelleme timer'ı (GitHub'dan periyodik pull)
echo "[6/7] Otomatik güncelleme zamanlayıcısı ayarlanıyor..."

# Güncelleme servisi (tek seferlik çalışır)
sudo tee /etc/systemd/system/${TIMER_NAME}.service > /dev/null << EOF
[Unit]
Description=antimustafamir12 GitHub Auto-Update
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$BOT_DIR
ExecStart=/bin/bash $BOT_DIR/update.sh
StandardOutput=journal
StandardError=journal
EOF

# Timer (belirli aralıklarla güncelleme servisini tetikler)
sudo tee /etc/systemd/system/${TIMER_NAME}.timer > /dev/null << EOF
[Unit]
Description=antimustafamir12 Auto-Update Timer ($UPDATE_INTERVAL aralıkla)

[Timer]
OnBootSec=2min
OnUnitActiveSec=$UPDATE_INTERVAL
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${TIMER_NAME}.timer
sudo systemctl start ${TIMER_NAME}.timer
echo "       Otomatik güncelleme aktif (her $UPDATE_INTERVAL GitHub'dan çeker)."

# Update scriptinin servisi şifresiz yeniden başlatabilmesi (sınırlı yetki)
sudo tee /etc/sudoers.d/${SERVICE_NAME} > /dev/null << EOF
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart ${SERVICE_NAME}.service, /bin/systemctl restart ${SERVICE_NAME}.service
EOF
sudo chmod 440 /etc/sudoers.d/${SERVICE_NAME}
echo "       Şifresiz restart yetkisi verildi (sadece bu servis için)."

# 7. Manuel güncelleme komutu (her dizinden: bot-update)
echo "[7/7] Manuel güncelleme komutu kuruluyor..."
chmod +x "$BOT_DIR/update.sh"
sudo ln -sf "$BOT_DIR/update.sh" /usr/local/bin/bot-update
echo "       Tamam. Manuel güncelleme için herhangi bir dizinde: bot-update"

echo ""
echo "=========================================="
echo "  Kurulum Tamamlandı!"
echo "=========================================="
echo ""
echo "  Konum:          $BOT_DIR"
echo "  Servis:         $SERVICE_NAME"
echo "  Oto-Güncelleme: Her $UPDATE_INTERVAL (GitHub'dan otomatik çeker)"
echo ""
echo "  Sonraki Adımlar:"
echo "  1. .env dosyasını düzenleyin:"
echo "     nano $BOT_DIR/.env"
echo ""
echo "  2. Botu başlatın:"
echo "     sudo systemctl start $SERVICE_NAME"
echo ""
echo "  3. Logları izleyin:"
echo "     sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "  4. Manuel güncelleme:"
echo "     bot-update"
echo "     (veya: bash $BOT_DIR/update.sh)"
echo ""
echo "  Diğer Komutlar:"
echo "     sudo systemctl stop $SERVICE_NAME         # Durdur"
echo "     sudo systemctl restart $SERVICE_NAME       # Yeniden başlat"
echo "     sudo systemctl status $SERVICE_NAME        # Durum"
echo "     sudo systemctl status $TIMER_NAME.timer    # Oto-güncelleme durumu"
echo "     sudo systemctl list-timers                 # Tüm timer'ları göster"
echo "=========================================="
echo ""

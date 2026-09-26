# antimustafamir12 Discord Troll Bot

Mustafamir12 için özel olarak geliştirilmiş, Artvin ve VLC temalı, öfke analizi yapan, rastgele fun fact ve son dakika haberleri basan Discord troll botu.

---

## Raspberry Pi Kurulumu (Tek Komut)

SSH ile Raspberry Pi'ye bağlan ve şunu yapıştır:

```bash
curl -sL https://raw.githubusercontent.com/kyoshau/antimustafamir12/main/setup.sh | bash
```

Bu kadar. Script otomatik olarak:
- Python3, pip, venv ve git kurar
- Repo'yu `~/antimustafamir12` klasörüne klonlar
- Sanal ortam oluşturur ve bağımlılıkları yükler
- systemd servisi oluşturur (açılışta otomatik başlar, çökerse otomatik yeniden başlar)
- **Otomatik güncelleme timer'ı** kurar (her 30 dakikada GitHub'dan çeker)

### Kurulumdan Sonra

```bash
# 1. Token'ını gir
nano ~/antimustafamir12/.env

# 2. Botu başlat
sudo systemctl start antimustafamir12

# 3. Çalıştığını kontrol et
sudo systemctl status antimustafamir12
```

---

## Otomatik Güncelleme

Bot **her 30 dakikada bir** GitHub'dan otomatik güncelleme çeker. Sen hiçbir şey yapmasan bile:
- GitHub'a push at → Raspberry Pi otomatik olarak son kodu çeker → Bot yeniden başlar

Manuel güncelleme istersen (herhangi bir dizinden):
```bash
bot-update
```

Veya tam yol ile:
```bash
bash ~/antimustafamir12/update.sh
```

Timer durumunu kontrol et:
```bash
sudo systemctl status antimustafamir12-update.timer
sudo systemctl list-timers
```

---

## Günlük Kullanım Komutları

```bash
# Botu başlat
sudo systemctl start antimustafamir12

# Botu durdur
sudo systemctl stop antimustafamir12

# Botu yeniden başlat
sudo systemctl restart antimustafamir12

# Durumunu kontrol et
sudo systemctl status antimustafamir12

# Canlı logları izle
sudo journalctl -u antimustafamir12 -f

# Son 50 satır log
sudo journalctl -u antimustafamir12 -n 50

# Otomatik güncelleme logları
sudo journalctl -u antimustafamir12-update -f
```

---

## Nasıl Çalışır?

Bot **otonom** çalışır — komut yazmaya gerek yoktur:

- **Rastgele zamanlarda** (30-120 dk arası sürpriz): Kanala **Fun Fact**, **Son Dakika Haberi**, **Telemetri Raporu** veya **Mahkeme İlamı** bırakır.
- **Mustafa yazdığında** organik tepkiler verir:
  - Soru sorduğunda (`?`) → "Yok."
  - Caps Lock açtığında → Sismik çıldırma uyarısı (günde 3. caps'te özel etkinlik)
  - Kısa cevap verdiğinde (`tm`, `he`, `hayırdır`) → Fun fact patlatır
  - Tetik kelimeler (`yok`, `sg`, `kes`, `vlc`, `fener`, `ermeni` vb.) → Şansa bağlı özel tepki
  - Rastgele emoji bombardımanı ve "Mustafaca Çevirmen™"
  - Herhangi bir mesajına %25 şansla rastgele troll (fun fact / bilgelik / genel troll)
- **Olay bazlı ifşalar** (şansa bağlı):
  - Mesajını **düzenlerse** → orijinaliyle ifşa
  - Mesajını **silerse** → "kanıt karartma" alarmı
  - **Online/offline/DND** olunca → saatine göre roast (gece 3'te online olduysa ayrı)
  - **Nick değiştirirse** → kimlik değişikliği anonsu
- **Zincir & yokluk sistemleri**:
  - Arka arkaya 3 `yok` → İnkâr Zinciri rekoru
  - 6+ saat sessizlik → Kayıp İhbarı (günde bir)
  - Günlük **Bingo kartı**: 9 tetik kelime, kart dolarsa BINGO anonsu
- **Raporlar**: Her gece 23:55 günlük rapor, her Pazartesi 00:05 haftalık rapor (kelime top 5 + rage grafiği)

> **NOT:** Online/offline trollü için Discord Developer Portal'dan **Presence Intent**'i açman gerekir
> (Bot → Privileged Gateway Intents → Presence Intent). Message Content ve Server Members intentleri de açık olmalı.

### Slash Komutları

| Komut | Açıklama |
| :--- | :--- |
| `/fact` | Anında fun fact atar |
| `/troll` | Son dakika haberi veya bilgelik sözü |
| `/vlc` | VLC kurulum kılavuzu |
| `/rage` | Anlık öfke metresi |
| `/rapor` | Günlük istatistikler |
| `/slot` | İnteraktif slot makinesi |
| `/mahkeme` | Artvin Ağır Ceza Mahkemesi |
| `/sahte_haber` | Özel veya rastgele son dakika haberi |
| `/nick` | Mustafa'nın ismini değiştirir |
| `/cevir` | Mustafaca-Türkçe tercüman |
| `/hedef` | Hedef kullanıcıyı değiştirir |
| `/kanal` | Mesaj kanalını değiştirir |
| `/liderlik` | Kışkırtma ligi sıralaması |
| `/anket` | Troll anket (canlı sonuçlu butonlar) |
| `/karne` | Mustafa'nın resmi karnesi |
| `/dava_gecmisi` | Mahkeme dava arşivi |
| `/hava` | Artvin hava durumu + vücut sıcaklığı |
| `/olay` | [Manuel] Rastgele olay trollü |
| `/kayip` | [Manuel] Kayıp ihbarı |
| `/bingo` | Günlük bingo kartı durumu |
| `/haftalik` | [Manuel] Haftalık rapor |
| `/istatistik` | Kelime top 5 + rage grafiği + genel stats |

---

## Dosya Yapısı

```
antimustafamir12/
├── bot.py              # Ana bot kodu
├── config.py           # Ortam değişkenleri
├── messages.py         # Mesaj havuzları ve tetikleyiciler
├── requirements.txt    # Python bağımlılıkları
├── setup.sh            # Raspberry Pi tek komut kurulumu
├── update.sh           # GitHub güncelleme scripti (manuel + otomatik)
├── .env.example        # Örnek ortam değişkenleri
├── .env                # Gerçek tokenler (git'e dahil değil)
├── .gitignore
└── README.md
```

---

## .env Ayarları

| Değişken | Açıklama | Varsayılan |
| :--- | :--- | :--- |
| `DISCORD_TOKEN` | Bot tokeni (Developer Portal'dan) | — |
| `TARGET_USER_ID` | Hedef kullanıcının Discord ID'si | 1416885917108539454 |
| `CHANNEL_ID` | Troll mesajlarının atılacağı kanal | — |
| `GUILD_ID` | Sunucu ID'si (slash komutları için) | — |
| `RANDOM_INTERVAL_MIN` | Min. rastgele mesaj aralığı (dk) | 30 |
| `RANDOM_INTERVAL_MAX` | Max. rastgele mesaj aralığı (dk) | 120 |
| `TRIGGER_CHANCE_TARGET` | Target tetik kelime yazınca tepki şansı | 0.6 |
| `TRIGGER_CHANCE_OTHERS` | Başkaları tetik kelime yazınca tepki şansı | 0.25 |
| `TARGET_RANDOM_CHANCE` | Target'ın herhangi bir mesajına rastgele troll şansı | 0.25 |
| `EVENT_TROLL_CHANCE` | Olay ifşaları (edit/silme/online/nick) şansı | 0.7 |
| `ABSENCE_HOURS` | Kayıp ihbarı için sessizlik eşiği (saat) | 6 |

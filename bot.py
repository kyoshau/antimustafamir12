import asyncio
import datetime
import json
import logging
import os
import random
import re
import sys
from typing import Optional

# Windows terminal UTF-8 desteği
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
import messages

# ----------------- LOGGING AYARLARI -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("EvilMustafaBot")

# ----------------- VERİ YÖNETİMİ (PERSISTENCE) -----------------
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "target_user_id": config.TARGET_USER_ID,
    "channel_id": config.CHANNEL_ID,
    "inkar_sayisi": 0,
    "ermeni_inkar": 0,
    "fener_inkar": 0,
    "kufur_sayisi": 0,
    "toplam_mesaj": 0,
    "gunluk_mesaj": 0,
    "gunluk_kufur": 0,
    "max_rage": 0,
    "last_report_date": str(datetime.date.today()),
    "kiskirtmalar": {}  # {user_id_str: count}
}

def load_data():
    """Veriyi yükler ve eksik anahtarları varsayılanlarla doldurur."""
    data = DEFAULT_DATA.copy()
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    data.update(saved)
        except Exception as e:
            logger.error(f"Veri yüklenirken hata oluştu: {e}")
            
    if not data.get("target_user_id"):
        data["target_user_id"] = config.TARGET_USER_ID
    if not data.get("channel_id"):
        data["channel_id"] = config.CHANNEL_ID
        
    return data

def save_data(data):
    """Veriyi atomik (atomic replace) olarak güvenle kaydeder."""
    try:
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, DATA_FILE)
    except Exception as e:
        logger.error(f"Veri kaydedilemedi: {e}")

bot_data = load_data()

# ----------------- BOT SETUP -----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

current_rage = 15  # Başlangıç öfke seviyesi 0-100

def get_target_user_id() -> int:
    return bot_data.get("target_user_id") or config.TARGET_USER_ID

def get_channel_id() -> int:
    return bot_data.get("channel_id") or config.CHANNEL_ID

def get_target_mention() -> str:
    tid = get_target_user_id()
    if tid:
        return f"<@{tid}>"
    return "@Mustafamir12"

def record_provocation(user_id: int):
    """Kullanıcının Mustafa'yı kışkırtma sayısını kaydeder."""
    tid = get_target_user_id()
    if user_id == tid or (bot.user and user_id == bot.user.id):
        return
    uid_str = str(user_id)
    if "kiskirtmalar" not in bot_data or not isinstance(bot_data["kiskirtmalar"], dict):
        bot_data["kiskirtmalar"] = {}
    bot_data["kiskirtmalar"][uid_str] = bot_data["kiskirtmalar"].get(uid_str, 0) + 1
    save_data(bot_data)

def calculate_rage_status(rage_val: int):
    if rage_val < 25:
        return "Sakin (0-25)", "Mustafa şimdilik sakin. Gürcistan'dan iyi haberler gelmiş olmalı."
    elif rage_val < 55:
        return "Gergin (25-55)", "Mustafa hafiften bileniyor. Biri 'ermeni' veya 'fener' mi dedi?"
    elif rage_val < 80:
        return "Patlama Noktası (55-80)", "DİKKAT: Artvinli ermeni her an klavyeyi parçalayabilir!"
    else:
        return "DEFCON 1 - Nükleer Çıldırma (80-100)", "MUSTAFA TAMAMEN KONTROLDEN ÇIKTI! 'Amına koyarım tamam' fazına geçildi!"

def make_rage_bar(rage_val: int, length: int = 10) -> str:
    filled = max(0, min(length, int((rage_val / 100) * length)))
    return "█" * filled + "░" * (length - filled)

def check_word_match(trigger: str, text: str) -> bool:
    """Kelimelerin başka kelimelerin içinde sahte eşleşme yapmasını engeller."""
    pattern = rf"(?:\b|\A){re.escape(trigger)}(?:\b|\Z)"
    return bool(re.search(pattern, text, re.IGNORECASE))

# ----------------- ETKİLEŞİMLİ UI BİLEŞENLERİ (VIEWS) -----------------

def generate_slot_embed(user: discord.User | discord.Member):
    items = ["🇦🇲", "🇬🇪", "🔧", "🐱", "🤡", "⚽", "🥔"]
    s1, s2, s3 = random.choice(items), random.choice(items), random.choice(items)
    target_mention = get_target_mention()

    is_jackpot = (s1 == s2 == s3)
    if is_jackpot:
        if s1 == "🇦🇲":
            result_text = f"JACKPOT! {target_mention}'in Erivan vatandaşlık pasaportu onaylandı!"
        elif s1 == "🔧":
            result_text = f"JACKPOT! {target_mention}'e ömür boyu sınırsız VLC Premium kurulum paketi çıktı!"
        elif s1 == "⚽":
            result_text = f"JACKPOT! {target_mention} Fenerbahçe kongre divan heyetine başkan seçildi!"
        elif s1 == "🐱":
            result_text = f"JACKPOT! Profildeki turuncu kedi konuştu: 'Artvinime dokunmayın miyav'!"
        else:
            result_text = f"JACKPOT! {target_mention} bugün 100 kez 'amına koyarım tamam' deme hakkı kazandı!"
    else:
        result_text = f"Kaybettiniz! Ama {target_mention} yine de Artvinli bir larpçı olmaya devam ediyor."

    embed = discord.Embed(
        title="Mustafamir12 Slot Makinesi",
        description=f"**[ {s1} | {s2} | {s3} ]**\n\n{result_text}",
        color=discord.Color.green() if is_jackpot else discord.Color.blurple()
    )
    embed.set_footer(text=f"Çeviren: {user.display_name} • 'Tekrar Döndür' ile şansını dene!")
    return embed, is_jackpot

class SlotView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id

    @discord.ui.button(label="Tekrar Döndür", style=discord.ButtonStyle.primary)
    async def spin_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, _ = generate_slot_embed(interaction.user)
        record_provocation(interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

class MahkemeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="İtiraz Et ('Yok')", style=discord.ButtonStyle.danger)
    async def appeal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_mention = get_target_mention()
        embed = discord.Embed(
            title="Artvin Mahkemesi: İTİRAZ REDDEDİLDİ",
            description=f"Mahkeme Heyeti: *'Sanık {target_mention}'in sunduğu gerekçesiz 'yok' savunması doğrudan reddedilmiştir. Cezası 2 katına çıkarıldı!'*",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Teslim Ol ('Amına koyarım tamam')", style=discord.ButtonStyle.secondary)
    async def surrender_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_mention = get_target_mention()
        embed = discord.Embed(
            title="Artvin Mahkemesi: PİŞMANLIK İNDİRİMİ",
            description=f"Sanık {target_mention} 'amına koyarım tamam' diyerek suçunu itiraf etmiştir. Hafifletici sebep olarak cezası günde 1 saat VLC simgesini izlemeye indirildi.",
            color=discord.Color.dark_green()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Trafik Konisini Kabul Et", style=discord.ButtonStyle.primary)
    async def accept_koni(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_mention = get_target_mention()
        embed = discord.Embed(
            title="Artvin Mahkemesi: İNFAZ PROTOKOLÜ TAMAMLANDI",
            description=f"Karayolları Genel Müdürlüğü Artvin Bölge Başmühendisliği {target_mention} üzerine resmi turuncu trafik konisini başarıyla monte etti.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

# ----------------- EVENTS -----------------

@bot.event
async def on_ready():
    logger.info(f"Bot göreve hazır! Giriş yapıldı: {bot.user}")
    
    # Slash komutlarını sunucuya senkronize et
    if config.GUILD_ID:
        guild_obj = discord.Object(id=config.GUILD_ID)
        tree.copy_global_to(guild=guild_obj)
        await tree.sync(guild=guild_obj)
        logger.info(f"Slash komutları {config.GUILD_ID} ID'li sunucuya senkronize edildi.")
    else:
        await tree.sync()
        logger.info("Slash komutları global olarak senkronize edildi.")

    # Background task döngülerini başlat
    if not random_troll_loop.is_running():
        random_troll_loop.start()
    if not daily_report_loop.is_running():
        daily_report_loop.start()

# Rastgele Saatlerde Fun Fact, Haber, Telemetri ve Mahkeme Döngüsü
@tasks.loop(minutes=config.RANDOM_INTERVAL_MIN)
async def random_troll_loop():
    global current_rage
    await bot.wait_until_ready()
    
    cid = get_channel_id()
    if not cid:
        return

    channel = bot.get_channel(cid)
    if not channel:
        try:
            channel = await bot.fetch_channel(cid)
        except Exception as e:
            logger.error(f"Hedef kanal ({cid}) bulunamadı: {e}")
            return

    choice = random.random()
    target_mention = get_target_mention()

    try:
        if choice < 0.35:
            # 1. Fun Fact (%35 şans)
            fact = random.choice(messages.MUSTAFA_FUN_FACTS).format(target=target_mention)
            embed = discord.Embed(
                title="Biliyor Muydunuz? | Mustafa Fun Fact",
                description=fact,
                color=discord.Color.gold()
            )
            embed.set_footer(text="Mustafa Arşivi & İstihbarat Bülteni")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await channel.send(embed=embed)
        elif choice < 0.55:
            # 2. Son Dakika Haberi (%20 şans)
            haber = random.choice(messages.SON_DAKIKA_HABERLERI)
            embed = discord.Embed(
                title=f"SON DAKİKA | {haber['baslik']}",
                description=haber["icerik"].format(target=target_mention),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Kaynak: {haber['kaynak']}")
            embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await channel.send(embed=embed)
        elif choice < 0.70:
            # 3. Telemetri & İstihbarat Raporu (%15 şans)
            status_title, _ = calculate_rage_status(current_rage)
            msg_tpl = random.choice(messages.TELEMETRI_MESAJLARI)
            msg_text = msg_tpl.format(target=target_mention, rage=current_rage)
            embed = discord.Embed(
                title="Artvin Radar & Telemetri Raporu",
                description=f"{msg_text}\n\n**Mevcut Öfke Durumu:** `{status_title}`",
                color=discord.Color.dark_teal()
            )
            embed.set_footer(text="Anlık Mustafa Takip Sistemi (AMTS)")
            await channel.send(embed=embed)
        elif choice < 0.85:
            # 4. Artvin Ağır Ceza Mahkemesi İlamı (%15 şans)
            dava = random.choice(messages.MAHKEME_DAVALARI)
            embed = discord.Embed(
                title="Artvin 1. Ağır Ceza Mahkemesi Resmi İlamı",
                description=f"**Sanık:** {target_mention}\n**Duruşma Durumu:** Gıyabi Otomatik Celp",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="İsnat Edilen Suç", value=dava["suc"], inline=False)
            embed.add_field(name="Mahkeme Kararı", value=dava["hukum"], inline=False)
            embed.add_field(name="Savcılık Mütalaası", value=dava["savci_yorumu"], inline=False)
            embed.set_footer(text="Aşağıdaki butonlarla davaya müdahale edebilirsiniz.")
            view = MahkemeView()
            await channel.send(embed=embed, view=view)
        elif choice < 0.95:
            # 5. Kadim Bilgelik Sözü (%10 şans)
            soz = random.choice(messages.MUSTAFA_BILGELIK_SOZLERI)
            embed = discord.Embed(
                title="Mustafamir12'nin Kadim Bilgelik Sözleri",
                description=f'*{soz}*\n\n— **{target_mention}** (Artvin Filozofu)',
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
        else:
            # 6. Genel Troll Mesajı (%5 şans)
            msg = random.choice(messages.GENEL_TROLL_MESAJLARI)
            await channel.send(msg.format(target=target_mention))
    except Exception as e:
        logger.error(f"Rastgele troll mesajı gönderilirken hata: {e}")

    # Doğal öfke dalgalanması
    current_rage = max(10, min(95, current_rage + random.randint(-10, 15)))

    # Bir sonraki aralığı rastgele belirle
    min_int = max(5, config.RANDOM_INTERVAL_MIN)
    max_int = max(min_int + 1, config.RANDOM_INTERVAL_MAX)
    next_minutes = random.randint(min_int, max_int)
    random_troll_loop.change_interval(minutes=next_minutes)
    logger.info(f"Sonraki rastgele fun fact / olay {next_minutes} dakika sonra gönderilecek.")

# Gece Yarısı Günlük Rapor Döngüsü (Her dakika kontrol eder, 23:55 sonrası kaçırmaz)
@tasks.loop(minutes=1)
async def daily_report_loop():
    await bot.wait_until_ready()
    now = datetime.datetime.now()
    today_str = str(datetime.date.today())

    if now.hour == 23 and now.minute >= 55 and bot_data.get("last_report_date") != today_str:
        cid = get_channel_id()
        if not cid:
            return
        channel = bot.get_channel(cid)
        if not channel:
            try:
                channel = await bot.fetch_channel(cid)
            except Exception:
                return
        if channel:
            target_mention = get_target_mention()
            status_title, _ = calculate_rage_status(bot_data.get("max_rage", 50))

            embed = discord.Embed(
                title=f"Günlük Mustafa Analizi — {today_str}",
                description=f"{target_mention} için hazırlanan günlük resmi istihbarat raporu:",
                color=discord.Color.dark_purple()
            )
            embed.add_field(name="Toplam Mesaj", value=str(bot_data.get("gunluk_mesaj", 0)), inline=True)
            embed.add_field(name="Küfürlü Mesaj", value=str(bot_data.get("gunluk_kufur", 0)), inline=True)
            embed.add_field(name="Ermeni İnkârı", value=str(bot_data.get("ermeni_inkar", 0)), inline=True)
            embed.add_field(name="Fener İnkârı", value=str(bot_data.get("fener_inkar", 0)), inline=True)
            embed.add_field(name="Genel İnkâr ('Yok')", value=str(bot_data.get("inkar_sayisi", 0)), inline=True)
            embed.add_field(name="Zirve Rage Seviyesi", value=status_title, inline=True)
            embed.add_field(name="VLC Durumu", value="Hâlâ başarıyla monte edilmiş durumda.", inline=False)
            embed.set_footer(text="Artvin 1. Sulh Ceza Denetim Masası")

            try:
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(f"Günlük rapor gönderilemedi: {e}")

            # Günlük istatistikleri sıfırla
            bot_data["gunluk_mesaj"] = 0
            bot_data["gunluk_kufur"] = 0
            bot_data["max_rage"] = 0
            bot_data["last_report_date"] = today_str
            save_data(bot_data)
            logger.info("Günlük rapor başarıyla paylaşıldı ve sayaçlar sıfırlandı.")

# Mesaj Dinleme ve Mustafa Takibi (Organik Tetiklenme Mekanizması)
@bot.event
async def on_message(message: discord.Message):
    global current_rage
    if message.author.bot:
        return

    content_lower = message.content.lower().strip()
    target_id = get_target_user_id()
    is_mustafa = (message.author.id == target_id) if target_id else ("mustafa" in message.author.name.lower())
    already_responded = False

    # 1. Mustafa Mesaj Attıysa İstatistikleri ve Rage'i Güncelle
    if is_mustafa:
        bot_data["toplam_mesaj"] = bot_data.get("toplam_mesaj", 0) + 1
        bot_data["gunluk_mesaj"] = bot_data.get("gunluk_mesaj", 0) + 1

        # Küfür kontrolü - Tam kelime eşleme ile
        kufurler = ["amk", "aq", "mk", "sik", "sikeyim", "sikerim", "amına", "yarrak", "yarram", "puşt", "orospu", "piç", "göt"]
        has_kufur = any(check_word_match(k, content_lower) for k in kufurler)

        if has_kufur:
            bot_data["kufur_sayisi"] = bot_data.get("kufur_sayisi", 0) + 1
            bot_data["gunluk_kufur"] = bot_data.get("gunluk_kufur", 0) + 1
            current_rage = min(100, current_rage + 15)
        else:
            current_rage = max(0, current_rage - 3)

        # Caps lock rage etkisi
        if len(message.content) > 5 and message.content.isupper():
            current_rage = min(100, current_rage + 20)

        bot_data["max_rage"] = max(bot_data.get("max_rage", 0), current_rage)
        save_data(bot_data)

        # Emoji Reaksiyonu Bombardımanı (%35 şansla Mustafa'ya emoji at)
        if random.random() < 0.35:
            selected_emojis = random.sample(messages.TROLL_EMOJILER, k=min(3, len(messages.TROLL_EMOJILER)))
            for emoji in selected_emojis:
                try:
                    await message.add_reaction(emoji)
                    await asyncio.sleep(0.2)
                except Exception:
                    pass

        # A) CAPS LOCK ÇILDIRMA TEPKİSİ
        if len(message.content) > 6 and message.content.isupper() and random.random() < 0.60:
            target_mention = get_target_mention()
            embed = discord.Embed(
                title="SİSMİK ÇILDIRMA UYARISI (DEFCON 1)",
                description=f"{target_mention} Caps Lock açarak Artvin Çoruh barajını titretti! Öfke seviyesi: %{current_rage}. Lütfen acil olarak ortama bir adet sakinleştirici turuncu koni bırakınız!",
                color=discord.Color.dark_red()
            )
            try:
                await message.channel.send(embed=embed)
                already_responded = True
            except Exception:
                pass

        # B) SORU İŞARETİ (?) SORDUYSA (%45 şansla 'Yok' cevabı)
        if not already_responded and message.content.endswith("?") and random.random() < 0.45:
            target_mention = get_target_mention()
            try:
                await message.channel.send(f"{target_mention} evrenin sırlarını sorguluyor... Kadim Artvin Dağları'ndan gelen nihai cevap: **'Yok.'**")
                already_responded = True
            except Exception:
                pass

        # C) KISA / DARLANMA CEVAPLARI (he, tm, tamam, noldu, hayırdır)
        kisa_sozler = ["he", "tm", "tamam", "noldu", "hayırdır", "ne diyon", "boş yapma"]
        if not already_responded and any(content_lower == ks for ks in kisa_sozler) and random.random() < 0.40:
            target_mention = get_target_mention()
            fact = random.choice(messages.MUSTAFA_FUN_FACTS).format(target=target_mention)
            try:
                await message.channel.send(fact)
                already_responded = True
            except Exception:
                pass

        # D) MUSTAFA ÇEVİRMEN (%20 şansla ne demek istediğini açıkla)
        if not already_responded and random.random() < 0.20:
            matched_ceviri = None
            for trigger, meaning in messages.CEVIRMEN_SOZLUK:
                if check_word_match(trigger, content_lower):
                    matched_ceviri = meaning
                    break
            if not matched_ceviri:
                matched_ceviri = "Aslında çok kırılgan biriyim, Artvin dağlarında tek başıma ağlıyorum."

            embed = discord.Embed(
                title="Mustafaca Çevirmen™",
                description=f"**Mustafa aslında ne demek istedi:**\n> \"{matched_ceviri}\"",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Türkçe - Mustafaca Yeminli Tercüme Bürosu")
            try:
                await message.channel.send(embed=embed)
                already_responded = True
            except Exception:
                pass

    # 2. Tetik Kelime Kontrolleri (Kelimelerin içine sahte eşleşme yapmaz)
    # Görünür tepkiler artık şansa bağlı tetiklenir (config.TRIGGER_CHANCE_*), sayaçlar her durumda işlenir
    if not already_responded:
        for trigger, responses in messages.TETIK_CEVAPLAR.items():
            if check_word_match(trigger, content_lower):
                if is_mustafa:
                    if trigger == "yok":
                        bot_data["inkar_sayisi"] = bot_data.get("inkar_sayisi", 0) + 1
                    elif trigger == "ermeni":
                        bot_data["ermeni_inkar"] = bot_data.get("ermeni_inkar", 0) + 1
                    elif trigger == "fener":
                        bot_data["fener_inkar"] = bot_data.get("fener_inkar", 0) + 1
                    save_data(bot_data)
                else:
                    # Başka bir üye Mustafa'yı kışkırtıyorsa skora yaz
                    record_provocation(message.author.id)

                chance = config.TRIGGER_CHANCE_TARGET if is_mustafa else config.TRIGGER_CHANCE_OTHERS
                if random.random() < chance:
                    target_mention = get_target_mention()
                    reply_text = random.choice(responses).format(target=target_mention)
                    try:
                        await message.channel.send(reply_text)
                        already_responded = True
                    except Exception:
                        pass
                break

    # 3. Target herhangi bir mesaj yazdıysa rastgele troll tepkisi (şansa bağlı)
    if is_mustafa and not already_responded and random.random() < config.TARGET_RANDOM_CHANCE:
        target_mention = get_target_mention()
        choice = random.random()
        try:
            if choice < 0.4:
                fact = random.choice(messages.MUSTAFA_FUN_FACTS).format(target=target_mention)
                await message.channel.send(fact)
            elif choice < 0.7:
                soz = random.choice(messages.MUSTAFA_BILGELIK_SOZLERI)
                await message.channel.send(f'"{soz}"\n\n— **{target_mention}** (Az önce söyledi, biz not aldık)')
            else:
                msg = random.choice(messages.GENEL_TROLL_MESAJLARI).format(target=target_mention)
                await message.channel.send(msg)
            already_responded = True
        except Exception:
            pass

    await bot.process_commands(message)

# ----------------- GLOBAL APP COMMAND ERROR HANDLER -----------------

@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        msg = f"Sakin ol! Bu komut için bekleme süresindesin: {error.retry_after:.1f} saniye."
    elif isinstance(error, app_commands.MissingPermissions):
        msg = "Bu komutu kullanmak için yetkiniz bulunmuyor."
    else:
        logger.error(f"Slash komut hatası: {error}", exc_info=True)
        msg = f"Komut çalıştırılırken bir sorun oluştu: {error}"

    try:
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
    except Exception:
        pass

# ----------------- SLASH KOMUTLARI (DEBUG & MANUEL TEST) -----------------

@tree.command(name="fact", description="[Debug/Test] Mustafa hakkında anında rastgele bir Fun Fact atar.")
async def slash_fact(interaction: discord.Interaction):
    record_provocation(interaction.user.id)
    target_mention = get_target_mention()
    fact = random.choice(messages.MUSTAFA_FUN_FACTS).format(target=target_mention)
    embed = discord.Embed(
        title="Biliyor Muydunuz? | Mustafa Fun Fact",
        description=fact,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Tetikleyen: {interaction.user.display_name} • [Debug/Test]")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    await interaction.response.send_message(embed=embed)

@tree.command(name="troll", description="[Debug/Test] Mustafamir12'ye anında troll mesaj veya son dakika haberi yollar.")
async def slash_troll(interaction: discord.Interaction):
    record_provocation(interaction.user.id)
    target_mention = get_target_mention()
    choice = random.choice([1, 2, 3])

    if choice == 1:
        haber = random.choice(messages.SON_DAKIKA_HABERLERI)
        embed = discord.Embed(
            title=f"SON DAKİKA | {haber['baslik']}",
            description=haber["icerik"].format(target=target_mention),
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Kaynak: {haber['kaynak']}")
        await interaction.response.send_message(embed=embed)
    elif choice == 2:
        soz = random.choice(messages.MUSTAFA_BILGELIK_SOZLERI)
        embed = discord.Embed(
            title="Mustafamir12'nin Özlü Sözü",
            description=f'"{soz}"\n\n— **{target_mention}**',
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)
    else:
        msg = random.choice(messages.GENEL_TROLL_MESAJLARI).format(target=target_mention)
        await interaction.response.send_message(msg)

@tree.command(name="vlc", description="Mustafamir12 için özel hazırlanmış VLC Kurulum Kılavuzunu açar.")
async def slash_vlc(interaction: discord.Interaction):
    record_provocation(interaction.user.id)
    target_mention = get_target_mention()
    steps_formatted = "\n".join(messages.VLC_KURULUM_ADIMLARI).format(target=target_mention)

    embed = discord.Embed(
        title="VLC Media Player Resmi Kurulum Sihirbazı v6.9",
        description=f"Sayın {target_mention}, sunucu sakinleri tarafından talep edilen VLC kurulum protokolü aşağıdadır:\n\n{steps_formatted}",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url="https://images.videolan.org/images/icons-pressed/vlc.png")
    embed.set_footer(text="VideoLAN & Artvin Bölge Bayii Ortak Hizmetidir.")
    await interaction.response.send_message(embed=embed)

@tree.command(name="rage", description="Mustafamir12'nin anlık öfke seviyesini ve DEFCON durumunu gösterir.")
async def slash_rage(interaction: discord.Interaction):
    target_mention = get_target_mention()
    status_title, status_desc = calculate_rage_status(current_rage)
    bar = make_rage_bar(current_rage)

    embed = discord.Embed(
        title="Mustafamir12 Öfke & Rage Metresi",
        description=f"Hedef: {target_mention}\n\n**Öfke Seviyesi:** `[{bar}]` %{current_rage}\n**Durum:** {status_title}\n\n_{status_desc}_",
        color=discord.Color.red() if current_rage > 50 else discord.Color.green()
    )
    embed.set_footer(text="Öneri: Mustafa'nın yanında 'yok' veya 'vlc' kelimelerini fısıldamayın.")
    await interaction.response.send_message(embed=embed)

@tree.command(name="rapor", description="Bugünkü Mustafa verilerini (küfür, inkar, rage) gösterir.")
async def slash_rapor(interaction: discord.Interaction):
    target_mention = get_target_mention()
    status_title, _ = calculate_rage_status(current_rage)

    embed = discord.Embed(
        title="Mustafa İstihbarat Raporu",
        description=f"Hedef: {target_mention}",
        color=discord.Color.purple()
    )
    embed.add_field(name="Toplam Mesaj", value=str(bot_data.get("toplam_mesaj", 0)), inline=True)
    embed.add_field(name="Küfür Sayacı", value=str(bot_data.get("kufur_sayisi", 0)), inline=True)
    embed.add_field(name="Ermeni İnkârı", value=str(bot_data.get("ermeni_inkar", 0)), inline=True)
    embed.add_field(name="Fener İnkârı", value=str(bot_data.get("fener_inkar", 0)), inline=True)
    embed.add_field(name="'Yok' Sayacı", value=str(bot_data.get("inkar_sayisi", 0)), inline=True)
    embed.add_field(name="Mevcut Rage", value=f"%{current_rage} ({status_title})", inline=True)
    embed.set_footer(text="Veriler her gün 23:59'da sıfırlanıp genel arşive kaydedilir.")
    await interaction.response.send_message(embed=embed)

@tree.command(name="slot", description="Mustafa temalı interaktif slot makinesi çevir.")
async def slash_slot(interaction: discord.Interaction):
    record_provocation(interaction.user.id)
    embed, _ = generate_slot_embed(interaction.user)
    view = SlotView(author_id=interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="nick", description="Mustafa'nın sunucu ismini troll bir isimle değiştirir (Yetki gerekir).")
async def slash_nick(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("Bu komut sadece sunucularda çalışır.", ephemeral=True)
        return

    tid = get_target_user_id()
    member = interaction.guild.get_member(tid) if tid else None
    if not member:
        await interaction.response.send_message("Hedef kullanıcı sunucuda bulunamadı veya TARGET_USER_ID ayarlanmamış.", ephemeral=True)
        return

    new_nick = random.choice(messages.NICKNAME_HAVUZU)
    try:
        await member.edit(nick=new_nick)
        record_provocation(interaction.user.id)
        await interaction.response.send_message(f"Mustafa'nın yeni kimliği hayırlı olsun: **{new_nick}**")
    except discord.Forbidden:
        await interaction.response.send_message(f"Botun rol yetkisi Mustafa'nın ismini değiştirmeye yetmiyor (Botun rolünü Mustafa'nın rolünün üstüne taşıyın). Seçilen isim: **{new_nick}**", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Hata oluştu: {e}", ephemeral=True)

@tree.command(name="cevir", description="Mustafaca bir cümleyi Türkçeye çevirir.")
@app_commands.describe(mesaj="Mustafa'nın yazdığı mesaj")
async def slash_cevir(interaction: discord.Interaction, mesaj: str):
    found = None
    for trigger, meaning in messages.CEVIRMEN_SOZLUK:
        if check_word_match(trigger, mesaj):
            found = meaning
            break
    if not found:
        found = "Bu karmaşık Artvin lehçesi henüz çözülemedi ancak muhtemelen ağlıyor."

    embed = discord.Embed(
        title="Mustafaca Tercümanlık",
        description=f"**Orijinal:** {mesaj}\n**Tercüme:** \"{found}\"",
        color=discord.Color.teal()
    )
    await interaction.response.send_message(embed=embed)

@tree.command(name="hedef", description="Trollenecek hedef kullanıcının ID'sini ayarlar ve kalıcı kaydeder.")
@app_commands.describe(kullanici="Hedef Discord kullanıcısı")
async def slash_hedef(interaction: discord.Interaction, kullanici: discord.Member):
    bot_data["target_user_id"] = kullanici.id
    save_data(bot_data)
    await interaction.response.send_message(
        f"Yeni hedef kilitlendi ve kalıcı kaydedildi: {kullanici.mention} ({kullanici.name})! Artık tüm füzeler ona doğrultuldu.",
        ephemeral=False
    )

@tree.command(name="kanal", description="Troll ve Fun Fact mesajlarının atılacağı kanalı ayarlar.")
@app_commands.describe(kanal="Hedef metin kanalı")
async def slash_kanal(interaction: discord.Interaction, kanal: discord.TextChannel):
    bot_data["channel_id"] = kanal.id
    save_data(bot_data)
    await interaction.response.send_message(
        f"Hedef kanal güncellendi ve kalıcı kaydedildi: {kanal.mention}! Artık tüm Fun Fact ve troll yayınları buraya yapılacak.",
        ephemeral=False
    )


@tree.command(name="liderlik", description="Mustafa'yı en çok kışkırtan sunucu üyelerinin sıralaması.")
async def slash_liderlik(interaction: discord.Interaction):
    kiskirtmalar = bot_data.get("kiskirtmalar", {})
    if not kiskirtmalar:
        await interaction.response.send_message("Henüz kimse Mustafa'yı kışkırtmadı. İlk kışkırtan sen ol!", ephemeral=True)
        return

    # Puana göre sırala
    sorted_users = sorted(kiskirtmalar.items(), key=lambda item: item[1], reverse=True)[:10]

    lines = []
    for idx, (uid_str, score) in enumerate(sorted_users):
        lines.append(f"**{idx+1}.** <@{uid_str}> — **{score}** kışkırtma")

    embed = discord.Embed(
        title="Mustafa Kışkırtma Ligi (Liderlik Tablosu)",
        description="\n".join(lines),
        color=discord.Color.gold()
    )
    embed.set_footer(text="Mustafa'yı rage'e sokan herkese tebrikler!")
    await interaction.response.send_message(embed=embed)

@tree.command(name="mahkeme", description="Mustafa'yı Artvin 1. Ağır Ceza Mahkemesi'nde yargıla.")
async def slash_mahkeme(interaction: discord.Interaction):
    record_provocation(interaction.user.id)
    target_mention = get_target_mention()
    dava = random.choice(messages.MAHKEME_DAVALARI)

    embed = discord.Embed(
        title="Artvin 1. Ağır Ceza Mahkemesi Celbi",
        description=f"**Sanık:** {target_mention}\n**Duruşma Hakimi:** {interaction.user.mention}",
        color=discord.Color.dark_red()
    )
    embed.add_field(name="İsnat Edilen Suç", value=dava["suc"], inline=False)
    embed.add_field(name="Mahkeme Heyeti Hükmü", value=dava["hukum"], inline=False)
    embed.add_field(name="Savcılık Mütalaası", value=dava["savci_yorumu"], inline=False)
    embed.set_footer(text="Karar kesindir, temyiz yolu Artvin dağlarında kapalıdır.")

    view = MahkemeView()
    await interaction.response.send_message(embed=embed, view=view)

@tree.command(name="sahte_haber", description="Mustafa hakkında anında özel veya rastgele son dakika haberi basar.")
@app_commands.describe(konu="Özel haber başlığı veya konusu (boş bırakırsan rastgele gelir)")
async def slash_sahte_haber(interaction: discord.Interaction, konu: Optional[str] = None):
    record_provocation(interaction.user.id)
    target_mention = get_target_mention()

    if konu:
        title = f"SON DAKİKA | {konu}"
        description = (
            f"Artvin İstihbarat Bürosu'ndan gelen sıcak bilgilere göre, {target_mention} konuyla ilgili "
            f"yaptığı ilk basın açıklamasında 'Ben fenerli değilim, amına koyarım tamam' diyerek iddiaları yalanladı. "
            f"Görgü tanıkları şahsın hızla Gürcistan sınırına doğru ilerlediğini belirtiyor."
        )
        kaynak = "Özel Artvin Haber Ajansı"
    else:
        haber = random.choice(messages.SON_DAKIKA_HABERLERI)
        title = f"SON DAKİKA | {haber['baslik']}"
        description = haber["icerik"].format(target=target_mention)
        kaynak = haber["kaynak"]

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Kaynak: {kaynak} • Muhabir: {interaction.user.display_name}")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    await interaction.response.send_message(embed=embed)

# ----------------- ÇALIŞTIRMA -----------------

if __name__ == "__main__":
    token = config.DISCORD_TOKEN
    if not token or token == "BURAYA_BOT_TOKENI_YAPISTIR":
        logger.error("LÜTFEN .env DOSYASINA GEÇERLİ BİR DISCORD_TOKEN YAZIN!")
    else:
        try:
            bot.run(token)
        except discord.errors.PrivilegedIntentsRequired:
            logger.error(
                "\n"
                "========================================================================\n"
                "HATA: AYRICALIKLI NİYETLER (PRIVILEGED INTENTS) AÇIK DEĞİL!\n"
                "Botun mesajları dinleyebilmesi ve Mustafa'yı takip edebilmesi için Discord\n"
                "Developer Portal'dan izinleri açmanız gerekir:\n\n"
                "1. https://discord.com/developers/applications adresine gidin.\n"
                "2. Botunuzu seçip sol menüden 'Bot' sekmesine tıklayın.\n"
                "3. 'Privileged Gateway Intents' başlığı altındaki şu ayarları AÇIN:\n"
                "   - Message Content Intent (Mesajları okumak için ZORUNLU)\n"
                "   - Server Members Intent (Kullanıcıları görmek için ZORUNLU)\n"
                "4. En alttan 'Save Changes' butonuna tıklayıp kaydedin.\n"
                "5. Ardından botu tekrar çalıştırın!\n"
                "========================================================================"
            )
        except Exception as e:
            logger.error(f"Bot çalışırken beklenmeyen bir hata oluştu: {e}")

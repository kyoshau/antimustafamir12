import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID", "1416885917108539454"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1192132603550117932"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

RANDOM_INTERVAL_MIN = int(os.getenv("RANDOM_INTERVAL_MIN", "30"))
RANDOM_INTERVAL_MAX = int(os.getenv("RANDOM_INTERVAL_MAX", "120"))

# Tetik kelime tepkilerinin rastgele tetiklenme şansları (0.0 - 1.0)
# Target tetik kelime yazınca tepki verme şansı
TRIGGER_CHANCE_TARGET = float(os.getenv("TRIGGER_CHANCE_TARGET", "0.6"))
# Başka üyeler tetik kelime yazınca tepki verme şansı (0 = tamamen kapalı)
TRIGGER_CHANCE_OTHERS = float(os.getenv("TRIGGER_CHANCE_OTHERS", "0.25"))
# Target herhangi bir mesaj yazdığında rastgele troll tepkisi şansı
TARGET_RANDOM_CHANCE = float(os.getenv("TARGET_RANDOM_CHANCE", "0.25"))
# Olay bazlı troll şansı (edit/silme/online/nick ifşaları) (0.0 - 1.0)
EVENT_TROLL_CHANCE = float(os.getenv("EVENT_TROLL_CHANCE", "0.7"))
# Kayıp ihbarı için gereken sessizlik süresi (saat)
ABSENCE_HOURS = int(os.getenv("ABSENCE_HOURS", "6"))

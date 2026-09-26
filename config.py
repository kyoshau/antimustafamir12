import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID", "1416885917108539454"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1192132603550117932"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

RANDOM_INTERVAL_MIN = int(os.getenv("RANDOM_INTERVAL_MIN", "30"))
RANDOM_INTERVAL_MAX = int(os.getenv("RANDOM_INTERVAL_MAX", "120"))

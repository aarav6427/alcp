from os import getenv
from dotenv import load_dotenv

load_dotenv()

API_ID = int(getenv("API_ID", 0))
API_HASH = getenv("API_HASH", None)
BOT_TOKEN = getenv("BOT_TOKEN", None)
OWNER_ID = int(getenv("OWNER_ID", 1282754256))
SUDO_USERS = list(map(int, getenv("OWNER_ID", "5356564375 5336023580").split()))


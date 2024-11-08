from os import getenv
from dotenv import load_dotenv

load_dotenv()

API_ID = int(getenv("API_ID", 2645474)
API_HASH = getenv("API_HASH", 6c9a5044d2f2c2350ac20b3838a7896e)
BOT_TOKEN = getenv("BOT_TOKEN", 7919367706:AAHHUP6WcmYh6INvMFqEjL_k9EWQcyYkKK4)
OWNER_ID = int(getenv("OWNER_ID", 929216155))
SUDO_USERS = list(map(int, getenv("OWNER_ID", "5356564375 5336023580").split()))


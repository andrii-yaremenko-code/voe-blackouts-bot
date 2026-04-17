import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
EIC_CODE = os.getenv("EIC_CODE")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 600))
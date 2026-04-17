import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

EIC_CODE = os.getenv("EIC_CODE")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))

BASE_URL = os.getenv("BASE_URL")

WEBHOOK_SECRET_PATH = os.getenv("WEBHOOK_SECRET_PATH", "webhook")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "secret")
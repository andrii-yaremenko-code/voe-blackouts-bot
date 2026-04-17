import time
import threading
from datetime import datetime, timedelta

from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

from config import *
from voe import get_blackouts

# =====================
# APP
# =====================
app = Flask(__name__)

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# =====================
# STATE
# =====================
last_state = None
last_send_time = None
user_last_call = {}

COOLDOWN = 1800
USER_RATE_LIMIT = 5


# =====================
# SECURITY HELPERS
# =====================
def is_allowed_chat(update):
    return str(update.effective_chat.id) == str(CHAT_ID)


def rate_limit_ok(user_id):
    now = time.time()
    last = user_last_call.get(user_id)

    if last and now - last < USER_RATE_LIMIT:
        return False

    user_last_call[user_id] = now
    return True


def send(text):
    bot.send_message(chat_id=CHAT_ID, text=text)


# =====================
# COMMANDS
# =====================
def start(update, context):
    if not is_allowed_chat(update):
        return
    update.message.reply_text("🤖 Bot is running (secure webhook)")


def status(update, context):
    if not is_allowed_chat(update):
        return
    if not rate_limit_ok(update.effective_user.id):
        return

    result = get_blackouts(EIC_CODE)
    update.message.reply_text(str(result))


def today(update, context):
    if not is_allowed_chat(update):
        return
    if not rate_limit_ok(update.effective_user.id):
        return

    result = get_blackouts(EIC_CODE)
    update.message.reply_text("📅 Today:\n" + str(result))


dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("today", today))


# =====================
# WEBHOOK
# =====================
@app.route(f"/{WEBHOOK_SECRET_PATH}", methods=["POST"])
def webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if secret != WEBHOOK_SECRET_TOKEN:
        print("❌ Unauthorized request")
        abort(403)

    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)

    return "ok"


# =====================
# MONITOR LOOP
# =====================
def monitor():
    global last_state, last_send_time

    while True:
        try:
            result = get_blackouts(EIC_CODE)
            now = datetime.now()

            if result and result != "NO":
                changed = result != last_state

                can_send = (
                    last_send_time is None or
                    now - last_send_time > timedelta(seconds=COOLDOWN)
                )

                if changed and can_send:
                    send("⚠️ Power alert:\n" + result)
                    last_state = result
                    last_send_time = now

        except Exception as e:
            print("monitor error:", e)

        time.sleep(CHECK_INTERVAL)


# =====================
# HEALTH CHECK
# =====================
@app.route("/")
def home():
    return "OK - bot running"


# =====================
# START WEBHOOK
# =====================
def setup_webhook():
    webhook_url = f"{BASE_URL}/{WEBHOOK_SECRET_PATH}"

    bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET_TOKEN
    )

    print("Webhook set:", webhook_url)


# =====================
# START
# =====================
if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()

    setup_webhook()

    app.run(host="0.0.0.0", port=10000)
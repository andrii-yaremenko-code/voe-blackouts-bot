import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
import time
from datetime import datetime, timedelta

from flask import Flask, request, abort
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from config import *
from voe import get_blackouts

# =====================
# APP
# =====================
app = Flask(__name__)

application = ApplicationBuilder().token(BOT_TOKEN).build()

last_state = None
last_send_time = None
user_last_call = {}

COOLDOWN = 1800
USER_RATE_LIMIT = 5


# =====================
# HELPERS
# =====================
def is_allowed(chat_id):
    return str(chat_id) == str(CHAT_ID)


def rate_limit_ok(user_id):
    now = time.time()
    last = user_last_call.get(user_id)

    if last and now - last < USER_RATE_LIMIT:
        return False

    user_last_call[user_id] = now
    return True


# =====================
# COMMANDS (ASYNC)
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_chat.id):
        return
    await update.message.reply_text("🤖 Async bot running")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_chat.id):
        return
    if not rate_limit_ok(update.effective_user.id):
        return

    result = get_blackouts(EIC_CODE)
    await update.message.reply_text(str(result))


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_chat.id):
        return
    if not rate_limit_ok(update.effective_user.id):
        return

    result = get_blackouts(EIC_CODE)
    await update.message.reply_text("📅 Today:\n" + str(result))


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("status", status))
application.add_handler(CommandHandler("today", today))


# =====================
# WEBHOOK
# =====================
@app.route(f"/{WEBHOOK_SECRET_PATH}", methods=["POST"])
def webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

    if secret != WEBHOOK_SECRET_TOKEN:
        print("❌ Unauthorized request")
        abort(403)

    update = Update.de_json(request.get_json(force=True), application.bot)

    asyncio.run_coroutine_threadsafe(
        application.process_update(update),
        loop
    )

    return "ok"


# =====================
# MONITOR (ASYNC LOOP)
# =====================
async def monitor():
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
                    await application.bot.send_message(
                        chat_id=CHAT_ID,
                        text="⚠️ Power alert:\n" + result
                    )
                    last_state = result
                    last_send_time = now

        except Exception as e:
            print("monitor error:", e)

        await asyncio.sleep(CHECK_INTERVAL)


# =====================
# HEALTH
# =====================
@app.route("/")
def home():
    return "OK async bot running"


# =====================
# STARTUP
# =====================
async def setup():
    webhook_url = f"{BASE_URL}/{WEBHOOK_SECRET_PATH}"

    # 🔥 ВАЖНО
    await application.initialize()

    await application.bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET_TOKEN
    )

    print("Webhook set:", webhook_url)

    asyncio.create_task(monitor())


def start_async():
    loop.run_until_complete(setup())
    loop.run_forever()


# =====================
# MAIN
# =====================
if __name__ == "__main__":
    import threading

    threading.Thread(target=start_async, daemon=True).start()

    app.run(host="0.0.0.0", port=10000)
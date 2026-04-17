import time
from datetime import datetime, timedelta
from telegram.ext import Updater, CommandHandler
from config import BOT_TOKEN, CHAT_ID, EIC_CODE, CHECK_INTERVAL
from voe import get_blackouts

# ======================
# 🔧 настройки
# ======================
COOLDOWN = 1800  # антиспам (30 мин)

last_state = None
last_send_time = None

updater = Updater(token=BOT_TOKEN, use_context=True)
bot = updater.bot


# ======================
# 📤 отправка
# ======================
def send(text):
    bot.send_message(chat_id=CHAT_ID, text=text)


# ======================
# 🤖 команды
# ======================
def start(update, context):
    if str(update.effective_chat.id) != str(CHAT_ID):
        return
    update.message.reply_text("🤖 Бот работает.\nКоманды:\n/status\n/today")


def status(update, context):
    if str(update.effective_chat.id) != str(CHAT_ID):
        return

    result = get_blackouts(EIC_CODE)

    if result is None:
        update.message.reply_text("⚠️ Ошибка получения данных")
    elif result == "NO":
        update.message.reply_text("✅ Сейчас отключений нет")
    else:
        update.message.reply_text("⚠️ Сейчас:\n" + result)


def today(update, context):
    if str(update.effective_chat.id) != str(CHAT_ID):
        return

    result = get_blackouts(EIC_CODE)

    if result is None:
        update.message.reply_text("⚠️ Ошибка получения данных")
    elif result == "NO":
        update.message.reply_text("✅ Сегодня отключений нет")
    else:
        update.message.reply_text("📅 Сегодня:\n" + result)


# ======================
# 🔁 фоновая проверка
# ======================
def monitor(context):
    global last_state, last_send_time

    result = get_blackouts(EIC_CODE)
    now = datetime.now()

    if result is None:
        return

    if result == "NO":
        last_state = None
        return

    normalized = result.strip()

    changed = (normalized != last_state)

    can_send = (
        last_send_time is None or
        now - last_send_time > timedelta(seconds=COOLDOWN)
    )

    if changed and can_send:
        send("⚠️ Возможны отключения:\n" + normalized)

        last_state = normalized
        last_send_time = now


# ======================
# 🚀 запуск
# ======================
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("today", today))

# фоновая задача
updater.job_queue.run_repeating(monitor, interval=CHECK_INTERVAL, first=5)

print("Бот запущен...")
updater.start_polling()
updater.idle()
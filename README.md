# VOE Blackout Bot

Telegram bot for monitoring electricity outages (VOE Ukraine).

## Setup

1. Copy `.env.example` → `.env`
2. Fill values:
   - BOT_TOKEN
   - CHAT_ID
   - EIC_CODE

## Install

```bash
pip install -r requirements.txt
```

## 📲 Как это выглядит

Ты пишешь боту:

/status

👉 ответ:

✅ Сейчас отключений нет

/today

👉 ответ:

📅 Сегодня:
08:00–10:00
18:00–20:00
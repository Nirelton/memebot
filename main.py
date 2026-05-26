from telegram.ext import *
import random

TOKEN = "8635966932:AAFkbhq9n0o6elo0ml61-s3jQWg1jGCOUIs"

blacklist = []

reply_chance = 0.35

triggers = {
    "гойда": [
        "ГОЙДААА 💀",
        "черти активировались",
        "шиза пошла по трубам"
    ],

    "спать": [
        "иди нахуй спи",
        "сон для слабых",
        "кладбище ждёт"
    ],

    "кот": [
        "🐈",
        "кот найден",
        "мяу блять"
    ]
}

async def message(update, context):

    if not update.message.text:
        return

    text = update.message.text.lower()
    user_id = update.message.from_user.id

    if user_id in blacklist:
        return

    for trigger in triggers:

        if trigger in text:

            if random.random() < reply_chance:

                await update.message.reply_text(
                    random.choice(triggers[trigger])
                )

                return

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(
    MessageHandler(filters.TEXT, message)
)

print("бот запущен")

app.run_polling()

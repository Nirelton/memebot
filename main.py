from telegram.ext import *
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import json, os, random, time, re
import asyncio

TOKEN = "8635966932:AAFkbhq9n0o6elo0ml61-s3jQWg1jGCOUIs"
OWNER_ID = 1235534514

DATA_FILE = "data.json"

default_data = {
    "groups": {},
    "global_triggers": {}
}

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_group(chat_id):
    chat_id = str(chat_id)

    if chat_id not in data["groups"]:
        data["groups"][chat_id] = {
            "reply_chance": 35,
            "reaction_chance": 40,
            "cooldown": 10,
            "enabled": True,
            "last_reply": 0,
            "mode": "normal",
            "mode_until": 0
        }
        save_data()


# ---------------- SAFETY LOCK (ВАЖНО) ----------------

_running_lock = False


# ---------------- REACT ----------------

async def react(update, context):
    emojis = ["👍", "😂", "🔥", "💀", "🤡", "👀"]

    try:
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            reaction=[random.choice(emojis)]
        )
    except:
        pass


# ---------------- MESSAGE ----------------

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_chat.type == "private":
        return

    chat_id = str(update.effective_chat.id)
    ensure_group(chat_id)
    group = data["groups"][chat_id]

    text = (update.message.text or "").lower()
    user_id = update.message.from_user.id

    if not group["enabled"]:
        return

    # cooldown
    if time.time() - group["last_reply"] < group["cooldown"]:
        return

    # triggers
    for trig, responses in data["global_triggers"].items():
        if trig in text:
            r = random.choice(responses)

            try:
                if r["type"] == "text":
                    await update.message.reply_text(r["content"])
            except:
                pass

            group["last_reply"] = time.time()
            save_data()

            await react(update, context)
            return


# ---------------- INIT BOT SAFETY ----------------

async def post_init(app):
    # убивает любые старые webhook/polling хвосты
    await app.bot.delete_webhook(drop_pending_updates=True)


# ---------------- MAIN ----------------

def main():
    global _running_lock

    if _running_lock:
        print("BOT ALREADY RUNNING - SKIP SECOND INSTANCE")
        return

    _running_lock = True

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(MessageHandler(filters.ALL, message))

    print("bot running (single instance mode)")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()

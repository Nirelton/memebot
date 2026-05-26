from telegram.ext import *
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import json
import os
import random
import time
import re

TOKEN = "8635966932:AAFkbhq9n0o6elo0ml61-s3jQWg1jGCOUIs"
OWNER_ID = 1235534514

DATA_FILE = "data.json"
user_states = {}

default_data = {
    "groups": {},
    "global_triggers": {}
}

# ---------------- LOAD ----------------

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
            "reaction_chance": 50,
            "cooldown": 10,
            "enabled": True,
            "blacklist": [],
            "last_reply": 0,
            "mode": "normal",
            "mode_until": 0
        }
        save_data()


def is_owner(user_id):
    return user_id == OWNER_ID


# ---------------- MODES ----------------

def set_mode(group, mode, seconds):
    group["mode"] = mode
    group["mode_until"] = time.time() + seconds


def update_mode(group):
    if group["mode"] != "normal" and time.time() > group["mode_until"]:
        group["mode"] = "normal"


# ---------------- REACTIONS (PTB 21+) ----------------

async def react(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emojis = ["👍", "😂", "🔥", "💀", "🤡", "👀", "😈"]

    try:
        await context.bot.set_message_reaction(
            chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
            reaction=[random.choice(emojis)]
        )
    except Exception as e:
        print("reaction error:", e)


async def random_react(update, context, group):
    if random.randint(1, 100) < group["reaction_chance"]:
        await react(update, context)


# ---------------- GLOBAL COMMANDS ----------------

async def global_commands(update, context, group):
    text = (update.message.text or "").lower()

    if "заткнись" in text:
        set_mode(group, "mute", 600)
        await update.message.reply_text("ok")
        return True

    if "отвечай минуту" in text:
        set_mode(group, "chaos", 60)
        await update.message.reply_text("ok")
        return True

    return False


# ---------------- MESSAGE CORE ----------------

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_chat.type == "private":
        return

    user_id = update.message.from_user.id
    text = (update.message.text or "").lower()

    chat_id = str(update.effective_chat.id)
    ensure_group(chat_id)
    group = data["groups"][chat_id]

    update_mode(group)

    if not group["enabled"]:
        return

    if user_id in group["blacklist"]:
        return

    # --- reply to bot hack (имитация "реакции на реакцию") ---
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            if "😂" in text or "💀" in text or "🤡" in text:
                await update.message.reply_text("сам ты смешной")
                await react(update, context)
                return

    # --- global commands ---
    if await global_commands(update, context, group):
        return

    if group["mode"] == "mute":
        return

    now = time.time()
    chaos = group["mode"] == "chaos"

    if not chaos and now - group["last_reply"] < group["cooldown"]:
        return

    # ---------------- TRIGGERS ----------------

    for trigger, responses in data["global_triggers"].items():

        if re.search(rf"\b{re.escape(trigger)}\b", text):

            chance = 95 if chaos else group["reply_chance"]

            if random.randint(1, 100) > chance:
                return

            r = random.choice(responses)

            try:
                if r["type"] == "text":
                    await update.message.reply_text(r["content"])
                elif r["type"] == "sticker":
                    await update.message.reply_sticker(r["content"])
                elif r["type"] == "photo":
                    await update.message.reply_photo(r["content"])
                elif r["type"] == "gif":
                    await update.message.reply_animation(r["content"])
                elif r["type"] == "voice":
                    await update.message.reply_voice(r["content"])
            except:
                pass

            group["last_reply"] = now
            save_data()

            await react(update, context)
            return

    # random reaction even without reply
    await random_react(update, context, group)


# ---------------- PANEL (OWNER ONLY) ----------------

async def panel(update, context):
    if update.effective_chat.type != "private":
        return
    if update.message.from_user.id != OWNER_ID:
        return

    keyboard = [
        [InlineKeyboardButton("reply chance", callback_data="chance")],
        [InlineKeyboardButton("reaction chance", callback_data="react")],
        [InlineKeyboardButton("cooldown", callback_data="cd")],
        [InlineKeyboardButton("mode", callback_data="mode")]
    ]

    await update.message.reply_text(
        "control panel",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def panel_cb(update, context):
    q = update.callback_query
    await q.answer()

    chat_id = str(q.message.chat.id)
    ensure_group(chat_id)
    g = data["groups"][chat_id]

    if q.data == "chance":
        await q.edit_message_text(f"reply chance: {g['reply_chance']}%")

    elif q.data == "react":
        await q.edit_message_text(f"reaction chance: {g['reaction_chance']}%")

    elif q.data == "cd":
        await q.edit_message_text(f"cooldown: {g['cooldown']}")

    elif q.data == "mode":
        await q.edit_message_text(
            f"mode: {g['mode']}\n"
            f"time left: {int(max(0, g['mode_until'] - time.time()))} sec"
        )


# ---------------- OWNER COMMANDS ----------------

async def setchance(update, context):
    if update.message.from_user.id != OWNER_ID:
        return

    val = max(0, min(100, int(context.args[0])))
    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)
    data["groups"][chat_id]["reply_chance"] = val
    save_data()

    await update.message.reply_text(f"reply {val}%")


async def setreact(update, context):
    if update.message.from_user.id != OWNER_ID:
        return

    val = max(0, min(100, int(context.args[0])))
    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)
    data["groups"][chat_id]["reaction_chance"] = val
    save_data()

    await update.message.reply_text(f"react {val}%")


async def cooldown(update, context):
    if update.message.from_user.id != OWNER_ID:
        return

    val = max(0, int(context.args[0]))
    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)
    data["groups"][chat_id]["cooldown"] = val
    save_data()

    await update.message.reply_text(f"cooldown {val}")


# ---------------- APP ----------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("setchance", setchance))
app.add_handler(CommandHandler("setreact", setreact))
app.add_handler(CommandHandler("cooldown", cooldown))

app.add_handler(CallbackQueryHandler(panel_cb))
app.add_handler(MessageHandler(filters.ALL, message))

print("bot running")
app.run_polling()

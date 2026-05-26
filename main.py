from telegram.ext import *
from telegram import Update
from telegram.ext import ContextTypes
import json
import os
import random
import time

TOKEN = "8635966932:AAFkbhq9n0o6elo0ml61-s3jQWg1jGCOUIs"
OWNER_ID = 1235534514

DATA_FILE = "data.json"

user_states = {}

default_data = {
    "groups": {}
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
            "cooldown": 10,
            "enabled": True,
            "blacklist": [],
            "triggers": {},
            "last_reply": 0
        }

        save_data()

def is_owner(user_id):
    return user_id == OWNER_ID

async def is_group_admin(update, context):

    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id

    if user_id == OWNER_ID:
        return True

    admins = await context.bot.get_chat_administrators(chat_id)

    for admin in admins:

        if admin.user.id == user_id:
            return True

    return False

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)

    group = data["groups"][chat_id]

    text = f"""
ШАНС ОТВЕТА: {group['reply_chance']}%
COOLDOWN: {group['cooldown']} сек
ВКЛЮЧЕН: {group['enabled']}

ТРИГГЕРЫ:
{list(group['triggers'].keys())}

BLACKLIST:
{group['blacklist']}
"""

    await update.message.reply_text(text)

async def setchance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_group_admin(update, context):
        return

    try:

        chance = int(context.args[0])

        if chance < 0:
            chance = 0

        if chance > 100:
            chance = 100

        chat_id = str(update.effective_chat.id)

        ensure_group(chat_id)

        data["groups"][chat_id]["reply_chance"] = chance

        save_data()

        await update.message.reply_text(
            f"новый шанс ответа: {chance}%"
        )

    except:
        await update.message.reply_text(
            "/setchance 35"
        )

async def cooldown(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_group_admin(update, context):
        return

    try:

        cd = int(context.args[0])

        if cd < 0:
            cd = 0

        chat_id = str(update.effective_chat.id)

        ensure_group(chat_id)

        data["groups"][chat_id]["cooldown"] = cd

        save_data()

        await update.message.reply_text(
            f"cooldown: {cd} сек"
        )

    except:
        await update.message.reply_text(
            "/cooldown 10"
        )

async def blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_group_admin(update, context):
        return

    try:

        user_id = int(context.args[0])

        chat_id = str(update.effective_chat.id)

        ensure_group(chat_id)

        if user_id not in data["groups"][chat_id]["blacklist"]:
            data["groups"][chat_id]["blacklist"].append(user_id)

        save_data()

        await update.message.reply_text(
            "юзер в чс"
        )

    except:
        await update.message.reply_text(
            "/blacklist USER_ID"
        )

async def unblacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_group_admin(update, context):
        return

    try:

        user_id = int(context.args[0])

        chat_id = str(update.effective_chat.id)

        ensure_group(chat_id)

        if user_id in data["groups"][chat_id]["blacklist"]:
            data["groups"][chat_id]["blacklist"].remove(user_id)

        save_data()

        await update.message.reply_text(
            "юзер удалён из чс"
        )

    except:
        await update.message.reply_text(
            "/unblacklist USER_ID"
        )

async def on(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_group_admin(update, context):
        return

    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)

    data["groups"][chat_id]["enabled"] = True

    save_data()

    await update.message.reply_text(
        "бот включён"
    )

async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await is_group_admin(update, context):
        return

    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)

    data["groups"][chat_id]["enabled"] = False

    save_data()

    await update.message.reply_text(
        "бот выключен"
    )

async def addtrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update.message.from_user.id):
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "используй команду в лс бота"
        )
        return

    user_states[update.message.from_user.id] = {
        "step": "waiting_trigger"
    }

    await update.message.reply_text(
        "напиши слово/триггер"
    )

async def deltrigger(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_owner(update.message.from_user.id):
        return

    try:

        trigger = " ".join(context.args).lower()

        removed = 0

        for group_id in data["groups"]:

            if trigger in data["groups"][group_id]["triggers"]:

                del data["groups"][group_id]["triggers"][trigger]

                removed += 1

        save_data()

        await update.message.reply_text(
            f"удалено из {removed} групп"
        )

    except:
        await update.message.reply_text(
            "/deltrigger слово"
        )

async def listtriggers(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)

    triggers = list(
        data["groups"][chat_id]["triggers"].keys()
    )

    if not triggers:
        await update.message.reply_text(
            "триггеров нет"
        )
        return

    text = "\n".join(triggers)

    await update.message.reply_text(text)

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user_id = update.message.from_user.id

    text = update.message.text

    if not text:
        text = ""

    text = text.lower()

    if user_id in user_states:

        state = user_states[user_id]

        if state["step"] == "waiting_trigger":

            state["trigger"] = text
            state["step"] = "waiting_response"

            await update.message.reply_text(
                "отправь ответ:\nтекст/стикер/фото/гиф/гс/кружок"
            )

            return

        elif state["step"] == "waiting_response":

            trigger = state["trigger"]

            group_id = state.get("group_id")

            if not group_id:
                group_id = list(data["groups"].keys())[0]

            ensure_group(group_id)

            if trigger not in data["groups"][group_id]["triggers"]:
                data["groups"][group_id]["triggers"][trigger] = []

            response = None

            if update.message.text:

                response = {
                    "type": "text",
                    "content": update.message.text
                }

            elif update.message.sticker:

                response = {
                    "type": "sticker",
                    "content": update.message.sticker.file_id
                }

            elif update.message.photo:

                response = {
                    "type": "photo",
                    "content": update.message.photo[-1].file_id
                }

            elif update.message.animation:

                response = {
                    "type": "gif",
                    "content": update.message.animation.file_id
                }

            elif update.message.voice:

                response = {
                    "type": "voice",
                    "content": update.message.voice.file_id
                }

            elif update.message.video_note:

                response = {
                    "type": "circle",
                    "content": update.message.video_note.file_id
                }

            if response:

                for group_id in data["groups"]:

                    if trigger not in data["groups"][group_id]["triggers"]:
                        data["groups"][group_id]["triggers"][trigger] = []

                    data["groups"][group_id]["triggers"][trigger].append(response)

                save_data()

                await update.message.reply_text(
                    "триггер сохранён"
                )

            del user_states[user_id]

            return

    if update.effective_chat.type == "private":
        return

    chat_id = str(update.effective_chat.id)

    ensure_group(chat_id)

    group = data["groups"][chat_id]

    if not group["enabled"]:
        return

    if user_id in group["blacklist"]:
        return

    current_time = time.time()

    if current_time - group["last_reply"] < group["cooldown"]:
        return

    for trigger in group["triggers"]:

        if trigger in text:

            chance = random.randint(1, 100)

            if chance > group["reply_chance"]:
                return

            response = random.choice(
                group["triggers"][trigger]
            )

            try:

                if response["type"] == "text":

                    await update.message.reply_text(
                        response["content"]
                    )

                elif response["type"] == "sticker":

                    await update.message.reply_sticker(
                        response["content"]
                    )

                elif response["type"] == "photo":

                    await update.message.reply_photo(
                        response["content"]
                    )

                elif response["type"] == "gif":

                    await update.message.reply_animation(
                        response["content"]
                    )

                elif response["type"] == "voice":

                    await update.message.reply_voice(
                        response["content"]
                    )

                elif response["type"] == "circle":

                    await update.message.reply_video_note(
                        response["content"]
                    )

            except:
                pass

            group["last_reply"] = current_time

            save_data()

            return

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("settings", settings))
app.add_handler(CommandHandler("setchance", setchance))
app.add_handler(CommandHandler("cooldown", cooldown))
app.add_handler(CommandHandler("blacklist", blacklist))
app.add_handler(CommandHandler("unblacklist", unblacklist))
app.add_handler(CommandHandler("on", on))
app.add_handler(CommandHandler("off", off))
app.add_handler(CommandHandler("addtrigger", addtrigger))
app.add_handler(CommandHandler("deltrigger", deltrigger))
app.add_handler(CommandHandler("listtriggers", listtriggers))

app.add_handler(
    MessageHandler(filters.ALL, message)
)

print("бот запущен")

app.run_polling()

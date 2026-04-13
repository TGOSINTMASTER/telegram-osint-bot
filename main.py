import os
import httpx
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)
from telegram.request import HTTPXRequest


# 🚀 ADD THIS GLOBAL CACHE (TOP)
cache = {}

# 🔥 FORCE JOIN CHANNEL
FORCE_CHANNELS = ["@zoraxgc"]

# 🔥 KEEP ALIVE (Render)
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is alive"

def run():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --------------------------- #

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API
API_ADV = "https://yash-code-with-ai.alphamovies.workers.dev/?num={}&key=7189814021"

# ---------- VALIDATION ---------- #
def is_valid_number(num):
    return num.isdigit() and len(num) == 10

# ---------- JOIN CHECK ---------- #
async def is_user_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        for channel in FORCE_CHANNELS:
            member = await context.bot.get_chat_member(channel, user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False

        return True

    except Exception as e:
        print("Join check error:", e)
        return False

# ---------- JOIN BUTTON ---------- #
def join_button():
    keyboard = []

    for channel in FORCE_CHANNELS:
        keyboard.append([
            InlineKeyboardButton(
                f"🚀 Join {channel}",
                url=f"https://t.me/{channel.replace('@','')}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("✅ I Joined", callback_data="check_join")
    ])

    return InlineKeyboardMarkup(keyboard)

# ---------- API CALL (OPTIMIZED - REUSE CLIENT) ---------- #
client = httpx.AsyncClient(timeout=20)

async def fetch_data(number):
    url = API_ADV.format(number)

    try:
        res = await client.get(url)

        if res.status_code != 200:
            return {"error": "API error"}

        data = res.json()

        if not isinstance(data, dict):
            return {"error": "Invalid response"}

        return data

    except Exception as e:
        print("API Error:", e)
        return {"error": "Request failed"}

# ---------- FORMAT RESPONSE ---------- #
def format_response(data):
    # 🔥 Safety check
    if not isinstance(data, dict):
        return "⚠️ Invalid response from API."

    if "error" in data:
        return "⚠️ API is slow or failed. Try again."

    # Convert dict → list
    results = list(data.values())

    if not results:
        return "❌ No records found."

    number = results[0].get("mobile", "N/A")

    msg = f"📱 NUMBER: {number}\n━━━━━━━━━━━━━━\n\n"

    for i, person in enumerate(results, 1):

        # 🔥 Skip invalid entries
        if not isinstance(person, dict):
            continue

        msg += f"🔎 Record {i}\n\n"
        msg += f"👤 Name: {person.get('name', 'N/A')}\n"
        msg += f"👨 Father: {person.get('fname', 'N/A')}\n"
        msg += f"📍 Address: {person.get('address', 'N/A')}\n"
        msg += f"📡 Circle: {person.get('circle', 'N/A')}\n"
        msg += f"📞 Alternate: {person.get('alt', 'N/A')}\n"
        msg += f"📧 Email: {person.get('email', 'N/A')}\n"

        msg += "\n━━━━━━━━━━━━━━\n\n"

    return msg

# ---------- COMMAND: /start ---------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_joined(update, context):
        return await update.message.reply_text(
            "🚫 Access Denied!\n\nJoin our channel to use this bot.",
            reply_markup=join_button()
        )

    await update.message.reply_text(
        "🤖 OSINT Number Lookup Bot\n\nUse:\n/num 9876543210"
    )

# ---------- COMMAND: /num ---------- #
async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not await is_user_joined(update, context):
            return await update.message.reply_text(
                "🚫 Join channel first!",
                reply_markup=join_button()
            )

        if len(context.args) == 0:
            return await update.message.reply_text("❌ Use: /num 9876543210")

        number = context.args[0]

        if not is_valid_number(number):
            return await update.message.reply_text("❌ Invalid number")

        # ⚡ CACHE CHECK (INSTANT RESPONSE)
        if number in cache:
            return await update.message.reply_text(cache[number])

        # ⚡ SINGLE MESSAGE (EDIT LATER)
        msg = await update.message.reply_text("🔍 Fetching...")

        # ⚡ ASYNC CALL (FIXED)
        data = await fetch_data(number)

        result = format_response(data)

        # ⚡ SAVE CACHE
        cache[number] = result

        # ⚡ EDIT MESSAGE (FASTER UX)
        await msg.edit_text(result)

    except Exception as e:
        print("Error:", e)
        await update.message.reply_text("⚠️ Error occurred")

# ---------- CALLBACK ---------- #
async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await is_user_joined(update, context):
        await query.edit_message_text("✅ Verified! Use /num now.")
    else:
        await query.answer("❌ Still not joined!", show_alert=True)

# ---------- MAIN ---------- #
def main():
    keep_alive()

    if not BOT_TOKEN:
        print("❌ BOT TOKEN missing")
        return

    # 🔥 FIX TIMEOUT ISSUE
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num_command))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="check_join"))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

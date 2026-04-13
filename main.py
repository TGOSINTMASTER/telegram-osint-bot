import os
import httpx
from dotenv import load_dotenv

from telegram import ( 
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from telegram.request import HTTPXRequest
from telegram.error import Forbidden

# 🚀 CACHE
cache = {}

# 🔥 YOUR GROUP (without @)
GROUP_USERNAME = "zoraxgc"

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API
API_ADV = "https://yash-code-with-ai.alphamovies.workers.dev/?num={}&key=7189814021"

# ---------- SAFE REPLY ---------- #
async def safe_reply(message, text, reply_markup=None):
    try:
        await message.reply_text(text, reply_markup=reply_markup)
    except Forbidden:
        print("User blocked bot")
    except Exception as e:
        print("Send error:", e)

# ---------- VALIDATION ---------- #
def is_valid_number(num):
    return num.isdigit() and len(num) == 10

# ---------- API CLIENT ---------- #
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
    if not isinstance(data, dict):
        return "⚠️ Invalid response from API."

    if "error" in data:
        return "⚠️ API is slow or failed. Try again."

    results = list(data.values())

    if not results:
        return "❌ No records found."

    number = results[0].get("mobile", "N/A")

    msg = f"📱 NUMBER: {number}\n━━━━━━━━━━━━━━\n\n"

    for i, person in enumerate(results, 1):
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

    # ❌ PRIVATE → REDIRECT TO GROUP
    if update.effective_chat.type == "private":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Open Group", url=f"https://t.me/{GROUP_USERNAME}")]
        ])

        return await safe_reply(
            update.message,
            "⚠️ This bot works only in group.\n\n👉 Click below to use it.",
            reply_markup=keyboard
        )

    await safe_reply(update.message, "✅ Bot is ready. Use /num <number>")

# ---------- COMMAND: /num ---------- #
async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ❌ BLOCK PRIVATE
        if update.effective_chat.type == "private":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Open Group", url=f"https://t.me/{GROUP_USERNAME}")]
            ])

            return await safe_reply(
                update.message,
                "⚠️ Use this bot in group only!",
                reply_markup=keyboard
            )

        if len(context.args) == 0:
            return await safe_reply(update.message, "❌ Use: /num 9876543210")

        number = context.args[0]

        if not is_valid_number(number):
            return await safe_reply(update.message, "❌ Invalid number")

        # ⚡ CACHE
        if number in cache:
            return await safe_reply(update.message, cache[number])

        msg = await update.message.reply_text("🔍 Fetching...")

        data = await fetch_data(number)
        result = format_response(data)

        # ⚠️ LIMIT CACHE
        if len(cache) > 500:
            cache.clear()

        cache[number] = result

        await msg.edit_text(result)

    except Exception as e:
        print("Error:", e)
        await safe_reply(update.message, "⚠️ Error occurred")

# ---------- MAIN ---------- #
def main():
    if not BOT_TOKEN:
        print("❌ BOT TOKEN missing")
        return

    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30
    )

    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num_command))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# 🔥 KEEP ALIVE (Render Fix)
from flask import Flask
from threading import Thread

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is alive"

def run():
    port = int(os.environ.get("PORT", 10000))  # Render uses dynamic PORT
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --------------------------- #

# Load env (for local only)
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API
API_ADV = "https://ft-osint-aih3.onrender.com/api/number?key=demo&num={}"

# ---------- VALIDATION ---------- #
def is_valid_number(num):
    return num.isdigit() and len(num) == 10

# ---------- API CALL ---------- #
def fetch_data(number):
    try:
        url = API_ADV.format(number)
        print("\n🌐 API URL:", url)

        res = requests.get(url, timeout=15)
        print("📡 Status Code:", res.status_code)

        if res.status_code != 200:
            return {"error": "API server error"}

        return res.json()

    except Exception as e:
        print("❌ Exception:", e)
        return {"error": "Request failed"}

# ---------- FORMAT RESPONSE ---------- #
def mask_aadhar(aadhar):
    if aadhar and len(aadhar) >= 8:
        return aadhar[:4] + "****" + aadhar[-2:]
    return aadhar

def format_response(data):
    if not data:
        return "❌ No response from API."

    if isinstance(data, dict) and data.get("status") == "error":
        return f"❌ API Error: {data.get('message', 'Unknown')}"

    if not data.get("success"):
        return "❌ No valid data found."

    number = data.get("number", "N/A")
    results = data.get("results", [])

    msg = f"📱 NUMBER: {number}\n"
    msg += "━━━━━━━━━━━━━━\n\n"

    if not results:
        return msg + "❌ No records found."

    for i, person in enumerate(results, 1):
        msg += f"🔎 Record {i}\n\n"
        msg += f"👤 Name: {person.get('name', 'N/A')}\n"
        msg += f"👨 Father: {person.get('father_name', 'N/A')}\n"
        msg += f"📍 Address: {person.get('address', 'N/A')}\n"
        msg += f"📡 Circle: {person.get('circle', 'N/A')}\n"
        msg += f"📞 Alternate: {person.get('alternate', 'N/A')}\n"
        msg += f"🆔 Aadhaar: {mask_aadhar(person.get('aadhar', 'N/A'))}\n"
        msg += f"📧 Email: {person.get('email', 'N/A')}\n"

        if person.get("truecaller_name"):
            msg += f"📲 Truecaller: {person.get('truecaller_name')}\n"

        msg += "\n━━━━━━━━━━━━━━\n\n"

    return msg

# ---------- COMMAND: /start ---------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 OSINT Number Lookup Bot\n\n"
        "Use command:\n"
        "👉 /num <10-digit-number>\n\n"
        "Example:\n"
        "/num 9876543210"
    )

# ---------- COMMAND: /num ---------- #
async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) == 0:
            return await update.message.reply_text(
                "❌ Usage: /num <10-digit-number>\nExample: /num 9876543210"
            )

        number = context.args[0]

        if not is_valid_number(number):
            return await update.message.reply_text("❌ Enter valid 10-digit number")

        await update.message.reply_text("🔍 Fetching data...")

        data = fetch_data(number)
        result = format_response(data)

        await update.message.reply_text(result)

    except Exception as e:
        print("❌ Error:", e)
        await update.message.reply_text("⚠️ Something went wrong")

# ---------- MAIN ---------- #
def main():
    keep_alive()  # 🔥 VERY IMPORTANT FOR RENDER
    print("BOT TOKEN:", BOT_TOKEN)

    if not BOT_TOKEN:
        print("❌ BOT TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("num", num_command))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

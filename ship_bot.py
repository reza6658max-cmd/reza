# ship_bot_render.py

import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

# ===========================
# تنظیمات ربات
# ===========================
TOKEN = "8118285081:AAEVYk_XQHJDC7tx8sPu1EzRGo9XRwh876k"  # توکن ربات خود را اینجا بگذارید

bot = Bot(token=TOKEN)
app = Flask(__name__)
dp = Dispatcher(bot, None, workers=0, use_context=True)

# ===========================
# فرمان‌ها
# ===========================
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! ربات آماده است.")

dp.add_handler(CommandHandler("start", start))

# ===========================
# مسیر webhook
# ===========================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "OK"

# صفحه اصلی
@app.route("/")
def index():
    return "Bot is running!"

# ===========================
# اجرا
# ===========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # تنظیم webhook روی آدرس Render
    bot.set_webhook(f"https://marin-ship.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=port)


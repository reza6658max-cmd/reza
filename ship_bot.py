from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
import requests
from PIL import Image  # جایگزین imghdr
import io

# --- توکن و تنظیمات ---
TOKEN = '8118285081:AAEVYk_XQHJDC7tx8sPu1EzRGo9XRwh876k'
bot = Bot(token=TOKEN)
updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

# --- تابع تشخیص نوع تصویر ---
def get_image_type(file_path_or_bytes):
    try:
        if isinstance(file_path_or_bytes, bytes):
            img = Image.open(io.BytesIO(file_path_or_bytes))
        else:
            img = Image.open(file_path_or_bytes)
        return img.format  # JPEG, PNG, GIF, ...
    except Exception:
        return None

# --- دستورات ساده ---
def start(update, context):
    update.message.reply_text("سلام! من ربات شما هستم.")

dispatcher.add_handler(CommandHandler("start", start))

# --- نمونه دریافت عکس ---
def photo_handler(update, context):
    file = update.message.photo[-1].get_file()
    file_bytes = file.download_as_bytearray()
    img_type = get_image_type(file_bytes)
    update.message.reply_text(f"نوع عکس: {img_type}")

dispatcher.add_handler(MessageHandler(Filters.photo, photo_handler))

# --- Scheduler نمونه ---
scheduler = BackgroundScheduler()
scheduler.start()

# --- Flask برای webhook (اگر نیاز داری) ---
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    # همزمان هم Bot polling هم Flask (اختیاری)
    updater.start_polling()
    app.run(host="0.0.0.0", port=5000)


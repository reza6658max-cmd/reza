from flask import Flask, request
import telegram
import os

TOKEN = "8118285081:AAEVYk_XQHJDC7tx8sPu1EzRGo9XRwh876k"
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

# Webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    
    chat_id = update.message.chat.id
    text = update.message.text

    if text == "/start":
        bot.send_message(chat_id=chat_id, text="سلام! ربات فعال شد.")
    else:
        bot.send_message(chat_id=chat_id, text=f"پیام شما: {text}")

    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    # تنظیم Webhook در شروع
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



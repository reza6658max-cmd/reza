import logging
import sqlite3
import requests
import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import Updater, CommandHandler

# ====== CONFIG ======
TELEGRAM_TOKEN = "8118285081:AAEVYk_XQHJDC7tx8sPu1EzRGo9XRwh876k"
DB = "ships_bot.db"
USER_AGENT = "ShipBot/1.0 (https://t.me/your_bot_username)"
TIMEZONE = pytz.timezone("Asia/Tehran")  # تغییر بر اساس نیاز

# ====== LOGGING ======
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== DATABASE ======
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        hhmm TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS fetched_ships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        summary TEXT,
        page_url TEXT,
        image_url TEXT,
        fetched_at TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ships_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT UNIQUE
    )""")
    conn.commit()
    conn.close()

# ====== WIKI FETCH ======
def wiki_get_page_extract_and_image(title):
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts|pageimages|info",
        "inprop": "url",
        "exintro": True,
        "explaintext": True,
        "format": "json",
        "pithumbsize": 800
    }
    headers = {"User-Agent": USER_AGENT}
    r = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=headers, timeout=10)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    for _, p in pages.items():
        return p.get("extract", ""), p.get("fullurl", ""), p.get("thumbnail", {}).get("source")
    return None, None, None

# ====== DB OPERATIONS ======
def save_ships_list(titles):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    for t in titles:
        cur.execute("INSERT OR IGNORE INTO ships_list (title) VALUES (?)", (t,))
    conn.commit()
    conn.close()

def populate_ships():
    titles = ["Titanic", "Queen Mary", "Bismarck", "USS Enterprise (CV-6)",
              "HMS Victory", "USS Constitution", "HMS Hood", "Costa Concordia"]
    save_ships_list(titles)
    print(f"✅ Saved {len(titles)} ships into DB")

def get_random_ship():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT title FROM ships_list ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def save_fetched_ship(title, summary, page_url, image_url=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO fetched_ships (title, summary, page_url, image_url, fetched_at)
    VALUES (?, ?, ?, ?, ?)""",
    (title, summary, page_url, image_url, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT chat_id, hhmm FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

def set_user_time(chat_id, hhmm):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO users (chat_id, hhmm) VALUES (?, ?)", (chat_id, hhmm))
    conn.commit()
    conn.close()

def remove_user(chat_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

# ====== BOT HANDLERS ======
def start(update, context):
    chat_id = update.effective_chat.id
    set_user_time(chat_id, None)
    update.message.reply_text(
        "سلام 👋\nبه ربات معرفی کشتی خوش آمدی!\n"
        "با دستور /settime ساعت دلخواهت رو تنظیم کن (مثال: /settime 22:30)\n"
        "برای لغو /stop رو بزن.\n"
        "برای تست سریع /sample رو بزن."
    )

def settime(update, context):
    chat_id = update.effective_chat.id
    if len(context.args) != 1:
        update.message.reply_text("فرمت صحیح: /settime HH:MM (مثلاً /settime 22:30)")
        return
    hhmm = context.args[0]
    try:
        datetime.datetime.strptime(hhmm, "%H:%M")
    except ValueError:
        update.message.reply_text("فرمت اشتباه! باید مثل 07:30 یا 22:30 باشه.")
        return
    set_user_time(chat_id, hhmm)
    update.message.reply_text(f"⏰ زمان شما روی {hhmm} تنظیم شد.")

def stop(update, context):
    remove_user(update.effective_chat.id)
    update.message.reply_text("❌ اشتراک شما لغو شد.")

def sample(update, context):
    chat_id = update.effective_chat.id
    fetch_and_send_ship(chat_id, context)

# ====== FETCH + SEND ======
def fetch_and_send_ship(chat_id, context):
    try:
        title = get_random_ship()
        if not title:
            title = "Titanic"
        summary, page_url, image = wiki_get_page_extract_and_image(title)
        if not summary:
            summary = "خلاصه‌ای در دسترس نیست."
        save_fetched_ship(title, summary, page_url, image_url=image)
        text = f"*{title}*\n\n{summary}\n\n🔗 منبع: {page_url}"
        if image:
            context.bot.send_photo(chat_id=chat_id, photo=image, caption=text, parse_mode="Markdown")
        else:
            context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error sending ship info: %s", e)
        context.bot.send_message(chat_id=chat_id, text="❌ خطا در دریافت اطلاعات کشتی.")

# ====== SCHEDULER ======
scheduler = BackgroundScheduler(timezone=TIMEZONE)

def schedule_jobs(updater):
    scheduler.remove_all_jobs()
    for chat_id, hhmm in get_users():
        if not hhmm:
            continue
        hh, mm = hhmm.split(":")
        scheduler.add_job(fetch_and_send_ship, 'cron', hour=int(hh), minute=int(mm), args=[chat_id, updater])
    if not scheduler.running:
        scheduler.start()

# ====== MAIN ======
def main():
    init_db()
    populate_ships()
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("settime", settime))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("sample", sample))
    schedule_jobs(updater)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


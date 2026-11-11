import os
import re
import asyncio
import tempfile
import threading

from flask import Flask
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

TOKEN = os.environ["BOT_TOKEN"]
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@your_bot")
CHANNEL = "https://t.me/zetsww1"

TIKTOK_RE = re.compile(r"https?://(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/\S+")

# ---- web server صغير ليبقى البوت مستيقظاً (UptimeRobot يزوره) ----
web = Flask(__name__)


@web.route("/")
def home():
    return "Bot is running"


def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


# ---- التحميل ----
def download(url: str, folder: str) -> str:
    opts = {
        "outtmpl": f"{folder}/%(id)s.%(ext)s",
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# ---- الأوامر ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في بوت تحميل التيكتوك 🎬\n"
        "أرسل رابط فيديو تيكتوك وأنا أحمله لك بدون علامة مائية.\n\n"
        "تم تطوير البوت بواسطة Zetsu @ZETSW\n"
        f"قناتنا: {CHANNEL}"
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = TIKTOK_RE.search(text)
    if not match:
        await update.message.reply_text("أرسل رابط تيكتوك صحيح من فضلك 🙏")
        return

    url = match.group(0)
    status = await update.message.reply_text("⏳ جاري التحميل...")

    try:
        with tempfile.TemporaryDirectory() as folder:
            loop = asyncio.get_running_loop()
            path = await loop.run_in_executor(None, download, url, folder)

            if os.path.getsize(path) > 49 * 1024 * 1024:
                await status.edit_text("❌ الفيديو أكبر من 50MB ولا يمكن إرساله.")
                return

            caption = f"📥 تم التحميل عبر {BOT_USERNAME}\n📢 قناتنا: {CHANNEL}"
            with open(path, "rb") as f:
                await update.message.reply_video(video=f, caption=caption)
        await status.delete()
    except Exception:
        await status.edit_text("❌ فشل التحميل. تأكد أن الرابط صحيح والفيديو عام.")


def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()


if __name__ == "__main__":
    main()

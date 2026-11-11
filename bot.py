import os
import re
import threading

import httpx
from flask import Flask
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

web = Flask(__name__)


@web.route("/")
def home():
    return "Bot is running"


def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


async def get_video(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        r = await client.get(
            "https://www.tikwm.com/api/", params={"url": url, "hd": 1}
        )
        data = r.json()
        if data.get("code") != 0:
            raise Exception(data.get("msg", "api error"))
        d = data["data"]
        video_url = d.get("hdplay") or d.get("play")
        if video_url.startswith("/"):
            video_url = "https://www.tikwm.com" + video_url
        v = await client.get(video_url)
        return v.content


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

    status = await update.message.reply_text("⏳ جاري التحميل...")
    try:
        video = await get_video(match.group(0))
        if len(video) > 49 * 1024 * 1024:
            await status.edit_text("❌ الفيديو أكبر من 50MB ولا يمكن إرساله.")
            return
        caption = f"📥 تم التحميل عبر {BOT_USERNAME}\n📢 قناتنا: {CHANNEL}"
        await update.message.reply_video(video=video, caption=caption)
        await status.delete()
    except Exception as e:
        print("ERROR:", e, flush=True)
        await status.edit_text("❌ فشل التحميل. تأكد أن الرابط صحيح والفيديو عام.")


def main():
    threading.Thread(target=run_web, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()


if __name__ == "__main__":
    main()

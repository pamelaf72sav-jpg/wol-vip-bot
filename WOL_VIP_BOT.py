# bot.py
# requirements:
# python-telegram-bot==20.7
# aiohttp
# aiofiles

import re
import os
import time
import logging
import asyncio
import aiohttp
import aiofiles
import tempfile
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")  # ضع التوكن في متغير بيئة
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # اختياري: ضع id الأدمن في متغير بيئة إن أردت

if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set. Please set the BOT_TOKEN environment variable and restart.")
    raise SystemExit("Missing BOT_TOKEN environment variable")

TIKTOK_REGEX = re.compile(
    r"(https?://)?(www\.)?(vm\.tiktok\.com|vt\.tiktok\.com|tiktok\.com)/\S+"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.tiktok.com/",
}

WELCOME = """
╔══════════════════════════╗
👑  مـرحـبـاً بـك فـي  👑
   ✨ WOL VIP BOT ✨
╚══════════════════════════╝

🎬 أقوى بوت لتحميل TikTok
━━━━━━━━━━━━━━━━━━━━━━━
🤖 ذكاء اصطناعي لتحسين الجودة
⚡️ بدون علامة مائية
🎥 جودة فول HD تلقائياً
🚀 سرعة تحميل فائقة
⚡️ مجاناً 100%
━━━━━━━━━━━━━━━━━━━━━━━
📌 فقط أرسل رابط الفيديو
"""

stats: Dict[str, Any] = {"downloads": 0, "users": set()}


async def resolve_short_url(url: str) -> str:
    """حل الروابط المختصرة عبر تتبع التحويلات"""
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url, allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
                headers=HEADERS
            ) as resp:
                return str(resp.url)
    except Exception as e:
        logger.debug("resolve_short_url failed: %s", e)
        return url


async def fetch_video_info(url: str) -> Optional[dict]:
    """جلب معلومات الفيديو من واجهات خارجية (tikwm كمثال)"""
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            apis = [
                f"https://www.tikwm.com/api/?url={url}&hd=1",
                f"https://www.tikwm.com/api/?url={url}",
            ]
            for api in apis:
                try:
                    async with session.get(api, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        # بعض الـ APIs قد يرجع content-type غير صحيح، لذا نستعمل content_type=None
                        data = await resp.json(content_type=None)
                        if isinstance(data, dict) and data.get("code") == 0:
                            return data.get("data")
                except Exception:
                    continue
    except Exception as e:
        logger.debug("fetch_video_info top-level error: %s", e)
    return None


async def fast_download(video_url: str) -> Optional[str]:
    """تحميل سريع باستخدام chunks وكتابة لملف مؤقت، يرجع مسار الملف أو None"""
    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_path = tmp.name
        tmp.close()

        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        timeout = aiohttp.ClientTimeout(total=180, connect=10, sock_read=60)

        async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
            async with session.get(video_url, timeout=timeout) as resp:
                if resp.status != 200:
                    logger.debug("download resp.status != 200: %s", resp.status)
                    return None
                async with aiofiles.open(tmp_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(512 * 1024):
                        await f.write(chunk)

        if os.path.getsize(tmp_path) < 5000:
            os.remove(tmp_path)
            return None
        return tmp_path
    except Exception as e:
        logger.debug("fast_download failed: %s", e)
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        return None


def pick_best_url(info: dict) -> Tuple[Optional[str], str]:
    """اختار أفضل رابط"""
    if info.get("play"):
        return info["play"], "🎥 HD عالية الجودة"
    if info.get("hdplay"):
        return info["hdplay"], "🤖 AI • فول HD 1080p"
    if info.get("wmplay"):
        return info["wmplay"], "📹 جودة عادية"
    return None, "❓"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats["users"].add(update.effective_user.id)
    kb = [
        [InlineKeyboardButton("📥 كيف أحمل؟", callback_data="how"),
         InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🤖 تقنية AI HD", callback_data="ai_info")],
    ]
    await update.message.reply_text(WELCOME, reply_markup=InlineKeyboardMarkup(kb))


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]])

    if q.data == "how":
        await q.edit_message_text(
            "╔══════════════════════════╗\n"
            "📖  طـريـقـة الاسـتـخـدام\n"
            "╚══════════════════════════╝\n\n"
            "1️⃣ افتح TikTok\n"
            "2️⃣ اضغط مشاركة ← نسخ الرابط\n"
            "3️⃣ ألصق الرابط هنا 📨\n"
            "4️⃣ استلم الفيديو فول HD ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 WOL VIP BOT", reply_markup=back_btn
        )
    elif q.data == "ai_info":
        await q.edit_message_text(
            "╔══════════════════════════╗\n"
            "🤖  تـقـنـيـة WOL AI HD\n"
            "╚══════════════════════════╝\n\n"
            "① يحلل الفيديو ويكتشف دقته\n"
            "② يطلب أعلى جودة من الخوادم\n"
            "③ يحمّله بسرعة فائقة 🚀\n"
            "④ يرسله نظيف بدون علامة ✅\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 WOL VIP BOT", reply_markup=back_btn
        )
    elif q.data == "stats":
        await q.edit_message_text(
            "╔══════════════════════════╗\n"
            "📊  إحـصـائـيـات البـوت\n"
            "╚══════════════════════════╝\n\n"
            f"🎬 مقاطع محملة  : {stats['downloads']}\n"
            f"👥 مستخدمين    : {len(stats['users'])}\n"
            f"⚡️ الحالة       : شغّال 24/7 ✅\n"
            f"🕐 التاريخ      : {datetime.now().strftime('%Y-%m-%d')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 WOL VIP BOT", reply_markup=back_btn
        )
    elif q.data == "back":
        kb = [
            [InlineKeyboardButton("📥 كيف أحمل؟", callback_data="how"),
             InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],
            [InlineKeyboardButton("🤖 تقنية AI HD", callback_data="ai_info")],
        ]
        await q.edit_message_text(WELCOME, reply_markup=InlineKeyboardMarkup(kb))


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = update.effective_user
    stats["users"].add(user.id)

    match = TIKTOK_REGEX.search(text)
    if not match:
        await update.message.reply_text(
            "╔══════════════════╗\n"
            "❌  رابط غير صحيح  \n"
            "╚══════════════════╝\n\n"
            "📌 أرسل رابط TikTok صحيح\n"
            "مثال: https://vt.tiktok.com/xxx"
        )
        return

    url = match.group(0)
    if not url.startswith("http"):
        url = "https://" + url

    msg = await update.message.reply_text(
        "╔══════════════════════════╗\n"
        "🤖  WOL AI ENHANCER  👑\n"
        "╚══════════════════════════╝\n\n"
        "🔗 جاري معالجة الرابط..."
    )

    # تحويل الرابط المختصر
    if "vt.tiktok.com" in url or "vm.tiktok.com" in url:
        url = await resolve_short_url(url)

    await msg.edit_text(
        "╔══════════════════════════╗\n"
        "🤖  WOL AI ENHANCER  👑\n"
        "╚══════════════════════════╝\n\n"
        "⚙️ AI يحلل الفيديو ويختار الجودة..."
    )

    info = await fetch_video_info(url)

    if not info:
        await msg.edit_text(
            "╔══════════════════╗\n"
            "❌  فشل التحميل   \n"
            "╚══════════════════╝\n\n"
            "😕 تأكد أن الفيديو عام\n"
            "👑 WOL VIP BOT"
        )
        return

    video_url, quality_label = pick_best_url(info)
    if not video_url:
        await msg.edit_text("❌ تعذر إيجاد رابط التشغيل للفيديو.")
        return

    author = info.get("author", {}).get("nickname", "غير معروف")
    title = info.get("title", "")[:150]
    plays = info.get("play_count", 0)
    likes = info.get("digg_count", 0)
    duration = info.get("duration", 0)

    await msg.edit_text(
        "╔══════════════════════════╗\n"
        "🤖  WOL AI ENHANCER  👑\n"
        "╚══════════════════════════╝\n\n"
        f"🚀 جاري التحميل بسرعة فائقة...\n"
        f"🎯 الجودة: {quality_label}"
    )

    tmp_path = await fast_download(video_url)

    if not tmp_path:
        await msg.edit_text(
            "╔══════════════════╗\n"
            "❌  فشل التحميل   \n"
            "╚══════════════════╝\n\n"
            "😕 الفيديو محمي أو غير متاح\n"
            "👑 WOL VIP BOT"
        )
        return

    caption = (
        "╔══════════════════════════╗\n"
        "✅  تـم التحميل بنجاح!  👑\n"
        "╚══════════════════════════╝\n\n"
        f"🎯 الجودة         : {quality_label}\n"
        f"👤 صاحب الفيديو  : {author}\n"
        f"⏱ المدة           : {duration} ثانية\n"
        f"▶️ المشاهدات       : {plays:,}\n"
        f"❤️ الإعجابات       : {likes:,}\n"
        f"📝 {title}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 WOL AI HD • 👑 VIP BOT ✨"
    )

    try:
        with open(tmp_path, "rb") as vf:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=vf,
                caption=caption,
                supports_streaming=True,
            )
        stats["downloads"] += 1
        await msg.delete()
        if ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"📥 تحميل جديد!\n👤 {user.first_name} | {user.id}\n🎬 {author}\n🎯 {quality_label}"
                )
            except Exception as e:
                logger.debug("notify admin failed: %s", e)
    except Exception as e:
        logger.exception("send_video failed: %s", e)
        await msg.edit_text(
            "╔══════════════════╗\n"
            "⚠️  خطأ في الإرسال \n"
            "╚══════════════════╝\n\n"
            "🔄 حاول مرة ثانية\n"
            "👑 WOL VIP BOT"
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    logger.info("👑 WOL VIP BOT شغّال 24/7 ✅")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

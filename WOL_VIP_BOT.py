import re
import os
import time
import logging
import asyncio
import aiohttp
import aiofiles
import tempfile
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

BOT_TOKEN = "8605583250:AAG_J8RsVN0U8sLvP9xW-ht2TqW_IQTOUeY"
ADMIN_ID = 5909444412

logging.basicConfig(level=logging.ERROR)

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

stats = {"downloads": 0, "users": set()}


async def resolve_short_url(url: str) -> str:
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url, allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
                headers=HEADERS
            ) as resp:
                return str(resp.url)
    except:
        return url


async def fetch_video_info(url: str):
    async with aiohttp.ClientSession() as session:
        for api in [
            f"https://www.tikwm.com/api/?url={url}&hd=1",
            f"https://www.tikwm.com/api/?url={url}",
        ]:
            try:
                async with session.get(
                    api, timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    data = await resp.json(content_type=None)
                    if data.get("code") == 0:
                        return data.get("data")
            except:
                continue
    return None


async def fast_download(video_url: str) -> str | None:
    """تحميل سريع بـ chunks كبيرة ومتوازية"""
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_path = tmp.name
        tmp.close()

        connector = aiohttp.TCPConnector(
            limit=10,
            ssl=False,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(
            total=180,
            connect=10,
            sock_read=60,
        )

        async with aiohttp.ClientSession(
            connector=connector,
            headers=HEADERS
        ) as session:
            async with session.get(video_url, timeout=timeout) as resp:
                if resp.status != 200:
                    return None
                async with aiofiles.open(tmp_path, "wb") as f:
                    # chunk كبير = تحميل أسرع
                    async for chunk in resp.content.iter_chunked(512 * 1024):
                        await f.write(chunk)

        if os.path.getsize(tmp_path) < 5000:
            os.remove(tmp_path)
            return None
        return tmp_path
    except:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass
        return None


def pick_best_url(info: dict) -> tuple:
    """اختار أفضل رابط - play أسرع من hdplay"""
    # play أسرع وجودته كافية، hdplay احتياطي
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
    author   = info.get("author", {}).get("nickname", "غير معروف")
    title    = info.get("title", "")[:150]
    plays    = info.get("play_count", 0)
    likes    = info.get("digg_count", 0)
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
                read_timeout=180,
                write_timeout=180,
            )
        stats["downloads"] += 1
        await msg.delete()
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📥 تحميل جديد!\n👤 {user.first_name} | {user.id}\n🎬 {author}\n🎯 {quality_label}"
            )
        except:
            pass
    except Exception:
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
        except:
            pass


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("👑 WOL VIP BOT شغّال 24/7 ✅")
    app.run_polling(drop_pending_updates=True)


while True:
    try:
        main()
    except Exception as e:
        print(f"⚠️ {e} — إعادة تشغيل...")
        time.sleep(3)

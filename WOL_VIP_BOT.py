import re
import os
import requests
import tempfile
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

BOT_TOKEN = "8701974784:AAECVuKO3ylnFUBcLl-TmHtjGbQxUF1rB-A"
ADMIN_ID = 5909444412

bot = telebot.TeleBot(BOT_TOKEN)

TIKTOK_REGEX = re.compile(
    r"(https?://)?(www\.)?(vm\.tiktok\.com|vt\.tiktok\.com|tiktok\.com)/\S+"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.tiktok.com/",
}

stats = {"downloads": 0, "users": set()}

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
━━━━━━━━━━━━━━━━━━━━━━━
📌 فقط أرسل رابط الفيديو
"""


def main_keyboard():
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("📥 كيف أحمل؟", callback_data="how"),
        InlineKeyboardButton("📊 إحصائيات", callback_data="stats")
    )
    kb.row(InlineKeyboardButton("🤖 تقنية AI HD", callback_data="ai_info"))
    return kb


def back_keyboard():
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("🔙 رجوع", callback_data="back"))
    return kb


def resolve_short_url(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10, headers=HEADERS)
        return r.url
    except:
        return url


def fetch_video_info(url):
    for api in [
        f"https://www.tikwm.com/api/?url={url}&hd=1",
        f"https://www.tikwm.com/api/?url={url}",
    ]:
        try:
            r = requests.get(api, timeout=20)
            data = r.json()
            if data.get("code") == 0:
                return data.get("data")
        except:
            continue
    return None


def download_video(video_url):
    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_path = tmp.name
        tmp.close()
        r = requests.get(video_url, headers=HEADERS, timeout=120, stream=True)
        if r.status_code != 200:
            return None
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=512 * 1024):
                f.write(chunk)
        if os.path.getsize(tmp_path) < 5000:
            os.remove(tmp_path)
            return None
        return tmp_path
    except:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass
        return None


def pick_best_url(info):
    if info.get("play"):
        return info["play"], "🎥 HD عالية الجودة"
    if info.get("hdplay"):
        return info["hdplay"], "🤖 AI • فول HD 1080p"
    if info.get("wmplay"):
        return info["wmplay"], "📹 جودة عادية"
    return None, "❓"


@bot.message_handler(commands=["start"])
def start(message):
    stats["users"].add(message.from_user.id)
    bot.send_message(message.chat.id, WELCOME, reply_markup=main_keyboard())


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "how":
        bot.edit_message_text(
            "╔══════════════════════════╗\n"
            "📖  طـريـقـة الاسـتـخـدام\n"
            "╚══════════════════════════╝\n\n"
            "1️⃣ افتح TikTok\n"
            "2️⃣ اضغط مشاركة ← نسخ الرابط\n"
            "3️⃣ ألصق الرابط هنا 📨\n"
            "4️⃣ استلم الفيديو فول HD ✨\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 WOL VIP BOT",
            call.message.chat.id, call.message.message_id,
            reply_markup=back_keyboard()
        )
    elif call.data == "ai_info":
        bot.edit_message_text(
            "╔══════════════════════════╗\n"
            "🤖  تـقـنـيـة WOL AI HD\n"
            "╚══════════════════════════╝\n\n"
            "① يحلل الفيديو ويكتشف دقته\n"
            "② يطلب أعلى جودة من الخوادم\n"
            "③ يحمّله بسرعة فائقة 🚀\n"
            "④ يرسله نظيف بدون علامة ✅\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 WOL VIP BOT",
            call.message.chat.id, call.message.message_id,
            reply_markup=back_keyboard()
        )
    elif call.data == "stats":
        bot.edit_message_text(
            "╔══════════════════════════╗\n"
            "📊  إحـصـائـيـات البـوت\n"
            "╚══════════════════════════╝\n\n"
            f"🎬 مقاطع محملة  : {stats['downloads']}\n"
            f"👥 مستخدمين    : {len(stats['users'])}\n"
            f"⚡️ الحالة       : شغّال 24/7 ✅\n"
            f"🕐 التاريخ      : {datetime.now().strftime('%Y-%m-%d')}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👑 WOL VIP BOT",
            call.message.chat.id, call.message.message_id,
            reply_markup=back_keyboard()
        )
    elif call.data == "back":
        bot.edit_message_text(
            WELCOME,
            call.message.chat.id, call.message.message_id,
            reply_markup=main_keyboard()
        )


@bot.message_handler(func=lambda m: True)
def handle(message):
    text = message.text.strip()
    stats["users"].add(message.from_user.id)

    match = TIKTOK_REGEX.search(text)
    if not match:
        bot.reply_to(message,
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

    msg = bot.reply_to(message,
        "╔══════════════════════════╗\n"
        "🤖  WOL AI ENHANCER  👑\n"
        "╚══════════════════════════╝\n\n"
        "🔗 جاري معالجة الرابط..."
    )

    if "vt.tiktok.com" in url or "vm.tiktok.com" in url:
        url = resolve_short_url(url)

    bot.edit_message_text(
        "╔══════════════════════════╗\n"
        "🤖  WOL AI ENHANCER  👑\n"
        "╚══════════════════════════╝\n\n"
        "⚙️ AI يحلل الفيديو...",
        message.chat.id, msg.message_id
    )

    info = fetch_video_info(url)
    if not info:
        bot.edit_message_text(
            "╔══════════════════╗\n"
            "❌  فشل التحميل   \n"
            "╚══════════════════╝\n\n"
            "😕 تأكد أن الفيديو عام\n"
            "👑 WOL VIP BOT",
            message.chat.id, msg.message_id
        )
        return

    video_url, quality_label = pick_best_url(info)
    author   = info.get("author", {}).get("nickname", "غير معروف")
    title    = info.get("title", "")[:150]
    plays    = info.get("play_count", 0)
    likes    = info.get("digg_count", 0)
    duration = info.get("duration", 0)

    bot.edit_message_text(
        f"╔══════════════════════════╗\n"
        f"🤖  WOL AI ENHANCER  👑\n"
        f"╚══════════════════════════╝\n\n"
        f"🚀 جاري التحميل...\n"
        f"🎯 الجودة: {quality_label}",
        message.chat.id, msg.message_id
    )

    tmp_path = download_video(video_url)
    if not tmp_path:
        bot.edit_message_text(
            "╔══════════════════╗\n"
            "❌  فشل التحميل   \n"
            "╚══════════════════╝\n\n"
            "😕 الفيديو محمي أو غير متاح\n"
            "👑 WOL VIP BOT",
            message.chat.id, msg.message_id
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
            bot.send_video(message.chat.id, vf, caption=caption, supports_streaming=True)
        stats["downloads"] += 1
        bot.delete_message(message.chat.id, msg.message_id)
        try:
            bot.send_message(ADMIN_ID,
                f"📥 تحميل جديد!\n"
                f"👤 {message.from_user.first_name} | {message.from_user.id}\n"
                f"🎬 {author}\n🎯 {quality_label}"
            )
        except:
            pass
    except:
        bot.edit_message_text(
            "╔══════════════════╗\n"
            "⚠️  خطأ في الإرسال \n"
            "╚══════════════════╝\n\n"
            "🔄 حاول مرة ثانية\n"
            "👑 WOL VIP BOT",
            message.chat.id, msg.message_id
        )
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass


print("👑 WOL VIP BOT شغّال 24/7 ✅")
bot.infinity_polling()

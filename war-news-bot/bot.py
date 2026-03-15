#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════╗
║     🔴 بوت أخبار الحرب - تطوير: عباس الشافعي 🔴     ║
║         نظام ذكاء اصطناعي للتحقق من الأخبار          ║
╚══════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import feedparser
import requests
import json
import re
import html
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from telegram.constants import ParseMode

# ═══════════════════════════════════════
#           ⚙️ الإعدادات الأساسية
# ═══════════════════════════════════════
BOT_TOKEN = ""
ANTHROPIC_API_KEY = "8781378692:AAFeeRwOVk50JDcra4aZhmaHzaH_vbRXr7M"  # ← ضع مفتاح Anthropic هنا
ADMIN_CHAT_ID = 5909444412

# ═══════════════════════════════════════
#        📡 مصادر الأخبار الموثوقة
# ═══════════════════════════════════════
NEWS_SOURCES = {
    "🌍 رويترز عربي": {
        "url": "https://feeds.reuters.com/reuters/arabicTopNews",
        "lang": "ar", "trust": 95, "flag": "🇬🇧"
    },
    "📺 الجزيرة": {
        "url": "https://www.aljazeera.net/xml/rss/all.xml",
        "lang": "ar", "trust": 88, "flag": "🇶🇦"
    },
    "📻 بي بي سي عربي": {
        "url": "http://feeds.bbci.co.uk/arabic/rss.xml",
        "lang": "ar", "trust": 93, "flag": "🇬🇧"
    },
    "📡 العربية": {
        "url": "https://www.alarabiya.net/tools/rss/ar/العربية.xml",
        "lang": "ar", "trust": 82, "flag": "🇸🇦"
    },
    "🌐 أسوشيتد برس": {
        "url": "https://feeds.apnews.com/rss/apf-topnews",
        "lang": "en", "trust": 94, "flag": "🇺🇸"
    },
    "📰 الغارديان": {
        "url": "https://www.theguardian.com/world/iran/rss",
        "lang": "en", "trust": 90, "flag": "🇬🇧"
    },
    "🗞️ فرانس 24 عربي": {
        "url": "https://www.france24.com/ar/rss",
        "lang": "ar", "trust": 87, "flag": "🇫🇷"
    },
    "📢 سكاي نيوز عربية": {
        "url": "https://www.skynewsarabia.com/rss.xml",
        "lang": "ar", "trust": 80, "flag": "🇦🇪"
    },
}

# ═══════════════════════════════════════
#       🔍 كلمات مفتاحية للحرب
# ═══════════════════════════════════════
WAR_KEYWORDS = [
    "إيران", "أمريكا", "إسرائيل", "حرب", "هجوم", "ضربة",
    "صاروخ", "طائرة مسيّرة", "عملية عسكرية", "توتر",
    "تهديد", "مواجهة", "غارة", "انفجار", "اغتيال",
    "نووي", "حرس الثوري", "حزب الله", "الحوثيين",
    "البنتاغون", "تل أبيب", "طهران", "واشنطن",
    "البحر الأحمر", "مضيق هرمز", "غزة", "لبنان",
    "iran", "israel", "america", "usa", "war", "attack",
    "strike", "missile", "drone", "military", "nuclear",
    "irgc", "hezbollah", "houthi", "pentagon", "tehran",
    "netanyahu", "khamenei", "trump", "red sea", "hormuz"
]

# ═══════════════════════════════════════
#         📊 تخزين مؤقت للبيانات
# ═══════════════════════════════════════
news_cache = {}
sent_news_ids = set()
subscribed_users = set()
breaking_subscribers = set()
last_fetch_time = None

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
#                🤖 تحليل بالذكاء الاصطناعي
# ═══════════════════════════════════════════════════════
def analyze_with_ai(title: str, description: str, source: str) -> dict:
    """تحليل الخبر باستخدام Claude API مباشرة"""
    default = {
        "verified": "قيد التحقق",
        "importance": "متوسط",
        "summary_ar": (description[:200] if description else title),
        "alert_level": "🟡",
        "tags": [],
        "countries": [],
        "threat_level": "متوسط"
    }

    if ANTHROPIC_API_KEY == "YOUR_ANTHROPIC_API_KEY_HERE":
        return default

    try:
        prompt = f"""أنت محلل أخبار عسكرية وسياسية محترف.
حلل هذا الخبر وأعد JSON فقط بدون أي نص إضافي:

العنوان: {title}
المصدر: {source}
المحتوى: {description[:400] if description else ''}

أعد هذا JSON بالضبط:
{{
  "verified": "مؤكد" أو "غير مؤكد" أو "قيد التحقق",
  "importance": "عاجل" أو "مهم" أو "متوسط" أو "عادي",
  "summary_ar": "ملخص بالعربية جملة واحدة",
  "alert_level": "🔴" أو "🟠" أو "🟡" أو "🟢",
  "tags": ["وسم1", "وسم2"],
  "countries": ["دولة1", "دولة2"],
  "threat_level": "عالي" أو "متوسط" أو "منخفض"
}}"""

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )

        if response.status_code == 200:
            data = response.json()
            text = data["content"][0]["text"].strip()
            # تنظيف JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)

    except Exception as e:
        logger.error(f"AI Error: {e}")

    return default


# ═══════════════════════════════════════════════════════
#              📡 جلب الأخبار من المصادر
# ═══════════════════════════════════════════════════════
def fetch_all_news() -> list:
    """جلب الأخبار من جميع المصادر"""
    global news_cache, last_fetch_time
    all_news = []

    for source_name, source_info in NEWS_SOURCES.items():
        try:
            headers = {'User-Agent': 'Mozilla/5.0 NewsBot/2.0'}
            feed = feedparser.parse(source_info["url"], request_headers=headers)

            for entry in feed.entries[:8]:
                title = entry.get('title', '')
                desc = re.sub(r'<[^>]+>', '', entry.get('summary', entry.get('description', '')))
                link = entry.get('link', '')

                # فحص ارتباط الخبر بالحرب
                text_check = (title + " " + desc).lower()
                if not any(kw.lower() in text_check for kw in WAR_KEYWORDS):
                    continue

                # استخراج صورة
                image_url = None
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url')
                elif hasattr(entry, 'enclosures') and entry.enclosures:
                    for enc in entry.enclosures:
                        if 'image' in enc.get('type', ''):
                            image_url = enc.get('href', enc.get('url'))
                            break

                news_item = {
                    "id": hash(title[:40] + link[:20]),
                    "title": title,
                    "description": desc[:500],
                    "link": link,
                    "source": source_name,
                    "flag": source_info["flag"],
                    "trust": source_info["trust"],
                    "image_url": image_url,
                    "time": datetime.now().strftime('%H:%M')
                }
                all_news.append(news_item)

        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")

    # إزالة المكرر
    unique_news = []
    seen = set()
    for item in all_news:
        key = item['title'][:40].lower()
        if key not in seen:
            seen.add(key)
            unique_news.append(item)

    news_cache = {item['id']: item for item in unique_news}
    last_fetch_time = datetime.now()
    return unique_news


# ═══════════════════════════════════════════════════════
#              🎨 تنسيق رسائل الأخبار
# ═══════════════════════════════════════════════════════
def format_news(item: dict, ai: dict) -> str:
    """تنسيق الخبر بشكل احترافي"""
    alert = ai.get('alert_level', '🟡')
    importance = ai.get('importance', 'متوسط')
    verified = ai.get('verified', 'قيد التحقق')
    threat = ai.get('threat_level', 'متوسط')
    summary = ai.get('summary_ar', item.get('description', '')[:200])
    tags = " ".join(["#" + t.replace(' ', '_') for t in ai.get('tags', [])[:4]])
    countries = " | ".join(ai.get('countries', [])[:3])

    verify_map = {
        "مؤكد": "✅ مؤكد",
        "غير مؤكد": "❌ غير مؤكد",
        "قيد التحقق": "🔄 قيد التحقق"
    }
    importance_map = {
        "عاجل": "🚨 عاجل جداً",
        "مهم": "⚠️ مهم",
        "متوسط": "📌 متوسط",
        "عادي": "📋 عادي"
    }
    threat_map = {
        "عالي": "🔴 عالي",
        "متوسط": "🟡 متوسط",
        "منخفض": "🟢 منخفض"
    }

    trust = item.get('trust', 0)
    trust_bar = "█" * (trust // 10) + "░" * (10 - trust // 10)

    title_safe = html.escape(item.get('title', ''))
    summary_safe = html.escape(str(summary)[:250])

    msg = f"""{alert}{alert}{alert} <b>━━━━━━━━━━━━━━━━━━━━━━</b>

📰 <b>{title_safe}</b>

<b>━━━━━━━━━━━━━━━━━━━━━━</b>
{verify_map.get(verified, '🔄 قيد التحقق')}
{importance_map.get(importance, '📌 متوسط')}
💢 مستوى التهديد: {threat_map.get(threat, '🟡 متوسط')}

🤖 <b>تحليل AI:</b>
<i>{summary_safe}</i>

{('🌍 <b>الدول:</b> ' + html.escape(countries)) if countries else ''}
{tags}

<b>━━━━━━━━━━━━━━━━━━━━━━</b>
{item.get('flag', '🌍')} <b>المصدر:</b> {html.escape(item.get('source', ''))}
📊 <b>الموثوقية:</b> {trust}% <code>[{trust_bar}]</code>
🕐 <b>الوقت:</b> {item.get('time', '')}

{('<a href="' + item['link'] + '">🔗 اقرأ الخبر كاملاً</a>') if item.get('link') else ''}

<b>━━━━━━━━━━━━━━━━━━━━━━</b>
⚡ <i>تطوير: عباس الشافعي</i> | 🤖 <i>Claude AI</i>"""

    return msg


# ═══════════════════════════════════════════════════════
#              ⌨️ لوحات المفاتيح
# ═══════════════════════════════════════════════════════
def main_keyboard():
    kb = [
        [
            InlineKeyboardButton("📰 آخر الأخبار", callback_data="latest"),
            InlineKeyboardButton("🚨 الأخبار العاجلة", callback_data="breaking")
        ],
        [
            InlineKeyboardButton("🇮🇷 إيران", callback_data="iran"),
            InlineKeyboardButton("🇺🇸 أمريكا", callback_data="usa"),
            InlineKeyboardButton("🇮🇱 إسرائيل", callback_data="israel")
        ],
        [
            InlineKeyboardButton("💥 عمليات عسكرية", callback_data="military"),
            InlineKeyboardButton("☢️ الملف النووي", callback_data="nuclear")
        ],
        [
            InlineKeyboardButton("✅ أخبار مؤكدة", callback_data="verified"),
            InlineKeyboardButton("❓ غير مؤكدة", callback_data="unverified")
        ],
        [
            InlineKeyboardButton("🔔 تفعيل التنبيهات", callback_data="sub"),
            InlineKeyboardButton("🔕 إيقاف التنبيهات", callback_data="unsub")
        ],
        [
            InlineKeyboardButton("📡 المصادر", callback_data="sources"),
            InlineKeyboardButton("📊 إحصائيات", callback_data="stats")
        ],
        [
            InlineKeyboardButton("ℹ️ عن البوت", callback_data="about"),
            InlineKeyboardButton("❓ المساعدة", callback_data="help_menu")
        ]
    ]
    return InlineKeyboardMarkup(kb)


def news_keyboard(news_id: int):
    kb = [
        [
            InlineKeyboardButton("🤖 تحليل AI", callback_data=f"ai_{news_id}"),
            InlineKeyboardButton("🔄 تحديث", callback_data="latest")
        ],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home")]
    ]
    return InlineKeyboardMarkup(kb)


# ═══════════════════════════════════════════════════════
#                  📱 أوامر البوت
# ═══════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)

    msg = f"""🔴🔴🔴 <b>بوت أخبار الحرب</b> 🔴🔴🔴
{'═' * 32}

مرحباً <b>{html.escape(user.first_name)}</b> 👋

🤖 <b>النظام الإخباري الذكي</b>
تغطية شاملة لأخبار الحرب بين:
🇺🇸 أمريكا | 🇮🇷 إيران | 🇮🇱 إسرائيل

{'━' * 30}
📡 <b>المصادر:</b> رويترز، الجزيرة، BBC، العربية، AP، فرانس 24، سكاي نيوز وأكثر

🤖 <b>مميزات AI:</b>
• ✅ التحقق من صحة الأخبار
• 📊 تحليل مستوى التهديد
• 🚨 تنبيهات فورية للعاجل
• 🌍 تغطية عربية وعالمية

{'═' * 32}
👨‍💻 <b>تطوير:</b> عباس الشافعي
🤖 <b>مدعوم بـ:</b> Claude AI
{'═' * 32}

اختر من القائمة 👇"""

    await update.message.reply_html(msg, reply_markup=main_keyboard())


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ جاري جلب الأخبار...")
    await send_news_list(update.message.reply_html, [])


async def cmd_breaking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري البحث عن أخبار عاجلة...")
    news = fetch_all_news()
    found = False
    for item in news[:15]:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        if ai.get('importance') == 'عاجل':
            msg = format_news(item, ai)
            await update.message.reply_html(msg, reply_markup=news_keyboard(item['id']))
            found = True
            await asyncio.sleep(0.5)
    if not found:
        await update.message.reply_html("📭 <b>لا توجد أخبار عاجلة حالياً</b>", reply_markup=main_keyboard())


async def cmd_iran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇮🇷 جاري جلب أخبار إيران...")
    await send_filtered(update.message.reply_html, ["إيران", "iran", "طهران", "خامنئي", "irgc", "حرس الثوري"], "🇮🇷 إيران")


async def cmd_usa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇺🇸 جاري جلب أخبار أمريكا...")
    await send_filtered(update.message.reply_html, ["أمريكا", "america", "usa", "واشنطن", "ترامب", "بايدن", "pentagon"], "🇺🇸 أمريكا")


async def cmd_israel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇮🇱 جاري جلب أخبار إسرائيل...")
    await send_filtered(update.message.reply_html, ["إسرائيل", "israel", "تل أبيب", "نتنياهو", "netanyahu", "غزة"], "🇮🇱 إسرائيل")


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breaking_subscribers.add(update.effective_chat.id)
    await update.message.reply_html(
        "🔔 <b>تم تفعيل التنبيهات العاجلة!</b>\n\n✅ ستصلك الأخبار العاجلة فوراً\n\n/unsubscribe للإيقاف",
        reply_markup=main_keyboard()
    )


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breaking_subscribers.discard(update.effective_chat.id)
    await update.message.reply_html("🔕 <b>تم إيقاف التنبيهات</b>\n\n/subscribe للتفعيل", reply_markup=main_keyboard())


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""📊 <b>إحصائيات البوت</b>
{'━' * 28}
📰 أخبار محفوظة: <b>{len(news_cache)}</b>
👥 المشتركون: <b>{len(breaking_subscribers)}</b>
📡 المصادر النشطة: <b>{len(NEWS_SOURCES)}</b>
🕐 آخر تحديث: <b>{last_fetch_time.strftime('%H:%M - %d/%m/%Y') if last_fetch_time else 'لم يتم بعد'}</b>
{'━' * 28}
⚡ <i>تطوير: عباس الشافعي</i>"""
    await update.message.reply_html(msg, reply_markup=main_keyboard())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """📖 <b>الأوامر المتاحة</b>
{'━' * 28}
/start - القائمة الرئيسية
/news - آخر الأخبار
/breaking - الأخبار العاجلة
/iran - أخبار إيران 🇮🇷
/usa - أخبار أمريكا 🇺🇸
/israel - أخبار إسرائيل 🇮🇱
/subscribe - تفعيل التنبيهات 🔔
/unsubscribe - إيقاف التنبيهات 🔕
/stats - الإحصائيات 📊
/help - المساعدة ❓
{'━' * 28}
⚡ <i>تطوير: عباس الشافعي</i>"""
    await update.message.reply_html(msg, reply_markup=main_keyboard())


# ═══════════════════════════════════════════════════════
#              🔧 دوال مساعدة
# ═══════════════════════════════════════════════════════
async def send_news_list(reply_fn, keywords: list):
    news = fetch_all_news()
    if keywords:
        filtered = [n for n in news if any(k.lower() in (n['title']+n['description']).lower() for k in keywords)]
    else:
        filtered = news

    if not filtered:
        await reply_fn("📭 <b>لا توجد أخبار متاحة حالياً</b>", reply_markup=main_keyboard())
        return

    for item in filtered[:4]:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        msg = format_news(item, ai)
        await reply_fn(msg, reply_markup=news_keyboard(item['id']))
        await asyncio.sleep(0.4)


async def send_filtered(reply_fn, keywords: list, country: str):
    news = fetch_all_news()
    filtered = [n for n in news if any(k.lower() in (n['title']+n['description']).lower() for k in keywords)]

    if not filtered:
        await reply_fn(f"📭 <b>لا توجد أخبار عن {country} حالياً</b>", reply_markup=main_keyboard())
        return

    for item in filtered[:4]:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        msg = format_news(item, ai)
        await reply_fn(msg, reply_markup=news_keyboard(item['id']))
        await asyncio.sleep(0.4)


# ═══════════════════════════════════════════════════════
#           🎯 معالج الأزرار التفاعلية
# ═══════════════════════════════════════════════════════
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat.id

    async def send(msg, kb=None):
        try:
            await context.bot.send_message(
                chat_id, msg,
                parse_mode=ParseMode.HTML,
                reply_markup=kb or main_keyboard()
            )
        except Exception as e:
            logger.error(f"Send error: {e}")

    if data == "home":
        await query.edit_message_text(
            "🏠 <b>القائمة الرئيسية</b>",
            reply_markup=main_keyboard(),
            parse_mode=ParseMode.HTML
        )

    elif data == "latest":
        await query.edit_message_text("⏳ جاري جلب الأخبار...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        if news:
            for item in news[:3]:
                ai = analyze_with_ai(item['title'], item['description'], item['source'])
                await send(format_news(item, ai), news_keyboard(item['id']))
                await asyncio.sleep(0.4)
        else:
            await send("📭 لا توجد أخبار حالياً")

    elif data == "breaking":
        await query.edit_message_text("🔍 جاري البحث...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        found = False
        for item in news[:15]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('importance') in ['عاجل', 'مهم']:
                await send(format_news(item, ai), news_keyboard(item['id']))
                found = True
                await asyncio.sleep(0.4)
                break
        if not found:
            await send("📭 <b>لا توجد أخبار عاجلة حالياً</b>")

    elif data == "iran":
        await query.edit_message_text("🇮🇷 جاري جلب أخبار إيران...", parse_mode=ParseMode.HTML)
        await send_filtered(send, ["إيران", "iran", "طهران", "خامنئي", "irgc"], "🇮🇷 إيران")

    elif data == "usa":
        await query.edit_message_text("🇺🇸 جاري جلب أخبار أمريكا...", parse_mode=ParseMode.HTML)
        await send_filtered(send, ["أمريكا", "america", "usa", "واشنطن", "ترامب"], "🇺🇸 أمريكا")

    elif data == "israel":
        await query.edit_message_text("🇮🇱 جاري جلب أخبار إسرائيل...", parse_mode=ParseMode.HTML)
        await send_filtered(send, ["إسرائيل", "israel", "تل أبيب", "نتنياهو", "غزة"], "🇮🇱 إسرائيل")

    elif data == "military":
        await query.edit_message_text("💥 جاري جلب أخبار العمليات...", parse_mode=ParseMode.HTML)
        await send_filtered(send, ["هجوم", "ضربة", "صاروخ", "مسيّرة", "strike", "missile", "drone", "attack"], "💥 العمليات العسكرية")

    elif data == "nuclear":
        await query.edit_message_text("☢️ جاري جلب الأخبار النووية...", parse_mode=ParseMode.HTML)
        await send_filtered(send, ["نووي", "nuclear", "تخصيب", "uranium", "يورانيوم", "برنامج نووي"], "☢️ الملف النووي")

    elif data == "verified":
        await query.edit_message_text("✅ جاري البحث عن الأخبار المؤكدة...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        found = False
        for item in news[:15]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('verified') == 'مؤكد':
                await send(format_news(item, ai), news_keyboard(item['id']))
                found = True
                await asyncio.sleep(0.4)
        if not found:
            await send("📭 لا توجد أخبار مؤكدة حالياً")

    elif data == "unverified":
        await query.edit_message_text("❓ جاري البحث عن الأخبار غير المؤكدة...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        found = False
        for item in news[:15]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('verified') == 'غير مؤكد':
                await send(format_news(item, ai), news_keyboard(item['id']))
                found = True
                await asyncio.sleep(0.4)
        if not found:
            await send("📭 لا توجد أخبار غير مؤكدة في قاعدة البيانات")

    elif data == "sub":
        breaking_subscribers.add(chat_id)
        await query.edit_message_text(
            "🔔 <b>تم تفعيل التنبيهات!</b>\n\n✅ ستصلك الأخبار العاجلة فوراً",
            reply_markup=main_keyboard(),
            parse_mode=ParseMode.HTML
        )

    elif data == "unsub":
        breaking_subscribers.discard(chat_id)
        await query.edit_message_text(
            "🔕 <b>تم إيقاف التنبيهات</b>",
            reply_markup=main_keyboard(),
            parse_mode=ParseMode.HTML
        )

    elif data == "sources":
        sources_text = "📡 <b>مصادر الأخبار الموثوقة</b>\n" + "━" * 28 + "\n\n"
        for name, info in NEWS_SOURCES.items():
            sources_text += f"{info['flag']} <b>{name}</b>\n"
            sources_text += f"   📊 مستوى الثقة: {info['trust']}%\n"
            sources_text += f"   🌐 اللغة: {'العربية' if info['lang'] == 'ar' else 'الإنجليزية'}\n\n"
        sources_text += "━" * 28 + "\n⚡ <i>تطوير: عباس الشافعي</i>"
        await query.edit_message_text(sources_text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "stats":
        stats = f"""📊 <b>إحصائيات البوت</b>
{'━' * 28}
📰 أخبار محفوظة: <b>{len(news_cache)}</b>
👥 المشتركون: <b>{len(breaking_subscribers)}</b>
📡 المصادر: <b>{len(NEWS_SOURCES)}</b>
🕐 آخر تحديث: <b>{last_fetch_time.strftime('%H:%M') if last_fetch_time else 'لم يتم'}</b>
{'━' * 28}
⚡ <i>تطوير: عباس الشافعي</i>"""
        await query.edit_message_text(stats, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "about":
        about = """🤖 <b>عن بوت أخبار الحرب</b>
{'═' * 30}

🎯 <b>الهدف:</b>
تغطية إخبارية ذكية لأخبار الحرب بين أمريكا وإسرائيل وإيران

📡 <b>المصادر:</b>
8 مصادر عالمية وعربية موثوقة

🤖 <b>الذكاء الاصطناعي:</b>
• التحقق من صحة الأخبار
• تحليل مستوى التهديد
• تلخيص الأخبار بالعربية
• تنبيهات الأخبار العاجلة

{'━' * 30}
👨‍💻 <b>تطوير:</b> عباس الشافعي
🤖 <b>AI:</b> Claude (Anthropic)
📅 <b>الإصدار:</b> 2.0 Pro
{'═' * 30}"""
        await query.edit_message_text(about, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "help_menu":
        help_text = """❓ <b>المساعدة</b>
{'━' * 28}
الأوامر المتاحة:
/start - القائمة الرئيسية
/news - آخر الأخبار
/breaking - الأخبار العاجلة
/iran | /usa | /israel - أخبار حسب الدولة
/subscribe - تفعيل التنبيهات
/unsubscribe - إيقاف التنبيهات
/stats - الإحصائيات

مستويات التحقق:
✅ مؤكد | ❌ غير مؤكد | 🔄 قيد التحقق

مستويات الأهمية:
🚨 عاجل | ⚠️ مهم | 📌 متوسط | 📋 عادي
{'━' * 28}
⚡ <i>تطوير: عباس الشافعي</i>"""
        await query.edit_message_text(help_text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data.startswith("ai_"):
        news_id = int(data[3:])
        if news_id in news_cache:
            item = news_cache[news_id]
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            analysis = f"""🤖 <b>تحليل الذكاء الاصطناعي</b>
{'═' * 30}

📰 <b>{html.escape(item['title'][:100])}</b>

{'━' * 28}
🔍 <b>التحقق:</b> {ai.get('verified', 'غير محدد')}
⚠️ <b>الأهمية:</b> {ai.get('importance', 'متوسط')}
💢 <b>التهديد:</b> {ai.get('threat_level', 'متوسط')}
{ai.get('alert_level', '🟡')} <b>مستوى التنبيه</b>

📝 <b>الملخص:</b>
<i>{html.escape(str(ai.get('summary_ar', ''))[:300])}</i>

🌍 <b>الدول:</b> {html.escape(', '.join(ai.get('countries', [])))}
🏷️ <b>الوسوم:</b> {' '.join(['#' + t for t in ai.get('tags', [])])}
{'═' * 30}
⚡ <i>Claude AI Analysis | عباس الشافعي</i>"""

            await send(analysis)


# ═══════════════════════════════════════════════════════
#           ⏰ مهمة دورية للتنبيهات العاجلة
# ═══════════════════════════════════════════════════════
async def auto_alerts(context: ContextTypes.DEFAULT_TYPE):
    """فحص الأخبار العاجلة كل 15 دقيقة وإرسال تنبيهات"""
    if not breaking_subscribers:
        return

    try:
        news = fetch_all_news()
        for item in news:
            if item['id'] in sent_news_ids:
                continue
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('importance') == 'عاجل':
                sent_news_ids.add(item['id'])
                msg = "🚨🚨 <b>تنبيه عاجل!</b> 🚨🚨\n\n" + format_news(item, ai)

                for chat_id in list(breaking_subscribers):
                    try:
                        await context.bot.send_message(
                            chat_id, msg,
                            parse_mode=ParseMode.HTML,
                            reply_markup=main_keyboard()
                        )
                        await asyncio.sleep(0.1)
                    except Exception:
                        breaking_subscribers.discard(chat_id)
    except Exception as e:
        logger.error(f"Auto alerts error: {e}")


# ═══════════════════════════════════════════════════════
#                   🚀 تشغيل البوت
# ═══════════════════════════════════════════════════════
def main():
    print("""
╔══════════════════════════════════════════════════╗
║  🔴  بوت أخبار الحرب - يبدأ التشغيل  🔴       ║
║       👨‍💻 تطوير: عباس الشافعي                   ║
║       🤖 بدعم: Claude AI (Anthropic)             ║
╚══════════════════════════════════════════════════╝
    """)

    app = Application.builder().token(BOT_TOKEN).build()

    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("breaking", cmd_breaking))
    app.add_handler(CommandHandler("iran", cmd_iran))
    app.add_handler(CommandHandler("usa", cmd_usa))
    app.add_handler(CommandHandler("israel", cmd_israel))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("help", cmd_help))

    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))

    # مهمة تلقائية كل 15 دقيقة
    app.job_queue.run_repeating(auto_alerts, interval=900, first=120)

    print("✅ البوت يعمل الآن! اضغط Ctrl+C للإيقاف\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

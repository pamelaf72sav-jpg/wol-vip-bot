#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║   🔴💥 بوت أخبار الحرب PRO - تطوير: عباس الشافعي 💥🔴    ║
║     نظام ذكاء اصطناعي متقدم | فيديوهات | أخبار لحظية       ║
║              الإصدار 3.0 ULTRA PRO                          ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import feedparser
import requests
import json
import re
import html
import hashlib
from datetime import datetime, timedelta
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaVideo, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

# ═══════════════════════════════════════
#           ⚙️ الإعدادات الأساسية
# ═══════════════════════════════════════
BOT_TOKEN = "8781378692:AAFeeRwOVk50JDcra4aZhmaHzaH_vbRXr7M"
ANTHROPIC_API_KEY = ""  # ← ضع مفتاح Anthropic هنا
ADMIN_CHAT_ID = 5909444412

# ═══════════════════════════════════════════════════════════
#        📡 مصادر الأخبار الموثوقة - 20 مصدر عالمي
# ═══════════════════════════════════════════════════════════
NEWS_SOURCES = {
    # عربية
    "🌍 رويترز عربي":    {"url": "https://feeds.reuters.com/reuters/arabicTopNews", "lang": "ar", "trust": 95, "flag": "🇬🇧"},
    "📺 الجزيرة":        {"url": "https://www.aljazeera.net/xml/rss/all.xml", "lang": "ar", "trust": 88, "flag": "🇶🇦"},
    "📻 بي بي سي عربي":  {"url": "http://feeds.bbci.co.uk/arabic/rss.xml", "lang": "ar", "trust": 93, "flag": "🇬🇧"},
    "📡 العربية":        {"url": "https://www.alarabiya.net/tools/rss/ar/العربية.xml", "lang": "ar", "trust": 82, "flag": "🇸🇦"},
    "🗞️ فرانس 24":      {"url": "https://www.france24.com/ar/rss", "lang": "ar", "trust": 87, "flag": "🇫🇷"},
    "📢 سكاي نيوز":      {"url": "https://www.skynewsarabia.com/rss.xml", "lang": "ar", "trust": 80, "flag": "🇦🇪"},
    "🎙️ RT عربي":       {"url": "https://arabic.rt.com/rss/", "lang": "ar", "trust": 75, "flag": "🇷🇺"},
    "📰 اندبندنت عربي":  {"url": "https://www.independentarabia.com/feeds/rss", "lang": "ar", "trust": 83, "flag": "🇬🇧"},
    # عالمية
    "🌐 أسوشيتد برس":    {"url": "https://feeds.apnews.com/rss/apf-topnews", "lang": "en", "trust": 94, "flag": "🇺🇸"},
    "📰 الغارديان":      {"url": "https://www.theguardian.com/world/iran/rss", "lang": "en", "trust": 90, "flag": "🇬🇧"},
    "🗺️ BBC World":     {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "lang": "en", "trust": 93, "flag": "🇬🇧"},
    "📊 Reuters World":  {"url": "https://feeds.reuters.com/reuters/worldNews", "lang": "en", "trust": 95, "flag": "🇬🇧"},
    "🇺🇸 CNN":           {"url": "http://rss.cnn.com/rss/edition_world.rss", "lang": "en", "trust": 85, "flag": "🇺🇸"},
    "📡 Al Jazeera EN":  {"url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en", "trust": 88, "flag": "🇶🇦"},
    "🗞️ Times of Israel":{"url": "https://www.timesofisrael.com/feed/", "lang": "en", "trust": 82, "flag": "🇮🇱"},
    "⚡ Middle East Eye": {"url": "https://www.middleeasteye.net/rss", "lang": "en", "trust": 80, "flag": "🌍"},
    "🎯 Jerusalem Post":  {"url": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx", "lang": "en", "trust": 80, "flag": "🇮🇱"},
    "🏛️ Defense News":   {"url": "https://www.defensenews.com/arc/outboundfeeds/rss/", "lang": "en", "trust": 88, "flag": "🇺🇸"},
    "⚔️ Military Times":  {"url": "https://www.militarytimes.com/arc/outboundfeeds/rss/", "lang": "en", "trust": 85, "flag": "🇺🇸"},
    "🌏 PRESS TV":        {"url": "https://www.presstv.ir/rss.xml", "lang": "en", "trust": 70, "flag": "🇮🇷"},
}

# ═══════════════════════════════════════════════════════════
#    📹 مصادر فيديوهات الهجمات والأخبار العسكرية
# ═══════════════════════════════════════════════════════════
VIDEO_SOURCES = {
    "LiveUA Map": "https://liveuamap.com/",
    "ISW": "https://understandingwar.org/",
    "Telegram Channels": [
        "https://t.me/s/iraninternational_fa",
        "https://t.me/s/MEE_Arabic",
        "https://t.me/s/AlMayadeenLive",
    ]
}

# كلمات مفتاحية الحرب
WAR_KEYWORDS = [
    "إيران", "أمريكا", "إسرائيل", "حرب", "هجوم", "ضربة", "صاروخ",
    "طائرة مسيّرة", "عملية عسكرية", "توتر", "تهديد", "غارة", "انفجار",
    "اغتيال", "نووي", "حرس الثوري", "حزب الله", "الحوثيين", "البنتاغون",
    "تل أبيب", "طهران", "واشنطن", "البحر الأحمر", "مضيق هرمز", "غزة",
    "لبنان", "سوريا", "العراق", "اليمن", "قصف", "مدفعية", "دبابة",
    "iran", "israel", "america", "usa", "war", "attack", "strike",
    "missile", "drone", "military", "nuclear", "irgc", "hezbollah",
    "houthi", "pentagon", "tehran", "netanyahu", "khamenei", "trump",
    "red sea", "hormuz", "explosion", "bombing", "airstrike", "killed",
    "assassination", "conflict", "troops", "invasion", "offensive"
]

# ═══════════════════════════════════════════════════════════
#              💾 تخزين البيانات
# ═══════════════════════════════════════════════════════════
news_cache = {}
sent_news_ids = set()
subscribed_users = set()
breaking_subscribers = set()
video_subscribers = set()
last_fetch_time = None
stats = {"total_news": 0, "breaking_sent": 0, "users": 0}

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#           🌐 الترجمة التلقائية إلى العربية
# ═══════════════════════════════════════════════════════════
def translate_to_arabic(text: str, title: bool = False) -> str:
    """ترجمة النص إلى العربية باستخدام نظام ذكاء اصطناعي أو قاموس مدمج"""
    if not text or not text.strip():
        return text
    
    # فحص إذا النص عربي أصلاً
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    if arabic_chars > len(text) * 0.3:
        return text  # النص عربي بالفعل
    
    # محاولة الترجمة بـ نظام ذكاء اصطناعي
    if ANTHROPIC_API_KEY:
        try:
            prompt = f"""ترجم هذا النص إلى العربية الفصحى بدقة. أعد الترجمة فقط بدون أي شرح:

{text[:500]}"""
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Translation error: {e}")
    
    # قاموس ترجمة مدمج للكلمات الشائعة
    translations = {
        "attack": "هجوم", "strike": "ضربة", "missile": "صاروخ",
        "drone": "طائرة مسيّرة", "explosion": "انفجار", "killed": "قتيل",
        "war": "حرب", "military": "عسكري", "operation": "عملية",
        "iran": "إيران", "israel": "إسرائيل", "america": "أمريكا",
        "usa": "الولايات المتحدة", "nuclear": "نووي", "threat": "تهديد",
        "tension": "توتر", "conflict": "نزاع", "troops": "قوات",
        "invasion": "غزو", "bombing": "قصف", "airstrike": "غارة جوية",
        "assassination": "اغتيال", "dead": "قتيل", "wounded": "جريح",
        "forces": "قوات", "army": "جيش", "navy": "بحرية",
        "airforce": "قوات جوية", "pentagon": "البنتاغون",
        "white house": "البيت الأبيض", "congress": "الكونغرس",
        "president": "الرئيس", "prime minister": "رئيس الوزراء",
        "minister": "وزير", "general": "جنرال", "commander": "قائد",
        "red sea": "البحر الأحمر", "hormuz": "هرمز", "gulf": "الخليج",
        "tehran": "طهران", "tel aviv": "تل أبيب", "washington": "واشنطن",
        "netanyahu": "نتنياهو", "khamenei": "خامنئي", "trump": "ترامب",
        "biden": "بايدن", "irgc": "الحرس الثوري", "hezbollah": "حزب الله",
        "houthi": "الحوثيين", "hamas": "حماس", "idf": "الجيش الإسرائيلي",
        "ceasefire": "وقف إطلاق النار", "peace": "سلام", "deal": "صفقة",
        "sanctions": "عقوبات", "oil": "نفط", "gas": "غاز",
        "ballistic": "باليستي", "cruise": "كروز", "warship": "سفينة حربية",
        "fighter jet": "مقاتلة", "tank": "دبابة", "soldiers": "جنود",
        "casualties": "ضحايا", "civilians": "مدنيون", "hospital": "مستشفى",
        "reports": "تقارير", "according to": "وفقاً لـ", "sources": "مصادر",
        "confirmed": "مؤكد", "unconfirmed": "غير مؤكد", "breaking": "عاجل",
        "exclusive": "حصري", "urgent": "عاجل", "developing": "متطور",
        "latest": "أحدث", "update": "تحديث", "news": "أخبار",
    }
    
    result = text
    text_lower = text.lower()
    for en, ar in translations.items():
        if en in text_lower:
            result = re.sub(re.escape(en), ar, result, flags=re.IGNORECASE)
    
    return result


def translate_news_item(item: dict) -> dict:
    """ترجمة عنوان ووصف الخبر إلى العربية"""
    translated = item.copy()
    
    # ترجمة العنوان إذا كان إنجليزياً
    arabic_in_title = sum(1 for c in item.get('title', '') if '\u0600' <= c <= '\u06FF')
    if arabic_in_title < len(item.get('title', '')) * 0.3:
        translated['title_ar'] = translate_to_arabic(item.get('title', ''), title=True)
        translated['title_original'] = item.get('title', '')
    else:
        translated['title_ar'] = item.get('title', '')
        translated['title_original'] = item.get('title', '')
    
    # ترجمة الوصف
    arabic_in_desc = sum(1 for c in item.get('description', '') if '\u0600' <= c <= '\u06FF')
    if arabic_in_desc < len(item.get('description', '')) * 0.3:
        translated['description_ar'] = translate_to_arabic(item.get('description', ''))
    else:
        translated['description_ar'] = item.get('description', '')
    
    return translated


# ═══════════════════════════════════════════════════════════
#           🤖 تحليل بالذكاء الاصطناعي
# ═══════════════════════════════════════════════════════════
def analyze_with_ai(title: str, description: str, source: str) -> dict:
    default = {
        "verified": "قيد التحقق", "importance": "متوسط",
        "summary_ar": description[:200] if description else title,
        "alert_level": "🟡", "tags": [], "countries": [],
        "threat_level": "متوسط", "has_video": False,
        "video_keywords": []
    }
    if not ANTHROPIC_API_KEY:
        # تحليل بسيط بدون AI
        text = (title + " " + description).lower()
        if any(w in text for w in ["انفجار", "ضربة", "هجوم", "قصف", "explosion", "strike", "attack", "bombing"]):
            default["importance"] = "عاجل"
            default["alert_level"] = "🔴"
            default["threat_level"] = "عالي"
        elif any(w in text for w in ["تهديد", "توتر", "threat", "tension", "warning"]):
            default["importance"] = "مهم"
            default["alert_level"] = "🟠"
        return default

    try:
        prompt = f"""أنت محلل أخبار عسكري وسياسي متخصص.
حلل هذا الخبر وأعد JSON فقط بدون أي نص:

العنوان: {title}
المصدر: {source}
المحتوى: {description[:400] if description else ''}

أعد هذا JSON بالضبط:
{{
  "verified": "مؤكد" أو "غير مؤكد" أو "قيد التحقق",
  "importance": "عاجل" أو "مهم" أو "متوسط" أو "عادي",
  "summary_ar": "ملخص بالعربية جملة واحدة",
  "alert_level": "🔴" أو "🟠" أو "🟡" أو "🟢",
  "tags": ["وسم1", "وسم2", "وسم3"],
  "countries": ["دولة1", "دولة2"],
  "threat_level": "عالي" أو "متوسط" أو "منخفض",
  "has_video": true أو false,
  "video_keywords": ["كلمة1", "كلمة2"]
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
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )
        if response.status_code == 200:
            text = response.json()["content"][0]["text"].strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
    except Exception as e:
        logger.error(f"AI Error: {e}")
    return default


# ═══════════════════════════════════════════════════════════
#         📹 البحث عن فيديوهات الهجمات
# ═══════════════════════════════════════════════════════════
def search_attack_videos(keywords: list) -> list:
    """البحث عن فيديوهات الهجمات من مصادر موثوقة"""
    videos = []
    
    # مصادر فيديو موثوقة مع روابط مباشرة
    video_news_sources = [
        {
            "url": "https://feeds.reuters.com/reuters/video",
            "name": "Reuters Video",
            "flag": "🎥"
        },
        {
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "name": "Al Jazeera Video",
            "flag": "📹"
        },
    ]
    
    for source in video_news_sources:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:5]:
                title = entry.get('title', '')
                text = title.lower()
                if any(kw.lower() in text for kw in keywords):
                    # استخراج رابط الفيديو
                    video_url = None
                    if hasattr(entry, 'media_content'):
                        for media in entry.media_content:
                            if 'video' in media.get('type', ''):
                                video_url = media.get('url')
                                break
                    
                    videos.append({
                        "title": title,
                        "url": entry.get('link', ''),
                        "video_url": video_url,
                        "source": source["name"],
                        "flag": source["flag"]
                    })
        except:
            pass
    
    return videos[:3]


# ═══════════════════════════════════════════════════════════
#              📡 جلب الأخبار
# ═══════════════════════════════════════════════════════════
def fetch_all_news(force=False) -> list:
    global news_cache, last_fetch_time

    all_news = []
    headers = {'User-Agent': 'Mozilla/5.0 WarNewsBot/3.0'}

    for source_name, source_info in NEWS_SOURCES.items():
        try:
            feed = feedparser.parse(source_info["url"], request_headers=headers)
            for entry in feed.entries[:8]:
                title = entry.get('title', '')
                desc = re.sub(r'<[^>]+>', '', entry.get('summary', entry.get('description', '')))
                link = entry.get('link', '')
                
                text_check = (title + " " + desc).lower()
                if not any(kw.lower() in text_check for kw in WAR_KEYWORDS):
                    continue

                # استخراج صورة
                image_url = None
                video_url = None
                
                if hasattr(entry, 'media_content') and entry.media_content:
                    for media in entry.media_content:
                        mtype = media.get('type', '')
                        if 'video' in mtype:
                            video_url = media.get('url')
                        elif 'image' in mtype and not image_url:
                            image_url = media.get('url')
                
                if not image_url and hasattr(entry, 'enclosures') and entry.enclosures:
                    for enc in entry.enclosures:
                        t = enc.get('type', '')
                        if 'image' in t:
                            image_url = enc.get('href', enc.get('url'))
                        elif 'video' in t:
                            video_url = enc.get('href', enc.get('url'))

                # تحديد هل الخبر عاجل بناءً على الكلمات
                is_urgent = any(w in text_check for w in [
                    "انفجار", "ضربة", "هجوم عسكري", "اغتيال", "قصف",
                    "explosion", "airstrike", "assassination", "attack", "strike now"
                ])

                news_item = {
                    "id": int(hashlib.md5((title[:30] + link[:20]).encode()).hexdigest()[:8], 16),
                    "title": title,
                    "description": desc[:600],
                    "link": link,
                    "source": source_name,
                    "flag": source_info["flag"],
                    "trust": source_info["trust"],
                    "image_url": image_url,
                    "video_url": video_url,
                    "is_urgent": is_urgent,
                    "time": datetime.now().strftime('%H:%M'),
                    "date": datetime.now().strftime('%d/%m/%Y'),
                }
                all_news.append(news_item)
        except Exception as e:
            logger.error(f"Error {source_name}: {e}")

    # إزالة المكرر
    unique_news = []
    seen = set()
    for item in all_news:
        key = item['title'][:35].lower()
        if key not in seen:
            seen.add(key)
            unique_news.append(item)

    # ترتيب - العاجل أولاً
    unique_news.sort(key=lambda x: x.get('is_urgent', False), reverse=True)
    
    news_cache = {item['id']: item for item in unique_news}
    last_fetch_time = datetime.now()
    stats["total_news"] = len(unique_news)
    
    return unique_news


# ═══════════════════════════════════════════════════════════
#              🎨 تنسيق الرسائل
# ═══════════════════════════════════════════════════════════
def format_news(item: dict, ai: dict, index: int = 0, total: int = 0) -> str:
    # ترجمة الخبر للعربية
    item = translate_news_item(item)
    
    alert = ai.get('alert_level', '🟡')
    importance = ai.get('importance', 'متوسط')
    verified = ai.get('verified', 'قيد التحقق')
    threat = ai.get('threat_level', 'متوسط')
    summary = ai.get('summary_ar', item.get('description_ar', item.get('description', ''))[:200])
    tags = " ".join(["#" + t.replace(' ', '_') for t in ai.get('tags', [])[:4]])
    countries = " | ".join(ai.get('countries', [])[:3])

    verify_icons = {"مؤكد": "✅ مؤكد", "غير مؤكد": "❌ غير مؤكد", "قيد التحقق": "🔄 قيد التحقق"}
    importance_icons = {"عاجل": "🚨 عاجل جداً", "مهم": "⚠️ مهم", "متوسط": "📌 متوسط", "عادي": "📋 عادي"}
    threat_icons = {"عالي": "🔴 خطر عالي", "متوسط": "🟡 متوسط", "منخفض": "🟢 منخفض"}

    trust = item.get('trust', 0)
    trust_bar = "█" * (trust // 10) + "░" * (10 - trust // 10)
    has_video = "📹 يحتوي على فيديو" if item.get('video_url') else ""
    counter = f"📊 {index}/{total}" if total > 0 else ""
    
    # العنوان المترجم
    title_ar = html.escape(item.get('title_ar', item.get('title', '')))
    title_orig = item.get('title_original', '')
    # إظهار الأصل إذا كان إنجليزي
    orig_line = f"\n🔤 <i>{html.escape(title_orig[:100])}</i>" if title_orig and title_orig != item.get('title_ar','') else ""

    msg = f"""{alert}{alert} <b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b> {alert}{alert}

💥 <b>{title_ar}</b>{orig_line}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
{verify_icons.get(verified, '🔄 قيد التحقق')}
{importance_icons.get(importance, '📌 متوسط')}
💢 {threat_icons.get(threat, '🟡 متوسط')}
{has_video}

🤖 <b>تحليل AI بالعربية:</b>
<i>{html.escape(str(summary)[:280])}</i>

{('🌍 <b>الدول:</b> ' + html.escape(countries)) if countries else ''}
{tags}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
{item.get('flag', '🌍')} <b>المصدر:</b> {html.escape(item.get('source', ''))}
📊 <b>الموثوقية:</b> {trust}% <code>[{trust_bar}]</code>
🕐 <b>الوقت:</b> {item.get('time', '')} | {item.get('date', '')}
{counter}

{('<a href="' + item['link'] + '">🔗 اقرأ الخبر كاملاً</a>') if item.get('link') else ''}

<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
👑 <b>عباس الشافعي</b> | ⚡ <i>المطور الأول للأخبار</i>"""

    return msg


def format_breaking(item: dict) -> str:
    """تنسيق الأخبار العاجلة"""
    return f"""🚨🚨🚨 <b>⚡ خبر عاجل الآن ⚡</b> 🚨🚨🚨
{'═' * 30}

💥 <b>{html.escape(item.get('title', ''))}</b>

{'═' * 30}
{item.get('flag', '🌍')} <b>المصدر:</b> {html.escape(item.get('source', ''))}
🕐 <b>الوقت:</b> {item.get('time', '')}

{('<a href="' + item['link'] + '">🔗 اقرأ التفاصيل الآن</a>') if item.get('link') else ''}

{'═' * 30}
👑 <b>عباس الشافعي</b> | ⚡ <i>المطور الأول للأخبار</i>"""


# ═══════════════════════════════════════════════════════════
#              ⌨️ لوحات المفاتيح
# ═══════════════════════════════════════════════════════════
def main_keyboard():
    kb = [
        [
            InlineKeyboardButton("📰 آخر الأخبار", callback_data="latest"),
            InlineKeyboardButton("🚨 عاجل الآن", callback_data="breaking")
        ],
        [
            InlineKeyboardButton("🇮🇷 إيران", callback_data="iran"),
            InlineKeyboardButton("🇺🇸 أمريكا", callback_data="usa"),
            InlineKeyboardButton("🇮🇱 إسرائيل", callback_data="israel")
        ],
        [
            InlineKeyboardButton("📹 فيديوهات الهجمات", callback_data="videos"),
            InlineKeyboardButton("💥 عمليات عسكرية", callback_data="military")
        ],
        [
            InlineKeyboardButton("☢️ الملف النووي", callback_data="nuclear"),
            InlineKeyboardButton("🚀 صواريخ ومسيّرات", callback_data="missiles")
        ],
        [
            InlineKeyboardButton("🔴 أخبار اليوم فقط", callback_data="today"),
            InlineKeyboardButton("⚡ أقوى الأخبار", callback_data="top_news")
        ],
        [
            InlineKeyboardButton("✅ مؤكدة", callback_data="verified"),
            InlineKeyboardButton("❓ غير مؤكدة", callback_data="unverified"),
            InlineKeyboardButton("🔄 قيد التحقق", callback_data="pending")
        ],
        [
            InlineKeyboardButton("🔔 تفعيل التنبيهات", callback_data="sub"),
            InlineKeyboardButton("📹 تنبيهات الفيديو", callback_data="video_sub")
        ],
        [
            InlineKeyboardButton("🔕 إيقاف التنبيهات", callback_data="unsub"),
            InlineKeyboardButton("📡 المصادر", callback_data="sources")
        ],
        [
            InlineKeyboardButton("📊 إحصائيات", callback_data="stats"),
            InlineKeyboardButton("ℹ️ عن البوت", callback_data="about")
        ]
    ]
    return InlineKeyboardMarkup(kb)


def news_keyboard(news_id: int, has_video: bool = False):
    kb = [
        [
            InlineKeyboardButton("🤖 تحليل AI", callback_data=f"ai_{news_id}"),
            InlineKeyboardButton("🔄 تحديث", callback_data="latest")
        ],
    ]
    if has_video:
        kb.append([InlineKeyboardButton("📹 شاهد الفيديو", callback_data=f"vid_{news_id}")])
    kb.append([InlineKeyboardButton("🏠 القائمة", callback_data="home")])
    return InlineKeyboardMarkup(kb)


# ═══════════════════════════════════════════════════════════
#              📱 أوامر البوت
# ═══════════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)
    stats["users"] = len(subscribed_users)

    msg = f"""🔴💥🔴 <b>بوت أخبار الحرب PRO</b> 🔴💥🔴
{'═' * 32}

مرحباً <b>{html.escape(user.first_name)}</b> 👋

🤖 <b>النظام الإخباري الأقوى</b>
تغطية لحظية للحرب بين:
🇺🇸 أمريكا | 🇮🇷 إيران | 🇮🇱 إسرائيل

{'━' * 30}
📡 <b>20 مصدر عالمي وعربي موثوق</b>
رويترز | BBC | AP | الجزيرة | العربية
فرانس24 | CNN | Defense News | وأكثر

🆕 <b>مميزات الإصدار 3.0 PRO:</b>
• 📹 فيديوهات الهجمات والعمليات
• ⚡ أخبار اليوم فقط لحظة بلحظة
• 🚨 تنبيهات فورية للعمليات العسكرية
• 🤖 تحليل AI متقدم للأخبار
• ✅ نظام التحقق الذكي
• 📊 مستوى التهديد لكل خبر
• 🎯 فلترة متقدمة حسب النوع

{'═' * 32}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 <b>المطوّر:</b> عباس الشافعي
🏆 <b>الإصدار:</b> 3.0 ULTRA PRO
⚡ <b>الأقوى | الأسرع | الأدق</b>
{'═' * 32}

اختر من القائمة 👇"""

    await update.message.reply_html(msg, reply_markup=main_keyboard())


async def cmd_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جلب فيديوهات الهجمات"""
    await update.message.reply_text("📹 جاري البحث عن فيديوهات الهجمات...")
    
    news = fetch_all_news()
    video_news = [n for n in news if n.get('video_url')]
    
    if video_news:
        await update.message.reply_html(
            f"📹 <b>تم العثور على {len(video_news)} فيديو</b>\n{'━'*20}"
        )
        for item in video_news[:5]:
            try:
                caption = f"📹 <b>{html.escape(item['title'][:200])}</b>\n\n{item.get('flag','')} {html.escape(item['source'])}\n🕐 {item['time']}\n\n👑 <b>عباس الشافعي</b>"
                await context.bot.send_video(
                    update.effective_chat.id,
                    video=item['video_url'],
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(1)
            except:
                # إرسال رابط إذا فشل الفيديو
                ai = analyze_with_ai(item['title'], item['description'], item['source'])
                msg = format_news(item, ai)
                await update.message.reply_html(msg, reply_markup=news_keyboard(item['id'], True))
    else:
        # البحث عن أخبار بها صور مع روابط فيديو
        await update.message.reply_html(
            """📹 <b>فيديوهات الهجمات والعمليات</b>
{'━'*28}

لمشاهدة أحدث فيديوهات الهجمات من مصادر موثوقة:

🔴 <a href="https://liveuamap.com/">LiveUA Map - خريطة حية</a>
🎥 <a href="https://www.reuters.com/news/archive/videoNews">Reuters Video</a>
📺 <a href="https://www.aljazeera.net/videos/">الجزيرة فيديو</a>
🎬 <a href="https://arabic.rt.com/video/">RT عربي فيديو</a>
📡 <a href="https://www.france24.com/ar/فيديو/">فرانس 24 فيديو</a>

👑 <b>عباس الشافعي</b>""",
            reply_markup=main_keyboard()
        )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أخبار اليوم فقط"""
    await update.message.reply_text("🔴 جاري جلب أخبار اليوم...")
    news = fetch_all_news()
    
    header = f"""🔴 <b>أخبار اليوم - {datetime.now().strftime('%d/%m/%Y')}</b>
{'═'*30}
⏰ آخر تحديث: {datetime.now().strftime('%H:%M')}
📊 تم العثور على <b>{len(news)}</b> خبر
{'═'*30}"""
    
    await update.message.reply_html(header)
    
    for item in news[:5]:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        msg = format_news(item, ai)
        
        try:
            if item.get('image_url'):
                await update.message.reply_photo(
                    photo=item['image_url'],
                    caption=msg[:1024],
                    parse_mode=ParseMode.HTML,
                    reply_markup=news_keyboard(item['id'], bool(item.get('video_url')))
                )
            else:
                await update.message.reply_html(msg, reply_markup=news_keyboard(item['id']))
        except:
            await update.message.reply_html(msg, reply_markup=news_keyboard(item['id']))
        await asyncio.sleep(0.5)


async def cmd_missiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أخبار الصواريخ والمسيّرات"""
    await update.message.reply_text("🚀 جاري البحث عن أخبار الصواريخ والمسيّرات...")
    keywords = ["صاروخ", "مسيّرة", "باليستي", "كروز", "missile", "drone", "ballistic", "rocket", "UAV"]
    news = fetch_all_news()
    filtered = [n for n in news if any(k.lower() in (n['title']+n['description']).lower() for k in keywords)]
    
    if filtered:
        for item in filtered[:4]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            await update.message.reply_html(format_news(item, ai), reply_markup=news_keyboard(item['id']))
            await asyncio.sleep(0.4)
    else:
        await update.message.reply_html("📭 لا توجد أخبار صواريخ حالياً", reply_markup=main_keyboard())


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أقوى الأخبار"""
    await update.message.reply_text("⚡ جاري جلب أقوى الأخبار...")
    news = fetch_all_news()
    # ترتيب حسب الأهمية
    urgent = [n for n in news if n.get('is_urgent', False)]
    top_news = urgent[:5] if urgent else news[:5]
    
    await update.message.reply_html(
        f"⚡ <b>أقوى {len(top_news)} أخبار الآن</b>",
        reply_markup=main_keyboard()
    )
    
    for item in top_news:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        try:
            if item.get('image_url'):
                await update.message.reply_photo(
                    photo=item['image_url'],
                    caption=format_news(item, ai)[:1024],
                    parse_mode=ParseMode.HTML,
                    reply_markup=news_keyboard(item['id'])
                )
            else:
                await update.message.reply_html(format_news(item, ai), reply_markup=news_keyboard(item['id']))
        except:
            await update.message.reply_html(format_news(item, ai), reply_markup=news_keyboard(item['id']))
        await asyncio.sleep(0.5)


# ═══════════════════════════════════════════════════════════
#     أوامر أساسية
# ═══════════════════════════════════════════════════════════
async def send_filtered(reply_fn, keywords, country):
    news = fetch_all_news()
    filtered = [n for n in news if any(k.lower() in (n['title']+n['description']).lower() for k in keywords)]
    if not filtered:
        await reply_fn(f"📭 لا توجد أخبار عن {country} حالياً", reply_markup=main_keyboard())
        return
    for item in filtered[:4]:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        await reply_fn(format_news(item, ai), reply_markup=news_keyboard(item['id'], bool(item.get('video_url'))))
        await asyncio.sleep(0.4)


async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ جاري جلب أحدث الأخبار من 20 مصدر...")
    await cmd_today(update, context)


async def cmd_breaking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري البحث عن أخبار عاجلة...")
    news = fetch_all_news()
    found = False
    for item in news[:20]:
        ai = analyze_with_ai(item['title'], item['description'], item['source'])
        if ai.get('importance') in ['عاجل', 'مهم'] or item.get('is_urgent'):
            try:
                if item.get('image_url'):
                    await update.message.reply_photo(
                        photo=item['image_url'],
                        caption=format_news(item, ai)[:1024],
                        parse_mode=ParseMode.HTML,
                        reply_markup=news_keyboard(item['id'])
                    )
                else:
                    await update.message.reply_html(format_news(item, ai), reply_markup=news_keyboard(item['id']))
            except:
                await update.message.reply_html(format_news(item, ai), reply_markup=news_keyboard(item['id']))
            found = True
            await asyncio.sleep(0.5)
    if not found:
        await update.message.reply_html("📭 <b>لا توجد أخبار عاجلة حالياً</b>", reply_markup=main_keyboard())


async def cmd_iran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇮🇷 جاري جلب أخبار إيران...")
    await send_filtered(update.message.reply_html, ["إيران", "iran", "طهران", "خامنئي", "irgc", "حرس الثوري", "persian"], "🇮🇷 إيران")


async def cmd_usa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇺🇸 جاري جلب أخبار أمريكا...")
    await send_filtered(update.message.reply_html, ["أمريكا", "america", "usa", "واشنطن", "ترامب", "بايدن", "pentagon", "البنتاغون"], "🇺🇸 أمريكا")


async def cmd_israel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇮🇱 جاري جلب أخبار إسرائيل...")
    await send_filtered(update.message.reply_html, ["إسرائيل", "israel", "تل أبيب", "نتنياهو", "netanyahu", "غزة", "idf"], "🇮🇱 إسرائيل")


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breaking_subscribers.add(update.effective_chat.id)
    await update.message.reply_html("🔔 <b>تم تفعيل تنبيهات الأخبار العاجلة!</b>\n\n✅ ستصلك الأخبار العاجلة فوراً\n/unsubscribe للإيقاف", reply_markup=main_keyboard())


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    breaking_subscribers.discard(update.effective_chat.id)
    video_subscribers.discard(update.effective_chat.id)
    await update.message.reply_html("🔕 <b>تم إيقاف جميع التنبيهات</b>", reply_markup=main_keyboard())


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sources_list = "\n".join([f"  {info['flag']} {name} - {info['trust']}%" for name, info in list(NEWS_SOURCES.items())[:10]])
    msg = f"""📊 <b>إحصائيات البوت PRO</b>
{'━'*28}
📰 أخبار محفوظة: <b>{len(news_cache)}</b>
👥 المشتركون: <b>{len(breaking_subscribers)}</b>
📹 مشتركو الفيديو: <b>{len(video_subscribers)}</b>
📡 المصادر: <b>{len(NEWS_SOURCES)}</b>
🕐 آخر تحديث: <b>{last_fetch_time.strftime('%H:%M') if last_fetch_time else 'لم يتم'}</b>
🚨 تنبيهات أرسلت: <b>{stats['breaking_sent']}</b>
{'━'*28}
<b>أبرز المصادر:</b>
{sources_list}
{'━'*28}
👑 <b>عباس الشافعي</b> | ⚡ <i>المطور الأول للأخبار</i>"""
    await update.message.reply_html(msg, reply_markup=main_keyboard())


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """📖 <b>أوامر البوت PRO</b>
{'━'*28}
/start - القائمة الرئيسية
/news - آخر الأخبار من 20 مصدر
/breaking - الأخبار العاجلة 🚨
/today - أخبار اليوم فقط 🔴
/top - أقوى الأخبار ⚡
/videos - فيديوهات الهجمات 📹
/missiles - أخبار الصواريخ 🚀
/iran - أخبار إيران 🇮🇷
/usa - أخبار أمريكا 🇺🇸
/israel - أخبار إسرائيل 🇮🇱
/subscribe - تفعيل التنبيهات 🔔
/unsubscribe - إيقاف التنبيهات 🔕
/stats - الإحصائيات 📊
{'━'*28}
👑 <b>عباس الشافعي</b> | ⚡ <i>المطور الأول للأخبار</i>"""
    await update.message.reply_html(msg, reply_markup=main_keyboard())


# ═══════════════════════════════════════════════════════════
#           🎯 معالج الأزرار
# ═══════════════════════════════════════════════════════════
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat.id

    async def send(msg, kb=None, photo=None):
        try:
            if photo:
                await context.bot.send_photo(chat_id, photo=photo, caption=msg[:1024], parse_mode=ParseMode.HTML, reply_markup=kb or main_keyboard())
            else:
                await context.bot.send_message(chat_id, msg, parse_mode=ParseMode.HTML, reply_markup=kb or main_keyboard())
        except Exception as e:
            logger.error(f"Send error: {e}")

    async def send_news_list(keywords=None, label=""):
        news = fetch_all_news()
        filtered = [n for n in news if not keywords or any(k.lower() in (n['title']+n['description']).lower() for k in keywords)]
        if not filtered:
            await send(f"📭 لا توجد أخبار {label} حالياً")
            return
        for item in filtered[:3]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            await send(format_news(item, ai), news_keyboard(item['id'], bool(item.get('video_url'))), item.get('image_url'))
            await asyncio.sleep(0.4)

    if data == "home":
        await query.edit_message_text("🏠 <b>القائمة الرئيسية</b>", reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "latest":
        await query.edit_message_text("⏳ جاري جلب آخر الأخبار من 20 مصدر...", parse_mode=ParseMode.HTML)
        await send_news_list()

    elif data == "breaking":
        await query.edit_message_text("🔍 جاري البحث...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        found = False
        for item in news[:20]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('importance') in ['عاجل', 'مهم'] or item.get('is_urgent'):
                await send(format_news(item, ai), news_keyboard(item['id']), item.get('image_url'))
                found = True
                await asyncio.sleep(0.4)
                break
        if not found:
            await send("📭 لا توجد أخبار عاجلة حالياً")

    elif data == "iran":
        await query.edit_message_text("🇮🇷 جاري جلب أخبار إيران...", parse_mode=ParseMode.HTML)
        await send_news_list(["إيران", "iran", "طهران", "خامنئي", "irgc"], "عن إيران")

    elif data == "usa":
        await query.edit_message_text("🇺🇸 جاري جلب أخبار أمريكا...", parse_mode=ParseMode.HTML)
        await send_news_list(["أمريكا", "america", "usa", "واشنطن", "ترامب", "pentagon"], "عن أمريكا")

    elif data == "israel":
        await query.edit_message_text("🇮🇱 جاري جلب أخبار إسرائيل...", parse_mode=ParseMode.HTML)
        await send_news_list(["إسرائيل", "israel", "تل أبيب", "نتنياهو", "غزة"], "عن إسرائيل")

    elif data == "military":
        await query.edit_message_text("💥 جاري جلب أخبار العمليات...", parse_mode=ParseMode.HTML)
        await send_news_list(["هجوم", "ضربة", "قصف", "عملية", "strike", "attack", "bombing", "airstrike"], "عسكرية")

    elif data == "nuclear":
        await query.edit_message_text("☢️ جاري جلب الأخبار النووية...", parse_mode=ParseMode.HTML)
        await send_news_list(["نووي", "nuclear", "تخصيب", "uranium", "يورانيوم", "مفاعل"], "نووية")

    elif data == "missiles":
        await query.edit_message_text("🚀 جاري جلب أخبار الصواريخ...", parse_mode=ParseMode.HTML)
        await send_news_list(["صاروخ", "مسيّرة", "باليستي", "missile", "drone", "ballistic"], "عن الصواريخ")

    elif data == "videos":
        await query.edit_message_text("📹 جاري البحث عن الفيديوهات...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        video_news = [n for n in news if n.get('video_url')]
        if video_news:
            for item in video_news[:3]:
                ai = analyze_with_ai(item['title'], item['description'], item['source'])
                await send(format_news(item, ai), news_keyboard(item['id'], True))
        else:
            await send("""📹 <b>روابط فيديوهات الهجمات المباشرة</b>
{'━'*28}

🔴 <a href="https://liveuamap.com/">LiveUA Map - خريطة حية</a>
🎥 <a href="https://www.reuters.com/news/archive/videoNews">Reuters Video</a>
📺 <a href="https://www.aljazeera.net/videos/">الجزيرة فيديو</a>
🎬 <a href="https://arabic.rt.com/video/">RT عربي فيديو</a>
📡 <a href="https://www.france24.com/ar/فيديو/">فرانس 24 فيديو</a>
🎯 <a href="https://www.militarytimes.com/">Military Times</a>

👑 <b>عباس الشافعي</b>""")

    elif data == "today":
        await query.edit_message_text(f"🔴 أخبار اليوم {datetime.now().strftime('%d/%m/%Y')}...", parse_mode=ParseMode.HTML)
        await send_news_list()

    elif data == "top_news":
        await query.edit_message_text("⚡ جاري جلب أقوى الأخبار...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        urgent = [n for n in news if n.get('is_urgent', False)] or news[:5]
        for item in urgent[:3]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            await send(format_news(item, ai), news_keyboard(item['id']), item.get('image_url'))
            await asyncio.sleep(0.4)

    elif data == "verified":
        await query.edit_message_text("✅ جاري البحث...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        found = False
        for item in news[:15]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('verified') == 'مؤكد' or item.get('trust', 0) >= 90:
                await send(format_news(item, ai), news_keyboard(item['id']))
                found = True
                await asyncio.sleep(0.4)
        if not found:
            await send("📭 لا توجد أخبار مؤكدة حالياً")

    elif data == "unverified":
        await query.edit_message_text("❓ جاري البحث...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        found = False
        for item in news[:15]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('verified') == 'غير مؤكد':
                await send(format_news(item, ai), news_keyboard(item['id']))
                found = True
                await asyncio.sleep(0.4)
        if not found:
            await send("📭 لا توجد أخبار غير مؤكدة حالياً")

    elif data == "pending":
        await query.edit_message_text("🔄 جاري البحث...", parse_mode=ParseMode.HTML)
        news = fetch_all_news()
        for item in news[:3]:
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            if ai.get('verified') == 'قيد التحقق':
                await send(format_news(item, ai), news_keyboard(item['id']))
                await asyncio.sleep(0.4)

    elif data == "sub":
        breaking_subscribers.add(chat_id)
        await query.edit_message_text("🔔 <b>تم تفعيل تنبيهات الأخبار العاجلة!</b>\n\n✅ ستصلك الأخبار فوراً", reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "video_sub":
        video_subscribers.add(chat_id)
        breaking_subscribers.add(chat_id)
        await query.edit_message_text("📹🔔 <b>تم تفعيل تنبيهات الفيديو والأخبار العاجلة!</b>", reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "unsub":
        breaking_subscribers.discard(chat_id)
        video_subscribers.discard(chat_id)
        await query.edit_message_text("🔕 <b>تم إيقاف جميع التنبيهات</b>", reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "sources":
        src = "📡 <b>مصادر الأخبار - 20 مصدر</b>\n" + "━"*28 + "\n\n"
        for name, info in NEWS_SOURCES.items():
            src += f"{info['flag']} <b>{name}</b> - ثقة {info['trust']}%\n"
        src += "\n👑 <b>عباس الشافعي</b>"
        await query.edit_message_text(src, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)

    elif data == "stats":
        await query.edit_message_text(
            f"📊 <b>الإحصائيات</b>\n{'━'*20}\n📰 {len(news_cache)} خبر\n👥 {len(breaking_subscribers)} مشترك\n📡 {len(NEWS_SOURCES)} مصدر\n🕐 {last_fetch_time.strftime('%H:%M') if last_fetch_time else 'لم يتم'}",
            reply_markup=main_keyboard(), parse_mode=ParseMode.HTML
        )

    elif data == "about":
        await query.edit_message_text(
            """🤖 <b>بوت أخبار الحرب PRO</b>
{'═'*30}
📡 20 مصدر عالمي وعربي
📹 فيديوهات الهجمات
⚡ أخبار لحظية
🏅 نظام ذكاء اصطناعي متقدم
✅ نظام التحقق الذكي
🚨 تنبيهات فورية

👨‍💻 <b>تطوير:</b> عباس الشافعي
🏆 <b>المطور:</b> عباس الشافعي
📅 <b>الإصدار:</b> 3.0 ULTRA PRO""",
            reply_markup=main_keyboard(), parse_mode=ParseMode.HTML
        )

    elif data.startswith("ai_"):
        news_id = int(data[3:])
        if news_id in news_cache:
            item = news_cache[news_id]
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            analysis = f"""🤖 <b>تحليل الذكاء الاصطناعي المتقدم</b>
{'═'*30}

📰 <b>{html.escape(item['title'][:100])}</b>

{'━'*28}
🔍 <b>التحقق:</b> {ai.get('verified', '—')}
⚠️ <b>الأهمية:</b> {ai.get('importance', '—')}
💢 <b>التهديد:</b> {ai.get('threat_level', '—')}
{ai.get('alert_level', '🟡')} <b>مستوى التنبيه</b>
📹 <b>فيديو:</b> {'نعم ✅' if ai.get('has_video') else 'لا ❌'}

📝 <b>الملخص:</b>
<i>{html.escape(str(ai.get('summary_ar', ''))[:300])}</i>

🌍 <b>الدول:</b> {html.escape(', '.join(ai.get('countries', [])))}
🏷️ <b>الوسوم:</b> {' '.join(['#' + t for t in ai.get('tags', [])])}
{'═'*30}
👑 <b>عباس الشافعي</b> | ⚡ <i>المطور الأول للأخبار</i>"""
            await send(analysis)

    elif data.startswith("vid_"):
        news_id = int(data[4:])
        if news_id in news_cache:
            item = news_cache[news_id]
            if item.get('video_url'):
                try:
                    await context.bot.send_video(
                        chat_id, video=item['video_url'],
                        caption=f"📹 {html.escape(item['title'][:200])}\n\n{item.get('flag','')} {html.escape(item['source'])}\n👑 عباس الشافعي",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    await send(f"📹 رابط الفيديو:\n{item.get('link', '')}")
            else:
                await send("📹 لا يوجد فيديو لهذا الخبر")


# ═══════════════════════════════════════════════════════════
#         ⏰ التنبيهات التلقائية كل 10 دقائق
# ═══════════════════════════════════════════════════════════
async def auto_alerts(context: ContextTypes.DEFAULT_TYPE):
    """فحص تلقائي كل 10 دقائق"""
    if not breaking_subscribers and not video_subscribers:
        return

    try:
        news = fetch_all_news()
        
        for item in news:
            if item['id'] in sent_news_ids:
                continue
            
            ai = analyze_with_ai(item['title'], item['description'], item['source'])
            is_breaking = ai.get('importance') == 'عاجل' or item.get('is_urgent', False)
            has_video = bool(item.get('video_url'))
            
            if is_breaking:
                sent_news_ids.add(item['id'])
                msg = "🚨🚨 <b>تنبيه عاجل!</b> 🚨🚨\n\n" + format_news(item, ai)
                stats["breaking_sent"] += 1
                
                for chat_id in list(breaking_subscribers):
                    try:
                        if item.get('image_url'):
                            await context.bot.send_photo(
                                chat_id, photo=item['image_url'],
                                caption=msg[:1024], parse_mode=ParseMode.HTML,
                                reply_markup=main_keyboard()
                            )
                        else:
                            await context.bot.send_message(
                                chat_id, msg, parse_mode=ParseMode.HTML,
                                reply_markup=main_keyboard()
                            )
                        await asyncio.sleep(0.1)
                    except:
                        breaking_subscribers.discard(chat_id)
            
            # إرسال فيديو لمشتركي الفيديو
            if has_video and video_subscribers:
                vid_msg = f"📹🚨 <b>فيديو عاجل!</b>\n\n{html.escape(item['title'])}\n\n{item.get('flag','')} {html.escape(item['source'])}"
                for chat_id in list(video_subscribers):
                    try:
                        await context.bot.send_video(
                            chat_id, video=item['video_url'],
                            caption=vid_msg, parse_mode=ParseMode.HTML
                        )
                    except:
                        try:
                            await context.bot.send_message(chat_id, vid_msg + f"\n\n🔗 {item.get('link','')}", parse_mode=ParseMode.HTML)
                        except:
                            video_subscribers.discard(chat_id)

    except Exception as e:
        logger.error(f"Auto alerts error: {e}")


# ═══════════════════════════════════════════════════════════
#                   🚀 تشغيل البوت
# ═══════════════════════════════════════════════════════════
def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║  🔴💥 بوت أخبار الحرب PRO v3.0 - يبدأ التشغيل 💥🔴  ║
║          👨‍💻 تطوير: عباس الشافعي                       ║
║          👑 تطوير: عباس الشافعي                  ║
║          📡 20 مصدر | 📹 فيديوهات | ⚡ لحظي            ║
╚══════════════════════════════════════════════════════════╝
    """)

    app = Application.builder().token(BOT_TOKEN).build()

    # الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", cmd_news))
    app.add_handler(CommandHandler("breaking", cmd_breaking))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("top", cmd_top))
    app.add_handler(CommandHandler("videos", cmd_videos))
    app.add_handler(CommandHandler("missiles", cmd_missiles))
    app.add_handler(CommandHandler("iran", cmd_iran))
    app.add_handler(CommandHandler("usa", cmd_usa))
    app.add_handler(CommandHandler("israel", cmd_israel))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("help", cmd_help))

    # الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))

    # فحص تلقائي كل 10 دقائق
    app.job_queue.run_repeating(auto_alerts, interval=600, first=60)

    print("✅ البوت يعمل الآن! اضغط Ctrl+C للإيقاف\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

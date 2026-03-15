#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 WAR NEWS BOT - بوت أخبار الحرب
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تم التطوير بواسطة: عباس الشافعي
تيليغرام: @c4scc
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import logging
import os
import json
import random
import hashlib
import feedparser
import aiohttp
import time
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, JobQueue
)
from telegram.constants import ParseMode
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

# ══════════════════════════════════════════════
#              إعدادات البوت
# ══════════════════════════════════════════════
BOT_TOKEN = os.getenv("BOT_TOKEN", "8528463202:AAFGu6IHRYuopmY072ylIz0r1UN5kQAQ_II")
DEVELOPER = "عباس الشافعي"
DEVELOPER_TG = "@c4scc"
BOT_VERSION = "2.0.0"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════
#              مصادر الأخبار الموثوقة
# ══════════════════════════════════════════════
NEWS_SOURCES = {
    "arabic": {
        "الجزيرة العربية": {
            "rss": "https://www.aljazeera.net/aljazeerarss/a7c186be-1baa-4bd4-9d80-a84db769f779/8c42a6cd-7b18-4d63-bf51-f438ac4f6a95",
            "trust": 95,
            "icon": "🔵",
            "lang": "ar"
        },
        "BBC عربي": {
            "rss": "https://feeds.bbci.co.uk/arabic/rss.xml",
            "trust": 97,
            "icon": "🔴",
            "lang": "ar"
        },
        "رويترز عربي": {
            "rss": "https://feeds.reuters.com/reuters/MENnews",
            "trust": 98,
            "icon": "🟠",
            "lang": "ar"
        },
        "العربية نت": {
            "rss": "https://www.alarabiya.net/tools/rss",
            "trust": 88,
            "icon": "🟡",
            "lang": "ar"
        },
        "سكاي نيوز عربية": {
            "rss": "https://www.skynewsarabia.com/rss.xml",
            "trust": 85,
            "icon": "🔷",
            "lang": "ar"
        },
        "RT عربي": {
            "rss": "https://arabic.rt.com/rss/",
            "trust": 70,
            "icon": "⭕",
            "lang": "ar"
        },
    },
    "international": {
        "Reuters": {
            "rss": "https://feeds.reuters.com/reuters/topNews",
            "trust": 98,
            "icon": "🟠",
            "lang": "en"
        },
        "AP News": {
            "rss": "https://rsshub.app/apnews/topics/apf-topnews",
            "trust": 97,
            "icon": "🔵",
            "lang": "en"
        },
        "BBC World": {
            "rss": "http://feeds.bbci.co.uk/news/world/rss.xml",
            "trust": 97,
            "icon": "🔴",
            "lang": "en"
        },
        "Al Jazeera English": {
            "rss": "https://www.aljazeera.com/xml/rss/all.xml",
            "trust": 92,
            "icon": "🔵",
            "lang": "en"
        },
        "The Guardian": {
            "rss": "https://www.theguardian.com/world/rss",
            "trust": 90,
            "icon": "🟣",
            "lang": "en"
        },
    }
}

# الكلمات المفتاحية للحرب
WAR_KEYWORDS = {
    "ar": [
        "إيران", "أمريكا", "إسرائيل", "حرب", "هجوم", "ضربة", "صواريخ",
        "غارة", "قتلى", "انفجار", "عسكري", "قوات", "طائرات", "دفاع",
        "تهديد", "توتر", "مواجهة", "تصعيد", "جبهة", "ميليشيا",
        "نووي", "مفاوضات", "عقوبات", "حزب الله", "الحوثيين", "غزة",
        "الضفة", "لبنان", "سوريا", "العراق", "اليمن", "بحر عمان"
    ],
    "en": [
        "iran", "america", "israel", "war", "attack", "strike", "missiles",
        "airstrike", "casualties", "explosion", "military", "forces",
        "aircraft", "defense", "threat", "tension", "confrontation",
        "escalation", "nuclear", "sanctions", "hezbollah", "houthi",
        "gaza", "lebanon", "syria", "iraq", "yemen"
    ]
}

# ══════════════════════════════════════════════
#              قاعدة البيانات المحلية
# ══════════════════════════════════════════════
class NewsDatabase:
    def __init__(self):
        self.db_file = "news_db.json"
        self.users_file = "users_db.json"
        self.load()

    def load(self):
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                self.news = json.load(f)
        except:
            self.news = {}
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                self.users = json.load(f)
        except:
            self.users = {}

    def save(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.news, f, ensure_ascii=False, indent=2)
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def add_news(self, news_id, data):
        self.news[news_id] = data
        if len(self.news) > 500:
            oldest = sorted(self.news.keys())[:100]
            for k in oldest:
                del self.news[k]
        self.save()

    def news_exists(self, news_id):
        return news_id in self.news

    def add_user(self, user_id, data):
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = data
            self.save()
        return self.users[uid]

    def get_user(self, user_id):
        return self.users.get(str(user_id), None)

    def update_user(self, user_id, key, value):
        uid = str(user_id)
        if uid in self.users:
            self.users[uid][key] = value
            self.save()

    def get_all_users(self):
        return self.users

    def get_stats(self):
        total_users = len(self.users)
        active_users = sum(1 for u in self.users.values() if u.get("alerts", True))
        arabic_users = sum(1 for u in self.users.values() if u.get("lang", "ar") == "ar")
        english_users = total_users - arabic_users
        return {
            "total": total_users,
            "active": active_users,
            "arabic": arabic_users,
            "english": english_users,
            "news_count": len(self.news)
        }

db = NewsDatabase()

# ══════════════════════════════════════════════
#              نظام التحقق من الأخبار
# ══════════════════════════════════════════════
class NewsVerifier:
    
    VERIFICATION_LEVELS = {
        "confirmed": {
            "ar": "✅ مؤكد",
            "en": "✅ Confirmed",
            "color": "🟢",
            "score_min": 85
        },
        "likely": {
            "ar": "🔶 محتمل",
            "en": "🔶 Likely True",
            "color": "🟡",
            "score_min": 65
        },
        "unverified": {
            "ar": "⚠️ غير مؤكد",
            "en": "⚠️ Unverified",
            "color": "🟠",
            "score_min": 45
        },
        "rumor": {
            "ar": "❌ شائعة",
            "en": "❌ Rumor",
            "color": "🔴",
            "score_min": 0
        }
    }

    @staticmethod
    def verify_news(source_name: str, trust_score: int, title: str, 
                    cross_sources: int = 1) -> dict:
        """تحليل ودرجة التحقق من الخبر"""
        
        score = trust_score
        
        # تعزيز النقاط بناءً على عدد المصادر المتقاطعة
        if cross_sources >= 3:
            score = min(100, score + 15)
        elif cross_sources == 2:
            score = min(100, score + 8)
        
        # تحليل الكلمات في العنوان
        doubt_words_ar = ["مصادر", "يُقال", "يُزعم", "مجهول", "غير رسمي", "ادعاء"]
        doubt_words_en = ["sources say", "allegedly", "claimed", "unconfirmed", "reportedly"]
        confirm_words_ar = ["رسمي", "أعلن", "أكد", "بيان", "وزارة", "رئيس"]
        confirm_words_en = ["official", "confirmed", "announced", "statement", "minister"]
        
        title_lower = title.lower()
        for w in doubt_words_ar + doubt_words_en:
            if w in title_lower:
                score -= 15
                break
        for w in confirm_words_ar + confirm_words_en:
            if w in title_lower:
                score += 10
                break
        
        score = max(0, min(100, score))
        
        # تحديد مستوى التحقق
        if score >= 85:
            level = "confirmed"
        elif score >= 65:
            level = "likely"
        elif score >= 45:
            level = "unverified"
        else:
            level = "rumor"
        
        return {
            "score": score,
            "level": level,
            "labels": NewsVerifier.VERIFICATION_LEVELS[level]
        }

    @staticmethod
    def get_trust_bar(score: int) -> str:
        """شريط درجة الموثوقية"""
        filled = int(score / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}] {score}%"

verifier = NewsVerifier()

# ══════════════════════════════════════════════
#              جالب الأخبار
# ══════════════════════════════════════════════
class NewsFetcher:

    @staticmethod
    def is_war_related(title: str, summary: str = "") -> bool:
        text = (title + " " + summary).lower()
        for kw in WAR_KEYWORDS["ar"] + WAR_KEYWORDS["en"]:
            if kw.lower() in text:
                return True
        return False

    @staticmethod
    def generate_id(title: str, source: str) -> str:
        return hashlib.md5(f"{title}{source}".encode()).hexdigest()[:12]

    @staticmethod
    async def fetch_feed(source_name: str, source_data: dict) -> list:
        """جلب أخبار من مصدر RSS"""
        news_list = []
        try:
            feed = feedparser.parse(source_data["rss"])
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")
                
                if not NewsFetcher.is_war_related(title, summary):
                    continue
                
                # تنظيف HTML من الملخص
                if summary:
                    soup = BeautifulSoup(summary, "html.parser")
                    summary = soup.get_text()[:300]
                
                news_id = NewsFetcher.generate_id(title, source_name)
                
                if not db.news_exists(news_id):
                    verification = verifier.verify_news(
                        source_name, 
                        source_data["trust"],
                        title
                    )
                    news_item = {
                        "id": news_id,
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": source_name,
                        "trust": source_data["trust"],
                        "icon": source_data["icon"],
                        "lang": source_data["lang"],
                        "verification": verification,
                        "timestamp": datetime.now().isoformat(),
                        "is_breaking": source_data["trust"] >= 90 and verification["level"] == "confirmed"
                    }
                    news_list.append(news_item)
                    db.add_news(news_id, news_item)
        except Exception as e:
            logger.error(f"Error fetching {source_name}: {e}")
        return news_list

    @staticmethod
    async def fetch_all_news() -> list:
        """جلب جميع الأخبار من كل المصادر"""
        all_news = []
        all_sources = {**NEWS_SOURCES["arabic"], **NEWS_SOURCES["international"]}
        
        tasks = []
        for name, data in all_sources.items():
            tasks.append(NewsFetcher.fetch_feed(name, data))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
        
        return all_news

fetcher = NewsFetcher()

# ══════════════════════════════════════════════
#              تنسيق الرسائل
# ══════════════════════════════════════════════
class MessageFormatter:

    @staticmethod
    def format_news_ar(news: dict, index: int = None) -> str:
        v = news["verification"]
        trust_bar = verifier.get_trust_bar(news["trust"])
        
        breaking_tag = ""
        if news.get("is_breaking"):
            breaking_tag = "🚨 *عاجل - خبر مؤكد الآن* 🚨\n━━━━━━━━━━━━━━━━━━━━\n"
        
        num = f"[{index}] " if index else ""
        
        msg = f"""
{breaking_tag}{num}{news['icon']} *{news['title']}*

📋 {news.get('summary', 'لا يوجد ملخص')[:250]}...

🗂️ *المصدر:* {news['source']}
⏰ *التوقيت:* {datetime.fromisoformat(news['timestamp']).strftime('%Y-%m-%d %H:%M')}
📊 *الموثوقية:* {trust_bar}
{v['labels']['color']} *حالة التحقق:* {v['labels']['ar']} (درجة: {v['score']}/100)

🔗 [اقرأ الخبر الكامل]({news['link']})

━━━━━━━━━━━━━━━━━━━━
🛠 تطوير: {DEVELOPER} | {DEVELOPER_TG}
"""
        return msg.strip()

    @staticmethod
    def format_news_en(news: dict, index: int = None) -> str:
        v = news["verification"]
        trust_bar = verifier.get_trust_bar(news["trust"])
        
        breaking_tag = ""
        if news.get("is_breaking"):
            breaking_tag = "🚨 *BREAKING NEWS - CONFIRMED* 🚨\n━━━━━━━━━━━━━━━━━━━━\n"
        
        num = f"[{index}] " if index else ""
        
        msg = f"""
{breaking_tag}{num}{news['icon']} *{news['title']}*

📋 {news.get('summary', 'No summary available')[:250]}...

🗂️ *Source:* {news['source']}
⏰ *Time:* {datetime.fromisoformat(news['timestamp']).strftime('%Y-%m-%d %H:%M')}
📊 *Trust Score:* {trust_bar}
{v['labels']['color']} *Verification:* {v['labels']['en']} ({v['score']}/100)

🔗 [Read Full Story]({news['link']})

━━━━━━━━━━━━━━━━━━━━
🛠 Dev: {DEVELOPER} | {DEVELOPER_TG}
"""
        return msg.strip()

    @staticmethod
    def get_main_menu_ar() -> InlineKeyboardMarkup:
        buttons = [
            [
                InlineKeyboardButton("📰 أحدث الأخبار", callback_data="latest_news"),
                InlineKeyboardButton("🚨 الأخبار العاجلة", callback_data="breaking_news"),
            ],
            [
                InlineKeyboardButton("🇮🇷 أخبار إيران", callback_data="iran_news"),
                InlineKeyboardButton("🇮🇱 أخبار إسرائيل", callback_data="israel_news"),
            ],
            [
                InlineKeyboardButton("🇺🇸 أخبار أمريكا", callback_data="usa_news"),
                InlineKeyboardButton("🌍 أخبار عالمية", callback_data="world_news"),
            ],
            [
                InlineKeyboardButton("✅ أخبار مؤكدة", callback_data="confirmed_news"),
                InlineKeyboardButton("⚠️ أخبار غير مؤكدة", callback_data="unverified_news"),
            ],
            [
                InlineKeyboardButton("🔔 تفعيل/إيقاف التنبيهات", callback_data="toggle_alerts"),
                InlineKeyboardButton("🌐 تغيير اللغة", callback_data="change_lang"),
            ],
            [
                InlineKeyboardButton("📊 إحصائيات البوت", callback_data="stats"),
                InlineKeyboardButton("ℹ️ عن البوت", callback_data="about"),
            ],
            [
                InlineKeyboardButton("🔍 تحقق من خبر", callback_data="fact_check"),
                InlineKeyboardButton("📡 المصادر الموثوقة", callback_data="sources"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def get_main_menu_en() -> InlineKeyboardMarkup:
        buttons = [
            [
                InlineKeyboardButton("📰 Latest News", callback_data="latest_news"),
                InlineKeyboardButton("🚨 Breaking News", callback_data="breaking_news"),
            ],
            [
                InlineKeyboardButton("🇮🇷 Iran News", callback_data="iran_news"),
                InlineKeyboardButton("🇮🇱 Israel News", callback_data="israel_news"),
            ],
            [
                InlineKeyboardButton("🇺🇸 USA News", callback_data="usa_news"),
                InlineKeyboardButton("🌍 World News", callback_data="world_news"),
            ],
            [
                InlineKeyboardButton("✅ Confirmed News", callback_data="confirmed_news"),
                InlineKeyboardButton("⚠️ Unverified News", callback_data="unverified_news"),
            ],
            [
                InlineKeyboardButton("🔔 Toggle Alerts", callback_data="toggle_alerts"),
                InlineKeyboardButton("🌐 Change Language", callback_data="change_lang"),
            ],
            [
                InlineKeyboardButton("📊 Bot Stats", callback_data="stats"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about"),
            ],
            [
                InlineKeyboardButton("🔍 Fact Check", callback_data="fact_check"),
                InlineKeyboardButton("📡 Trusted Sources", callback_data="sources"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

formatter = MessageFormatter()

# ══════════════════════════════════════════════
#              أوامر البوت
# ══════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    
    existing = db.get_user(uid)
    if not existing:
        db.add_user(uid, {
            "id": uid,
            "name": user.full_name,
            "username": user.username or "",
            "lang": "ar",
            "alerts": True,
            "joined": datetime.now().isoformat(),
            "news_count": 0
        })
    
    user_data = db.get_user(uid)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    if lang == "ar":
        welcome = f"""
🔥 *مرحباً بك في بوت أخبار الحرب* 🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
مرحباً *{user.first_name}* 👋

🌐 أنت الآن متصل بأقوى بوت لمتابعة:
• أخبار الحرب بين 🇺🇸 أمريكا و🇮🇷 إيران و🇮🇱 إسرائيل
• تحقق فوري من صحة الأخبار ✅❌
• مصادر عالمية موثوقة بنسبة 95-98%
• تنبيهات عاجلة فورية 🚨
• أخبار بالعربية والإنجليزية 🌍

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠 *تم التطوير على يد:* {DEVELOPER}
📱 *تيليغرام المطور:* {DEVELOPER_TG}
📌 *الإصدار:* v{BOT_VERSION}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

اختر من القائمة أدناه 👇
"""
        menu = formatter.get_main_menu_ar()
    else:
        welcome = f"""
🔥 *Welcome to War News Bot* 🔥
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hello *{user.first_name}* 👋

🌐 Connected to the most powerful war news bot:
• 🇺🇸 USA • 🇮🇷 Iran • 🇮🇱 Israel conflicts
• Instant fact-checking ✅❌
• 95-98% trusted global sources
• Instant breaking alerts 🚨
• Arabic & English news 🌍

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠 *Developed by:* {DEVELOPER}
📱 *Developer TG:* {DEVELOPER_TG}
📌 *Version:* v{BOT_VERSION}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose from the menu below 👇
"""
        menu = formatter.get_main_menu_en()
    
    await update.message.reply_text(
        welcome.strip(),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=menu,
        disable_web_page_preview=True
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    if lang == "ar":
        text = """
📖 *دليل استخدام البوت*
━━━━━━━━━━━━━━━━━━━━━━
🔹 /start - القائمة الرئيسية
🔹 /news - أحدث الأخبار
🔹 /breaking - الأخبار العاجلة
🔹 /iran - أخبار إيران
🔹 /israel - أخبار إسرائيل
🔹 /usa - أخبار أمريكا
🔹 /confirmed - الأخبار المؤكدة فقط
🔹 /sources - قائمة المصادر الموثوقة
🔹 /alert - تفعيل/إيقاف التنبيهات
🔹 /lang - تغيير اللغة
🔹 /stats - إحصائيات البوت
🔹 /check [نص] - تحقق من خبر
🔹 /about - معلومات عن البوت

🔵 نظام التحقق:
✅ مؤكد (85-100%)
🔶 محتمل (65-84%)
⚠️ غير مؤكد (45-64%)
❌ شائعة (0-44%)
"""
    else:
        text = """
📖 *Bot Usage Guide*
━━━━━━━━━━━━━━━━━━━━━━
🔹 /start - Main menu
🔹 /news - Latest news
🔹 /breaking - Breaking news
🔹 /iran - Iran news
🔹 /israel - Israel news
🔹 /usa - USA news
🔹 /confirmed - Confirmed news only
🔹 /sources - Trusted sources list
🔹 /alert - Toggle alerts
🔹 /lang - Change language
🔹 /stats - Bot statistics
🔹 /check [text] - Fact check news
🔹 /about - Bot information

🔵 Verification System:
✅ Confirmed (85-100%)
🔶 Likely (65-84%)
⚠️ Unverified (45-64%)
❌ Rumor (0-44%)
"""
    
    await update.message.reply_text(
        text.strip(),
        parse_mode=ParseMode.MARKDOWN
    )

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    wait_msg = await update.message.reply_text(
        "⏳ جاري جلب أحدث الأخبار..." if lang == "ar" else "⏳ Fetching latest news..."
    )
    
    news_list = await fetcher.fetch_all_news()
    
    if not news_list:
        news_items = list(db.news.values())
        news_list = sorted(news_items, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
    
    await wait_msg.delete()
    
    if not news_list:
        msg = "لا توجد أخبار متاحة حالياً." if lang == "ar" else "No news available at the moment."
        await update.message.reply_text(msg)
        return
    
    for i, news in enumerate(news_list[:5], 1):
        try:
            if lang == "ar":
                msg = formatter.format_news_ar(news, i)
            else:
                if news.get("lang") == "ar":
                    try:
                        translated = GoogleTranslator(source="ar", target="en").translate(news["title"])
                        news["title"] = translated
                    except:
                        pass
                msg = formatter.format_news_en(news, i)
            
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 تحقق أكثر" if lang == "ar" else "🔍 More Info", 
                                        callback_data=f"verify_{news['id']}"),
                    InlineKeyboardButton("📤 مشاركة" if lang == "ar" else "📤 Share", 
                                        callback_data=f"share_{news['id']}"),
                ]
            ])
            
            await update.message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=buttons,
                disable_web_page_preview=False
            )
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error sending news: {e}")
            continue

async def breaking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    wait_msg = await update.message.reply_text(
        "🚨 جاري جلب الأخبار العاجلة..." if lang == "ar" else "🚨 Fetching breaking news..."
    )
    
    all_news = await fetcher.fetch_all_news()
    breaking = [n for n in all_news if n.get("is_breaking")]
    
    if not breaking:
        news_items = list(db.news.values())
        breaking = [n for n in news_items if n.get("is_breaking")]
    
    await wait_msg.delete()
    
    if not breaking:
        msg = "⚡ لا توجد أخبار عاجلة مؤكدة في الوقت الحالي.\n\nاستخدم /news لأحدث الأخبار" \
              if lang == "ar" else \
              "⚡ No confirmed breaking news at the moment.\n\nUse /news for latest news"
        await update.message.reply_text(msg)
        return
    
    header = "🚨 *الأخبار العاجلة المؤكدة* 🚨\n━━━━━━━━━━━━━━━━━━\n" \
             if lang == "ar" else \
             "🚨 *CONFIRMED BREAKING NEWS* 🚨\n━━━━━━━━━━━━━━━━━━\n"
    
    await update.message.reply_text(header, parse_mode=ParseMode.MARKDOWN)
    
    for news in breaking[:3]:
        try:
            msg = formatter.format_news_ar(news) if lang == "ar" else formatter.format_news_en(news)
            await update.message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False
            )
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Breaking news error: {e}")

async def filtered_news(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_key: str):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    wait_msg = await update.message.reply_text("⏳ جاري البحث..." if lang == "ar" else "⏳ Searching...")
    
    all_news = await fetcher.fetch_all_news()
    if not all_news:
        all_news = list(db.news.values())
    
    filters_map = {
        "iran": ["إيران", "iran", "طهران", "tehran", "خامنئي", "الحرس الثوري", "irgc"],
        "israel": ["إسرائيل", "israel", "نتنياهو", "netanyahu", "تل أبيب", "tel aviv", "جيش الاحتلال", "idf"],
        "usa": ["أمريكا", "america", "بايدن", "biden", "ترامب", "trump", "واشنطن", "washington", "البيت الأبيض"],
        "confirmed": [],
        "unverified": []
    }
    
    if filter_key in ["confirmed", "unverified"]:
        if filter_key == "confirmed":
            filtered = [n for n in all_news if n.get("verification", {}).get("level") == "confirmed"]
        else:
            filtered = [n for n in all_news if n.get("verification", {}).get("level") in ["unverified", "rumor"]]
    else:
        keywords = filters_map.get(filter_key, [])
        filtered = []
        for news in all_news:
            text = (news.get("title", "") + " " + news.get("summary", "")).lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(news)
    
    await wait_msg.delete()
    
    if not filtered:
        no_result = {
            "ar": "لم يتم العثور على أخبار لهذا الفلتر حالياً.",
            "en": "No news found for this filter currently."
        }
        await update.message.reply_text(no_result[lang])
        return
    
    for news in filtered[:5]:
        try:
            msg = formatter.format_news_ar(news) if lang == "ar" else formatter.format_news_en(news)
            await update.message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=False
            )
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Filter news error: {e}")

async def iran_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await filtered_news(update, context, "iran")

async def israel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await filtered_news(update, context, "israel")

async def usa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await filtered_news(update, context, "usa")

async def confirmed_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await filtered_news(update, context, "confirmed")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data = db.get_user(uid)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    current = user_data.get("alerts", True) if user_data else True
    new_state = not current
    db.update_user(uid, "alerts", new_state)
    
    if lang == "ar":
        msg = f"✅ تم تفعيل التنبيهات العاجلة!" if new_state else "🔕 تم إيقاف التنبيهات!"
    else:
        msg = "✅ Breaking news alerts enabled!" if new_state else "🔕 Alerts disabled!"
    
    await update.message.reply_text(msg)

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
            InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"),
        ]
    ])
    await update.message.reply_text(
        "🌐 اختر اللغة / Choose Language:",
        reply_markup=buttons
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    if not context.args:
        if lang == "ar":
            await update.message.reply_text(
                "🔍 *تحقق من الأخبار*\n\nأرسل: `/check [نص الخبر]`\nمثال: `/check صواريخ إيرانية تستهدف قاعدة أمريكية`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "🔍 *Fact Check*\n\nSend: `/check [news text]`\nExample: `/check Iranian missiles target US base`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    news_text = " ".join(context.args)
    
    # تحليل النص
    score = 50  # درجة افتراضية
    
    # البحث في المصادر المحلية
    matches = []
    for news_id, news in db.news.items():
        if any(word.lower() in news.get("title", "").lower() 
               for word in news_text.split() if len(word) > 3):
            matches.append(news)
    
    if matches:
        avg_trust = sum(m["trust"] for m in matches) / len(matches)
        score = int(avg_trust)
        sources_found = list(set(m["source"] for m in matches))
        
        if lang == "ar":
            result = f"""
🔍 *نتائج التحقق من الخبر*
━━━━━━━━━━━━━━━━━━━━━━
📝 *الخبر المُدخل:* {news_text}

✅ *وُجد في {len(matches)} مصدر موثوق!*
📡 *المصادر:* {', '.join(sources_found[:3])}
📊 *درجة الموثوقية:* {verifier.get_trust_bar(score)}

{verifier.verify_news('check', score, news_text)['labels']['color']} *الحكم النهائي:* {verifier.verify_news('check', score, news_text)['labels']['ar']}
"""
        else:
            result = f"""
🔍 *Fact Check Results*
━━━━━━━━━━━━━━━━━━━━━━
📝 *Checked:* {news_text}

✅ *Found in {len(matches)} trusted source(s)!*
📡 *Sources:* {', '.join(sources_found[:3])}
📊 *Trust Score:* {verifier.get_trust_bar(score)}

{verifier.verify_news('check', score, news_text)['labels']['color']} *Verdict:* {verifier.verify_news('check', score, news_text)['labels']['en']}
"""
    else:
        if lang == "ar":
            result = f"""
🔍 *نتائج التحقق*
━━━━━━━━━━━━━━━━━━━━━━
📝 *الخبر:* {news_text}

⚠️ *لم يُعثر على هذا الخبر في مصادرنا الموثوقة حتى الآن.*
📊 *درجة الموثوقية:* {verifier.get_trust_bar(35)}

❌ *الحكم:* يُرجح أنه شائعة أو خبر غير مؤكد
💡 *نصيحة:* انتظر للتأكيد من مصادر موثوقة
"""
        else:
            result = f"""
🔍 *Fact Check Result*
━━━━━━━━━━━━━━━━━━━━━━
📝 *News:* {news_text}

⚠️ *Not found in our trusted sources yet.*
📊 *Trust Score:* {verifier.get_trust_bar(35)}

❌ *Verdict:* Likely rumor or unconfirmed
💡 *Tip:* Wait for confirmation from trusted sources
"""
    
    await update.message.reply_text(result.strip(), parse_mode=ParseMode.MARKDOWN)

async def sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    if lang == "ar":
        text = "📡 *المصادر الموثوقة المتابعة*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "🌍 *المصادر العربية:*\n"
        for name, data in NEWS_SOURCES["arabic"].items():
            text += f"{data['icon']} *{name}* - موثوقية: {data['trust']}%\n"
        text += "\n🌐 *المصادر الدولية:*\n"
        for name, data in NEWS_SOURCES["international"].items():
            text += f"{data['icon']} *{name}* - Trust: {data['trust']}%\n"
    else:
        text = "📡 *Trusted News Sources*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "🌍 *Arabic Sources:*\n"
        for name, data in NEWS_SOURCES["arabic"].items():
            text += f"{data['icon']} *{name}* - Trust: {data['trust']}%\n"
        text += "\n🌐 *International Sources:*\n"
        for name, data in NEWS_SOURCES["international"].items():
            text += f"{data['icon']} *{name}* - Trust: {data['trust']}%\n"
    
    await update.message.reply_text(text.strip(), parse_mode=ParseMode.MARKDOWN)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    stats = db.get_stats()
    
    if lang == "ar":
        text = f"""
📊 *إحصائيات البوت*
━━━━━━━━━━━━━━━━━━━━━━
👥 *المستخدمون:* {stats['total']}
🔔 *المفعّل تنبيهاتهم:* {stats['active']}
🇸🇦 *مستخدمو العربية:* {stats['arabic']}
🇺🇸 *مستخدمو الإنجليزية:* {stats['english']}
📰 *الأخبار المحفوظة:* {stats['news_count']}
📡 *المصادر الموثوقة:* {len(NEWS_SOURCES['arabic']) + len(NEWS_SOURCES['international'])}

🛠 *المطور:* {DEVELOPER} | {DEVELOPER_TG}
📌 *الإصدار:* v{BOT_VERSION}
"""
    else:
        text = f"""
📊 *Bot Statistics*
━━━━━━━━━━━━━━━━━━━━━━
👥 *Total Users:* {stats['total']}
🔔 *Alerts Active:* {stats['active']}
🇸🇦 *Arabic Users:* {stats['arabic']}
🇺🇸 *English Users:* {stats['english']}
📰 *Saved News:* {stats['news_count']}
📡 *Trusted Sources:* {len(NEWS_SOURCES['arabic']) + len(NEWS_SOURCES['international'])}

🛠 *Developer:* {DEVELOPER} | {DEVELOPER_TG}
📌 *Version:* v{BOT_VERSION}
"""
    await update.message.reply_text(text.strip(), parse_mode=ParseMode.MARKDOWN)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    
    if lang == "ar":
        text = f"""
ℹ️ *عن بوت أخبار الحرب*
━━━━━━━━━━━━━━━━━━━━━━━━
🤖 *اسم البوت:* War News Bot
📌 *الإصدار:* v{BOT_VERSION}
🛠 *المطور:* {DEVELOPER}
📱 *تيليغرام:* {DEVELOPER_TG}

🔥 *المميزات الرئيسية:*
• تغطية شاملة للحرب الأمريكية-الإيرانية-الإسرائيلية
• {len(NEWS_SOURCES['arabic']) + len(NEWS_SOURCES['international'])} مصدر موثوق عالمي وعربي
• نظام تحقق ذكي بأربعة مستويات
• تنبيهات عاجلة فورية
• دعم كامل للغتين العربية والإنجليزية
• تحليل ودرجة موثوقية لكل خبر
• تصفية الأخبار حسب الدولة والموثوقية
• أداة تحقق من الأخبار المشبوهة

📜 *ملاحظة:* يعتمد البوت على مصادر إخبارية موثوقة
ولا يمثل رأي المطور أي توجه سياسي.

━━━━━━━━━━━━━━━━━━━━━━━━
جميع الحقوق محفوظة © {datetime.now().year}
"""
    else:
        text = f"""
ℹ️ *About War News Bot*
━━━━━━━━━━━━━━━━━━━━━━━━
🤖 *Bot Name:* War News Bot
📌 *Version:* v{BOT_VERSION}
🛠 *Developer:* {DEVELOPER}
📱 *Telegram:* {DEVELOPER_TG}

🔥 *Key Features:*
• Comprehensive US-Iran-Israel war coverage
• {len(NEWS_SOURCES['arabic']) + len(NEWS_SOURCES['international'])} trusted global & Arabic sources
• Smart 4-level verification system
• Instant breaking news alerts
• Full Arabic & English support
• Trust score analysis for every news item
• Country & credibility filtering
• Rumor fact-checking tool

📜 *Note:* This bot relies on trusted news sources.
Developer does not hold any political views.

━━━━━━━━━━━━━━━━━━━━━━━━
All rights reserved © {datetime.now().year}
"""
    await update.message.reply_text(text.strip(), parse_mode=ParseMode.MARKDOWN)

# ══════════════════════════════════════════════
#              معالج الأزرار
# ══════════════════════════════════════════════
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    uid = update.effective_user.id
    user_data = db.get_user(uid)
    lang = user_data.get("lang", "ar") if user_data else "ar"
    data = query.data
    
    if data == "latest_news":
        await query.message.reply_text(
            "⏳ جاري جلب الأخبار..." if lang == "ar" else "⏳ Fetching news..."
        )
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await news_command(fake_update, context)
    
    elif data == "breaking_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await breaking_command(fake_update, context)
    
    elif data == "iran_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await filtered_news(fake_update, context, "iran")
    
    elif data == "israel_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await filtered_news(fake_update, context, "israel")
    
    elif data == "usa_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await filtered_news(fake_update, context, "usa")
    
    elif data == "world_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await news_command(fake_update, context)
    
    elif data == "confirmed_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await filtered_news(fake_update, context, "confirmed")
    
    elif data == "unverified_news":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await filtered_news(fake_update, context, "unverified")
    
    elif data == "toggle_alerts":
        current = user_data.get("alerts", True) if user_data else True
        new_state = not current
        db.update_user(uid, "alerts", new_state)
        if lang == "ar":
            msg = "✅ تم تفعيل التنبيهات!" if new_state else "🔕 تم إيقاف التنبيهات!"
        else:
            msg = "✅ Alerts enabled!" if new_state else "🔕 Alerts disabled!"
        await query.answer(msg, show_alert=True)
    
    elif data == "change_lang":
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
                InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en"),
            ]
        ])
        await query.message.reply_text(
            "🌐 اختر اللغة / Choose Language:",
            reply_markup=buttons
        )
    
    elif data == "set_lang_ar":
        db.update_user(uid, "lang", "ar")
        await query.answer("✅ تم تغيير اللغة إلى العربية!", show_alert=True)
        await query.message.reply_text(
            "✅ تم تغيير اللغة إلى العربية 🇸🇦",
            reply_markup=formatter.get_main_menu_ar()
        )
    
    elif data == "set_lang_en":
        db.update_user(uid, "lang", "en")
        await query.answer("✅ Language changed to English!", show_alert=True)
        await query.message.reply_text(
            "✅ Language changed to English 🇺🇸",
            reply_markup=formatter.get_main_menu_en()
        )
    
    elif data == "stats":
        stats = db.get_stats()
        if lang == "ar":
            await query.message.reply_text(
                f"📊 المستخدمون: {stats['total']} | الأخبار: {stats['news_count']}",
            )
        else:
            await query.message.reply_text(
                f"📊 Users: {stats['total']} | News: {stats['news_count']}",
            )
    
    elif data == "about":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await about_command(fake_update, context)
    
    elif data == "sources":
        fake_update = type('obj', (object,), {'message': query.message, 'effective_user': update.effective_user})()
        await sources_command(fake_update, context)
    
    elif data == "fact_check":
        if lang == "ar":
            await query.message.reply_text(
                "🔍 أرسل: `/check [نص الخبر]`\nمثال: `/check صواريخ إيران تضرب قاعدة أمريكية`",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.message.reply_text(
                "🔍 Send: `/check [news text]`\nExample: `/check Iran missiles hit US base`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("verify_"):
        news_id = data.replace("verify_", "")
        news = db.news.get(news_id)
        if news:
            v = news["verification"]
            if lang == "ar":
                detail = f"""
🔬 *تفاصيل التحقق التقني*
━━━━━━━━━━━━━━━━━━━━━━
📰 *العنوان:* {news['title'][:100]}
📡 *المصدر:* {news['source']}
📊 *درجة موثوقية المصدر:* {news['trust']}%
🧮 *درجة التحقق:* {v['score']}/100
{v['labels']['color']} *الحكم:* {v['labels']['ar']}
📊 *الشريط:* {verifier.get_trust_bar(v['score'])}
"""
            else:
                detail = f"""
🔬 *Technical Verification Details*
━━━━━━━━━━━━━━━━━━━━━━
📰 *Title:* {news['title'][:100]}
📡 *Source:* {news['source']}
📊 *Source Trust:* {news['trust']}%
🧮 *Verify Score:* {v['score']}/100
{v['labels']['color']} *Verdict:* {v['labels']['en']}
📊 *Bar:* {verifier.get_trust_bar(v['score'])}
"""
            await query.message.reply_text(detail.strip(), parse_mode=ParseMode.MARKDOWN)

# ══════════════════════════════════════════════
#              المهمة الدورية
# ══════════════════════════════════════════════
async def auto_news_job(context: ContextTypes.DEFAULT_TYPE):
    """جلب وإرسال الأخبار الجديدة تلقائياً كل 15 دقيقة"""
    logger.info("🔄 Auto news fetch job running...")
    
    new_news = await fetcher.fetch_all_news()
    breaking_news = [n for n in new_news if n.get("is_breaking")]
    
    if breaking_news:
        users = db.get_all_users()
        for uid, user_data in users.items():
            if not user_data.get("alerts", True):
                continue
            
            lang = user_data.get("lang", "ar")
            
            for news in breaking_news[:2]:
                try:
                    if lang == "ar":
                        msg = f"🚨 *خبر عاجل مؤكد الآن!*\n━━━━━━━━━━━━━━\n\n{formatter.format_news_ar(news)}"
                    else:
                        msg = f"🚨 *BREAKING NEWS - CONFIRMED NOW!*\n━━━━━━━━━━━━━━\n\n{formatter.format_news_en(news)}"
                    
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text=msg,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=False
                    )
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error sending to user {uid}: {e}")

# ══════════════════════════════════════════════
#              تشغيل البوت
# ══════════════════════════════════════════════
async def set_commands(app: Application):
    commands = [
        BotCommand("start", "القائمة الرئيسية"),
        BotCommand("news", "أحدث الأخبار"),
        BotCommand("breaking", "الأخبار العاجلة المؤكدة"),
        BotCommand("iran", "أخبار إيران"),
        BotCommand("israel", "أخبار إسرائيل"),
        BotCommand("usa", "أخبار أمريكا"),
        BotCommand("confirmed", "الأخبار المؤكدة فقط"),
        BotCommand("check", "تحقق من خبر"),
        BotCommand("sources", "المصادر الموثوقة"),
        BotCommand("alert", "تفعيل/إيقاف التنبيهات"),
        BotCommand("lang", "تغيير اللغة"),
        BotCommand("stats", "إحصائيات البوت"),
        BotCommand("about", "عن البوت"),
        BotCommand("help", "المساعدة"),
    ]
    await app.bot.set_my_commands(commands)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ الرجاء تعيين BOT_TOKEN في متغيرات البيئة أو في الكود")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("breaking", breaking_command))
    app.add_handler(CommandHandler("iran", iran_command))
    app.add_handler(CommandHandler("israel", israel_command))
    app.add_handler(CommandHandler("usa", usa_command))
    app.add_handler(CommandHandler("confirmed", confirmed_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("sources", sources_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("about", about_command))
    
    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # المهمة الدورية - كل 15 دقيقة
    app.job_queue.run_repeating(auto_news_job, interval=900, first=30)
    
    # إعداد الأوامر عند بدء التشغيل
    app.post_init = set_commands
    
    logger.info(f"""
╔══════════════════════════════════════╗
║      🔥 WAR NEWS BOT STARTED 🔥      ║
║  Developer: {DEVELOPER}           ║
║  Telegram: {DEVELOPER_TG}              ║
║  Version: v{BOT_VERSION}                   ║
╚══════════════════════════════════════╝
""")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

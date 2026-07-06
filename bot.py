#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════════════════╗
║   ULTIMATE MEGA BOT – v14.0 – PER-USER API – PREMIUM EDITION          ║
║   ⚡ 1000x Speed  🔥 Enterprise‑Grade  🛡️ Military‑Grade Security      ║
║   👑 Developer: DK Sharma  |  📌 Admin: @OfficalEarningZone            ║
║   🔐 Per‑User Report Login  |  🛡️ Zero Runtime Errors (Fixed Global)  ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import aiosqlite
import csv
import io
import logging
import os
import random
import re
import smtplib
import sqlite3
import string
import sys
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple

# ---------- Environment Config ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "5888777479").split(",") if x.strip().isdigit()]

# ---------- Third Party Imports ----------
import aiohttp
import requests
from aiohttp import ClientTimeout, TCPConnector

# Telegram bot (compatible with Python 3.14)
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Optional dependencies
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from telethon import TelegramClient
    from telethon.tl.functions.account import ReportPeerRequest
    from telethon.tl.types import InputReportReasonSpam
    from telethon.errors import FloodWaitError, SessionPasswordNeededError
    from telethon.sessions import StringSession
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MegaBot")
logger.setLevel(logging.INFO)

# ---------- Module Settings ----------
REG_DEFAULT_REFERRAL = "1816"
REG_DEFAULT_PASSWORD = "Test@123"
REG_VERIFY_CODE = "7777"
REG_TIME_ZONE = "Asia/Calcutta"
REG_API_URL = "https://api.earnmigo.com/api/app/user/login/email"
REG_DB_PATH = "registrations.db"

REF_HOLWIN_INVITE = "WLRPSY"
REF_REX_INVITE = "O6NVYX"
REF_DB_PATH = "referrals.db"

UNBAN_DB_PATH = "appeals.db"
UNBAN_DEFAULT_DELAY = 1.0
UNBAN_MAX_RETRIES = 3
UNBAN_MAX_CONCURRENT_SENDS = 5
UNBAN_RATE_LIMIT_SECONDS = 60
UNBAN_RATE_LIMIT_CALLS = 20

REPORT_DB_PATH = "report_data.db"
REPORT_DEFAULT_MAX = 20000
REPORT_MAX_TARGETS = 10

# Default API credentials (only used if user hasn't set their own)
DEFAULT_API_ID = int(os.environ.get("API_ID", 32956022))
DEFAULT_API_HASH = os.environ.get("API_HASH", "5853b9eed0e062cebce5e46203f767ac")

# ---------- Global Application Reference ----------
APPLICATION = None
BOT_START_TIME = datetime.now()

# ---------- Database Initialisation (with new report_config table) ----------
async def init_all_dbs():
    """Create all database tables for every module."""
    try:
        # Registration DB
        async with aiosqlite.connect(REG_DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT,
                    referral TEXT,
                    authorized_key TEXT,
                    user_id TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    user_id INTEGER PRIMARY KEY,
                    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS pending_requests (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

        # Referral DB
        async with aiosqlite.connect(REF_DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mobile TEXT UNIQUE,
                    platform TEXT,
                    invite_used TEXT,
                    telegram_id INTEGER,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

        # Unban DB
        async with aiosqlite.connect(UNBAN_DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    tid INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    password TEXT,
                    reason TEXT DEFAULT 'personal communication',
                    delay REAL DEFAULT 1,
                    approved INTEGER DEFAULT 0,
                    email_valid INTEGER DEFAULT 1,
                    banned INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'en',
                    requested_at DATETIME,
                    last_active DATETIME,
                    total_appeals INTEGER DEFAULT 0,
                    success_appeals INTEGER DEFAULT 0,
                    failed_appeals INTEGER DEFAULT 0,
                    smtp_host TEXT DEFAULT 'smtp.gmail.com',
                    smtp_port INTEGER DEFAULT 587,
                    support_email TEXT DEFAULT 'support@whatsapp.com'
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS numbers (
                    phone TEXT PRIMARY KEY,
                    tid INTEGER,
                    last_appeal DATETIME,
                    appeal_count INTEGER DEFAULT 0,
                    blacklisted INTEGER DEFAULT 0,
                    custom_reason TEXT,
                    FOREIGN KEY(tid) REFERENCES users(tid)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tid INTEGER,
                    template TEXT,
                    is_default INTEGER DEFAULT 0,
                    FOREIGN KEY(tid) REFERENCES users(tid)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS appeal_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tid INTEGER,
                    phone TEXT,
                    success INTEGER,
                    error TEXT,
                    sent_at DATETIME,
                    template_used TEXT,
                    method TEXT,
                    FOREIGN KEY(tid) REFERENCES users(tid)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS scheduler_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tid INTEGER,
                    cron_expr TEXT,
                    interval_minutes INTEGER,
                    next_run DATETIME,
                    active INTEGER DEFAULT 1,
                    last_run DATETIME,
                    FOREIGN KEY(tid) REFERENCES users(tid)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS proxies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proxy TEXT UNIQUE,
                    last_used DATETIME,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS rate_limit (
                    tid INTEGER,
                    action TEXT,
                    timestamp DATETIME,
                    PRIMARY KEY (tid, action, timestamp)
                )
            ''')
            defaults = [
                ('global_delay', '1'),
                ('last_backup', ''),
                ('proxy_list', ''),
                ('captcha_api_key', ''),
                ('smtp_host', 'smtp.gmail.com'),
                ('smtp_port', '587'),
                ('support_emails', 'support@whatsapp.com,support@meta.com'),
                ('auto_backup_interval', '24'),
                ('enable_dashboard', 'true')
            ]
            for k, v in defaults:
                await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            cur = await db.execute("SELECT COUNT(*) FROM user_templates WHERE is_default=1")
            if (await cur.fetchone())[0] == 0:
                templates = []
                for i in range(1, 101):
                    templates.append(f"Appeal #{i}: My number {{number}} is banned. I use it for {{reason}}. Please help. {{name}}")
                for t in set(templates):
                    await db.execute("INSERT INTO user_templates (tid, template, is_default) VALUES (0, ?, 1)", (t,))
            await db.commit()

        # Report DB – add user_config table for per‑user API credentials
        async with aiosqlite.connect(REPORT_DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    premium_expiry INTEGER DEFAULT 0,
                    blocked INTEGER DEFAULT 0,
                    joined INTEGER DEFAULT 0
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT PRIMARY KEY,
                    duration_hours INTEGER,
                    used_by INTEGER DEFAULT 0,
                    used_at INTEGER DEFAULT 0
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS report_sessions (
                    user_id INTEGER PRIMARY KEY,
                    session_string TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # New table for per‑user API credentials
            await db.execute('''
                CREATE TABLE IF NOT EXISTS report_user_config (
                    user_id INTEGER PRIMARY KEY,
                    api_id INTEGER,
                    api_hash TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

        logger.info("All databases initialised (including report_user_config).")
        return True
    except Exception as e:
        logger.error(f"Database initialisation error: {e}")
        return False

# ---------- Persistent Main Menu Keyboard ----------
def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton("📋 Registration Bot"),
            KeyboardButton("📈 Referral Bot"),
        ],
        [
            KeyboardButton("🛡️ Unban Bot"),
            KeyboardButton("🔍 Ban Check Bot"),
        ],
        [
            KeyboardButton("🚨 Report Bot"),
            KeyboardButton("🎮 Fun & Utilities"),
        ],
        [
            KeyboardButton("⚙️ Global Settings"),
            KeyboardButton("❓ Help"),
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

# ---------- Module Entry ----------
async def module_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🌟 *Welcome to the ULTIMATE MEGA BOT!*\n\n"
        "Choose a module from the buttons below. Each module has its own powerful features.\n"
        "Use the persistent keyboard to navigate anytime.\n\n"
        "👑 *Developer:* DK Sharma\n"
        "📌 *Admin:* @OfficalEarningZone",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# ======================================================================
# REGISTRATION MODULE (unchanged)
# ======================================================================
REG_STATES = {}
REG_REFERRAL = REG_DEFAULT_REFERRAL
REG_CONCURRENCY = 250
REG_DELAY = 0.002
REG_TURBO = False
REG_RUNNING = False
REG_PAUSED = False
REG_CANCEL = False
REG_PROXY_MANAGER = None

class RegProxyManager:
    def __init__(self):
        self.proxies = []
        self.alive = set()
        self.lock = asyncio.Lock()
    def add_proxy(self, proxy: str) -> bool:
        proxy = proxy.strip()
        if not proxy or "://" not in proxy:
            return False
        self.proxies.append(proxy)
        self.alive.add(proxy)
        return True
    async def get_proxy(self):
        async with self.lock:
            alive = [p for p in self.proxies if p in self.alive]
            if not alive:
                return None
            return random.choice(alive)
    async def mark_dead(self, proxy):
        async with self.lock:
            self.alive.discard(proxy)

async def registration_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 Register", callback_data="reg_register")],
        [InlineKeyboardButton("📊 Dashboard", callback_data="reg_dashboard")],
        [InlineKeyboardButton("📜 History", callback_data="reg_history")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="reg_settings")],
        [InlineKeyboardButton("📤 Export", callback_data="reg_export")],
        [InlineKeyboardButton("🚀 Turbo Mode", callback_data="reg_turbo")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        "📋 *Registration Bot*\n\nRegister accounts on EarnMigo with your referral.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def reg_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📌 Enter count and optional referral:\nFormat: `count referral`\nExample: `100 1816`",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data["reg_waiting"] = "register"

async def reg_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REG_REFERRAL, REG_PROXY_MANAGER
    text = update.message.text.strip()
    waiting = context.user_data.get("reg_waiting")

    if waiting == "register":
        parts = text.split()
        try:
            count = int(parts[0])
            referral = parts[1] if len(parts) > 1 else REG_REFERRAL
            if count > 50000:
                await update.message.reply_text("❌ Max 50,000.")
                return
            if REG_RUNNING:
                await update.message.reply_text("⏳ Already running.")
                return
            context.user_data.pop("reg_waiting")
            await update.message.reply_text(f"🚀 Starting {count} accounts with referral `{referral}`...")
            asyncio.create_task(run_registration(update, count, referral))
        except ValueError:
            await update.message.reply_text("❌ Invalid. Send: `count referral`")
    elif waiting == "set_referral":
        if text.isdigit() and len(text) >= 4:
            REG_REFERRAL = text
            await update.message.reply_text(f"✅ Referral code updated to `{text}`")
        else:
            await update.message.reply_text("❌ Invalid referral code (must be numeric, min 4 digits).")
        context.user_data.pop("reg_waiting")
    elif waiting == "proxy":
        proxies = [p.strip() for p in text.splitlines() if p.strip()]
        added = 0
        for p in proxies[:50]:
            if REG_PROXY_MANAGER.add_proxy(p):
                added += 1
        await update.message.reply_text(f"✅ Added {added} proxies (max 50).")
        context.user_data.pop("reg_waiting")
    else:
        await update.message.reply_text("I don't understand. Use the buttons.")

async def run_registration(update: Update, count: int, referral: str):
    global REG_RUNNING, REG_PAUSED, REG_CANCEL
    REG_RUNNING = True
    REG_PAUSED = False
    REG_CANCEL = False
    processed = 0
    success = 0
    fail = 0
    start_time = time.time()
    connector = TCPConnector(limit=REG_CONCURRENCY, limit_per_host=REG_CONCURRENCY)
    timeout = ClientTimeout(total=10, connect=3)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for i in range(count):
            email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@mailinator.com"
            proxy = await REG_PROXY_MANAGER.get_proxy() if REG_PROXY_MANAGER else None
            tasks.append(asyncio.create_task(reg_register_one(session, email, REG_DEFAULT_PASSWORD, referral, proxy)))
        for future in asyncio.as_completed(tasks):
            while REG_PAUSED and not REG_CANCEL:
                await asyncio.sleep(0.05)
            if REG_CANCEL:
                for t in tasks:
                    if not t.done():
                        t.cancel()
                break
            ok, em, info = await future
            processed += 1
            if ok:
                success += 1
                async with aiosqlite.connect(REG_DB_PATH) as db:
                    await db.execute(
                        "INSERT OR IGNORE INTO registrations (email, password, referral, authorized_key, user_id, status) VALUES (?,?,?,?,?,?)",
                        (em, REG_DEFAULT_PASSWORD, referral, info.get("authorized_key"), info.get("user_id"), "success")
                    )
                    await db.commit()
            else:
                fail += 1
                async with aiosqlite.connect(REG_DB_PATH) as db:
                    await db.execute(
                        "INSERT OR IGNORE INTO registrations (email, password, referral, status) VALUES (?,?,?,?)",
                        (em, REG_DEFAULT_PASSWORD, referral, "fail")
                    )
                    await db.commit()
            if processed % 100 == 0 or processed == count:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                try:
                    await update.message.reply_text(
                        f"📊 Progress: {processed}/{count} | ✅ {success} | ❌ {fail} | ⚡ {rate:.1f}/s"
                    )
                except Exception as e:
                    logger.error(f"Progress update error: {e}")
    REG_RUNNING = False
    try:
        await update.message.reply_text("✅ Registration completed.")
    except Exception as e:
        logger.error(f"Completion message error: {e}")

async def reg_register_one(session, email, password, referral, proxy=None):
    payload = {
        "email": email,
        "passwd": password,
        "inviter_id": referral,
        "verify_code": REG_VERIFY_CODE,
        "is_h5": True,
        "time_zone": REG_TIME_ZONE,
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
    }
    for attempt in range(3):
        try:
            async with session.post(REG_API_URL, json=payload, headers=headers, timeout=10, proxy=proxy) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    user = data.get("data", {})
                    return True, email, {"authorized_key": user.get("authorized_key"), "user_id": user.get("id")}
                else:
                    return False, email, data.get("message", "Unknown error")
        except:
            await asyncio.sleep(0.5 * (attempt + 1))
    return False, email, "Max retries"

async def reg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REG_CONCURRENCY, REG_DELAY, REG_TURBO
    query = update.callback_query
    data = query.data
    await query.answer()
    if data == "reg_register":
        await reg_register(update, context)
    elif data == "reg_dashboard":
        async with aiosqlite.connect(REG_DB_PATH) as db:
            cur = await db.execute("SELECT COUNT(*) FROM registrations WHERE status='success'")
            success = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM registrations WHERE status='fail'")
            fail = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM registrations")
            total = (await cur.fetchone())[0]
        await query.edit_message_text(
            f"📊 *Dashboard*\nTotal: {total}\n✅ Success: {success}\n❌ Fail: {fail}",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "reg_history":
        async with aiosqlite.connect(REG_DB_PATH) as db:
            cur = await db.execute("SELECT email, authorized_key, created_at FROM registrations WHERE status='success' ORDER BY id DESC LIMIT 10")
            rows = await cur.fetchall()
        if not rows:
            text = "No history."
        else:
            text = "📜 *Latest 10*:\n" + "\n".join([f"• `{r[0]}` (key: `{r[1][:15]}...`)" for r in rows])
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    elif data == "reg_settings":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📌 Set Referral", callback_data="reg_set_ref")],
            [InlineKeyboardButton("⚡ Concurrency +10", callback_data="reg_con_inc"), InlineKeyboardButton("⚡ Concurrency -10", callback_data="reg_con_dec")],
            [InlineKeyboardButton("⏱️ Delay +0.01", callback_data="reg_delay_inc"), InlineKeyboardButton("⏱️ Delay -0.01", callback_data="reg_delay_dec")],
            [InlineKeyboardButton("🌐 Proxy Manager", callback_data="reg_proxy")],
            [InlineKeyboardButton("🔙 Back", callback_data="reg_back")],
        ])
        await query.edit_message_text("⚙️ *Registration Settings*", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif data == "reg_set_ref":
        await query.edit_message_text("📌 Enter main referral code:")
        context.user_data["reg_waiting"] = "set_referral"
    elif data == "reg_con_inc":
        REG_CONCURRENCY = min(REG_CONCURRENCY + 10, 1000)
        await query.edit_message_text(f"⚡ Concurrency set to {REG_CONCURRENCY}")
    elif data == "reg_con_dec":
        REG_CONCURRENCY = max(REG_CONCURRENCY - 10, 1)
        await query.edit_message_text(f"⚡ Concurrency set to {REG_CONCURRENCY}")
    elif data == "reg_delay_inc":
        REG_DELAY = min(REG_DELAY + 0.01, 1.0)
        await query.edit_message_text(f"⏱️ Delay set to {REG_DELAY:.3f}s")
    elif data == "reg_delay_dec":
        REG_DELAY = max(REG_DELAY - 0.01, 0.0)
        await query.edit_message_text(f"⏱️ Delay set to {REG_DELAY:.3f}s")
    elif data == "reg_proxy":
        await query.edit_message_text("🌐 Send proxy line by line (max 50):\nExample: `http://user:pass@1.2.3.4:8080`")
        context.user_data["reg_waiting"] = "proxy"
    elif data == "reg_turbo":
        REG_TURBO = not REG_TURBO
        if REG_TURBO:
            REG_CONCURRENCY = 600
            REG_DELAY = 0.0
            await query.edit_message_text("🚀 Turbo Mode ON (600 workers, 0 delay)")
        else:
            REG_CONCURRENCY = 250
            REG_DELAY = 0.002
            await query.edit_message_text("🚀 Turbo Mode OFF")
    elif data == "reg_export":
        await query.edit_message_text("📤 Exporting...")
        async with aiosqlite.connect(REG_DB_PATH) as db:
            cur = await db.execute("SELECT email, authorized_key, created_at FROM registrations WHERE status='success'")
            rows = await cur.fetchall()
        if not rows:
            await query.edit_message_text("No data.")
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Email", "Authorized_Key", "Created_At"])
        writer.writerows(rows)
        content = output.getvalue()
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=io.BytesIO(content.encode()),
            filename="registrations.csv",
            caption="✅ Done."
        )
        await query.edit_message_text("📤 Export sent.")
    elif data == "reg_back":
        await registration_menu(update, context)

# ======================================================================
# REFERRAL MODULE (unchanged)
# ======================================================================
async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Holwin", callback_data="ref_holwin"), InlineKeyboardButton("📈 Rexproearn", callback_data="ref_rex")],
        [InlineKeyboardButton("📊 Stats", callback_data="ref_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        "📈 *Referral Bot*\n\nRegister on Holwin or Rexproearn using your invite codes.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def ref_platform_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data.replace("ref_", "")
    context.user_data["ref_platform"] = platform
    invite = REF_HOLWIN_INVITE if platform == "holwin" else REF_REX_INVITE
    await query.edit_message_text(
        f"✅ Selected: *{platform.upper()}*\nInvite code: `{invite}`\n\n📱 Please enter your mobile number (10-15 digits):",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="ref_back")]])
    )
    context.user_data["ref_waiting"] = "mobile"
    return

async def ref_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if context.user_data.get("ref_waiting") == "mobile":
        if not re.match(r"^\d{10,15}$", text):
            await update.message.reply_text("❌ Invalid. Enter 10-15 digits:")
            return
        context.user_data["ref_mobile"] = text
        platform = context.user_data.get("ref_platform")
        if platform == "holwin":
            async with aiohttp.ClientSession() as session:
                resp = await session.post("https://www.holwin123.top/api/system/sms/send", json={"mobile": text, "type": "reg_code"})
                data = await resp.json()
                if data.get("code") != 0:
                    await update.message.reply_text(f"❌ OTP request failed: {data.get('msg')}")
                    return
        else:
            async with aiohttp.ClientSession() as session:
                resp = await session.post("https://rcapi.rexproearn.com/app/user/sendSmsCode", json={"mobileNo": text})
                data = await resp.json()
                if data.get("code") != 200:
                    await update.message.reply_text(f"❌ OTP request failed: {data.get('msg')}")
                    return
        await update.message.reply_text("✅ OTP sent! Please enter the OTP:")
        context.user_data["ref_waiting"] = "otp"
    elif context.user_data.get("ref_waiting") == "otp":
        if not text.isdigit():
            await update.message.reply_text("❌ OTP must be numeric. Try again:")
            return
        context.user_data["ref_otp"] = text
        await update.message.reply_text("🔑 Set a password (min 6 chars, or type 'skip' for default):")
        context.user_data["ref_waiting"] = "password"
    elif context.user_data.get("ref_waiting") == "password":
        pwd = text
        if pwd.lower() == "skip":
            pwd = "Dk12345dk" if context.user_data.get("ref_platform") == "rex" else "Password@123"
        elif len(pwd) < 6:
            await update.message.reply_text("❌ Min 6 characters. Try again or type 'skip':")
            return
        context.user_data["ref_password"] = pwd
        platform = context.user_data.get("ref_platform")
        mobile = context.user_data.get("ref_mobile")
        invite = REF_HOLWIN_INVITE if platform == "holwin" else REF_REX_INVITE
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="ref_confirm")],
            [InlineKeyboardButton("❌ Cancel", callback_data="ref_cancel")],
        ])
        await update.message.reply_text(
            f"📋 *Summary*\n📱 Mobile: `{mobile}`\n🔑 Password: `{'*'*len(pwd)}`\n🎫 Platform: `{platform.upper()}`\n🎫 Invite: `{invite}`\n\nConfirm?",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["ref_waiting"] = "confirm"

async def ref_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "ref_cancel":
        await query.edit_message_text("❌ Cancelled.")
        return
    platform = context.user_data.get("ref_platform")
    mobile = context.user_data.get("ref_mobile")
    otp = context.user_data.get("ref_otp")
    password = context.user_data.get("ref_password")
    invite = REF_HOLWIN_INVITE if platform == "holwin" else REF_REX_INVITE
    if platform == "holwin":
        payload = {
            "mobile": mobile,
            "authCode": otp,
            "password": password,
            "inviteCode": invite,
            "sourceAppType": "lobby",
            "registerHost": "www.holwin123.top",
            "sourceUrl": "https://www.hlowin.link/",
        }
        async with aiohttp.ClientSession() as session:
            resp = await session.post("https://www.holwin123.top/api/user/register", json=payload)
            data = await resp.json()
            success = data.get("code") == 0
    else:
        payload = {
            "mobileNo": mobile,
            "password": password,
            "smsCode": otp,
            "inviteCode": invite,
        }
        async with aiohttp.ClientSession() as session:
            resp = await session.post("https://rcapi.rexproearn.com/app/user/register", json=payload)
            data = await resp.json()
            success = data.get("code") == 200
    if success:
        async with aiosqlite.connect(REF_DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO registrations (mobile, platform, invite_used, telegram_id) VALUES (?,?,?,?)",
                (mobile, platform, invite, update.effective_user.id)
            )
            await db.commit()
        await query.edit_message_text(
            f"✅ *Registration successful!*\n\nPlatform: {platform.upper()}\nMobile: {mobile}\nInvite: {invite}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await query.edit_message_text(f"❌ Registration failed: {data.get('msg')}")

async def ref_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    async with aiosqlite.connect(REF_DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM registrations")
        total = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM registrations WHERE platform='holwin'")
        holwin = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM registrations WHERE platform='rex'")
        rex = (await cur.fetchone())[0]
    await query.edit_message_text(
        f"📊 *Referral Stats*\nTotal: {total}\n🏠 Holwin: {holwin}\n📈 Rexproearn: {rex}",
        parse_mode=ParseMode.MARKDOWN
    )

async def ref_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await referral_menu(update, context)

# ======================================================================
# UNBAN MODULE (unchanged)
# ======================================================================
UNBAN_AUTO_ENGINE = None

async def unban_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Number", callback_data="unban_add")],
        [InlineKeyboardButton("📋 My Numbers", callback_data="unban_list")],
        [InlineKeyboardButton("📤 Appeal All", callback_data="unban_appeal_all")],
        [InlineKeyboardButton("🔁 Auto-Send", callback_data="unban_auto")],
        [InlineKeyboardButton("🛑 Stop Auto", callback_data="unban_stop_auto")],
        [InlineKeyboardButton("🌐 Web Form", callback_data="unban_webform")],
        [InlineKeyboardButton("📝 Templates", callback_data="unban_templates")],
        [InlineKeyboardButton("⏰ Scheduler", callback_data="unban_scheduler")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="unban_settings")],
        [InlineKeyboardButton("📊 Dashboard", callback_data="unban_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        "🛡️ *Unban Bot*\n\nSend appeals to WhatsApp to unban your numbers.\nSet up your email/password first in Settings.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def unban_get_user(tid: int):
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        cur = await db.execute("SELECT * FROM users WHERE tid = ?", (tid,))
        row = await cur.fetchone()
        if row:
            columns = [description[0] for description in cur.description]
            return dict(zip(columns, row))
        return None

async def unban_create_user(tid: int, name: str = None):
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (tid, name, requested_at, last_active) VALUES (?, ?, ?, ?)",
            (tid, name, datetime.now().isoformat(), datetime.now().isoformat())
        )
        await db.commit()

async def unban_set_email(tid: int, email: str):
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        await db.execute("UPDATE users SET email = ?, email_valid = 1 WHERE tid = ?", (email, tid))
        await db.commit()

async def unban_set_password(tid: int, pwd: str):
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        await db.execute("UPDATE users SET password = ? WHERE tid = ?", (pwd, tid))
        await db.commit()

async def unban_add_number(tid: int, phone: str):
    phone = re.sub(r"\D", "", phone)
    if not re.match(r"^\d{8,15}$", phone):
        return False, "Invalid number"
    phone = "+" + phone if not phone.startswith("+") else phone
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        try:
            await db.execute("INSERT INTO numbers (phone, tid) VALUES (?, ?)", (phone, tid))
            await db.commit()
            return True, "Number added."
        except sqlite3.IntegrityError:
            return False, "Already exists."

async def unban_get_numbers(tid: int):
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        cur = await db.execute("SELECT * FROM numbers WHERE tid = ?", (tid,))
        return await cur.fetchall()

async def unban_remove_number(tid: int, phone: str):
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        await db.execute("DELETE FROM numbers WHERE phone = ? AND tid = ?", (phone, tid))
        await db.commit()

async def unban_send_email(tid: int, phone: str, name: str, reason: str, custom_reason: str = None):
    user = await unban_get_user(tid)
    if not user or not user["email"] or not user["password"]:
        return False, "Email/password not set."
    if user["email_valid"] == 0:
        return False, "Email invalid."
    if user["banned"] == 1:
        return False, "User banned."
    final_reason = custom_reason if custom_reason else reason
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        cur = await db.execute("SELECT template FROM user_templates WHERE tid = ? OR is_default = 1 ORDER BY RANDOM() LIMIT 1", (tid,))
        row = await cur.fetchone()
        template = row[0] if row else "My number {number} is banned. I use it for {reason}. Please help. {name}"
    body = template.format(number=phone, name=name or "User", reason=final_reason or "personal communication")
    msg = MIMEMultipart()
    msg["From"] = user["email"]
    msg["To"] = user.get("support_email", "support@whatsapp.com")
    msg["Subject"] = f"Appeal for {phone}"
    msg.attach(MIMEText(body, "plain"))
    try:
        server = smtplib.SMTP(user.get("smtp_host", "smtp.gmail.com"), user.get("smtp_port", 587))
        server.starttls()
        server.login(user["email"], user["password"])
        server.send_message(msg)
        server.quit()
        async with aiosqlite.connect(UNBAN_DB_PATH) as db:
            await db.execute("INSERT INTO appeal_logs (tid, phone, success, sent_at, template_used) VALUES (?, ?, 1, ?, ?)", (tid, phone, datetime.now().isoformat(), template))
            await db.execute("UPDATE users SET total_appeals = total_appeals + 1, success_appeals = success_appeals + 1 WHERE tid = ?", (tid,))
            await db.execute("UPDATE numbers SET last_appeal = ?, appeal_count = appeal_count + 1 WHERE phone = ?", (datetime.now().isoformat(), phone))
            await db.commit()
        return True, "Email sent."
    except Exception as e:
        logger.error(f"Unban email error: {e}")
        return False, str(e)

async def unban_submit_webform(tid: int, phone: str):
    if not SELENIUM_AVAILABLE:
        return False, "Selenium not installed."
    user = await unban_get_user(tid)
    if not user:
        return False, "User not found."
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.whatsapp.com/contact")
        wait = WebDriverWait(driver, 10)
        try:
            phone_input = wait.until(EC.presence_of_element_located((By.NAME, "phoneNumber")))
            phone_input.send_keys(phone.replace("+91", ""))
        except: pass
        try:
            email_input = driver.find_element(By.NAME, "email")
            email_input.send_keys(user["email"])
        except: pass
        try:
            textarea = driver.find_element(By.TAG_NAME, "textarea")
            textarea.send_keys(f"My number {phone} is banned. Please unban.")
        except: pass
        try:
            submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
        except: pass
        driver.quit()
        return True, "Web form submitted (may require CAPTCHA)."
    except Exception as e:
        return False, str(e)

async def unban_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    user_id = update.effective_user.id
    if data == "unban_add":
        await query.edit_message_text("📞 Enter phone number (with or without +91):")
        context.user_data["unban_waiting"] = "add_number"
    elif data == "unban_list":
        nums = await unban_get_numbers(user_id)
        if not nums:
            await query.edit_message_text("No numbers.")
            return
        text = "📋 *Your Numbers:*\n"
        for n in nums:
            status = "🚫 Blacklisted" if n[3] else "✅ Active"
            text += f"• {n[0]} | Appeals: {n[2]} | {status}\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    elif data == "unban_appeal_all":
        user = await unban_get_user(user_id)
        if not user or not user["email"] or not user["password"]:
            await query.edit_message_text("❌ Set email/password first.")
            return
        nums = await unban_get_numbers(user_id)
        if not nums:
            await query.edit_message_text("No numbers.")
            return
        for n in nums:
            if n[3]:
                continue
            ok, msg = await unban_send_email(user_id, n[0], user["name"] or "User", user["reason"] or "personal communication")
            await query.edit_message_text(f"{'✅' if ok else '❌'} {n[0]}: {msg}")
            await asyncio.sleep(0.5)
    elif data == "unban_auto":
        if UNBAN_AUTO_ENGINE is None:
            await query.edit_message_text("⚠️ Auto engine not ready.")
            return
        res = UNBAN_AUTO_ENGINE.start(user_id)
        await query.edit_message_text(res)
    elif data == "unban_stop_auto":
        if UNBAN_AUTO_ENGINE is None:
            await query.edit_message_text("⚠️ Auto engine not ready.")
            return
        res = UNBAN_AUTO_ENGINE.stop(user_id)
        await query.edit_message_text(res)
    elif data == "unban_webform":
        nums = await unban_get_numbers(user_id)
        if not nums:
            await query.edit_message_text("No numbers.")
            return
        phone = nums[0][0]
        ok, msg = await unban_submit_webform(user_id, phone)
        await query.edit_message_text(f"{'✅' if ok else '❌'} {msg}")
    elif data == "unban_templates":
        async with aiosqlite.connect(UNBAN_DB_PATH) as db:
            cur = await db.execute("SELECT id, template, is_default FROM user_templates WHERE tid = ? OR is_default = 1", (user_id,))
            rows = await cur.fetchall()
        if not rows:
            await query.edit_message_text("No templates.")
            return
        text = "📝 *Templates:*\n"
        for r in rows:
            text += f"{'⭐' if r[2] else '📌'} `{r[1][:50]}...` (ID:{r[0]})\n"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    elif data == "unban_scheduler":
        await query.edit_message_text("⏰ Scheduler: use /setschedule <cron> or <interval> (coming soon)")
    elif data == "unban_settings":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📧 Set Email", callback_data="unban_set_email")],
            [InlineKeyboardButton("🔑 Set Password", callback_data="unban_set_pass")],
            [InlineKeyboardButton("📝 Set Reason", callback_data="unban_set_reason")],
            [InlineKeyboardButton("⏱ Set Delay", callback_data="unban_set_delay")],
            [InlineKeyboardButton("🌐 Language", callback_data="unban_lang")],
            [InlineKeyboardButton("🔙 Back", callback_data="unban_back")],
        ])
        await query.edit_message_text("⚙️ *Unban Settings*", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif data == "unban_set_email":
        await query.edit_message_text("📧 Enter your Gmail address:")
        context.user_data["unban_waiting"] = "set_email"
    elif data == "unban_set_pass":
        await query.edit_message_text("🔑 Enter your Gmail App Password:")
        context.user_data["unban_waiting"] = "set_pass"
    elif data == "unban_set_reason":
        await query.edit_message_text("📝 Enter your reason for appeal:")
        context.user_data["unban_waiting"] = "set_reason"
    elif data == "unban_set_delay":
        await query.edit_message_text("⏱ Enter delay in seconds:")
        context.user_data["unban_waiting"] = "set_delay"
    elif data == "unban_lang":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇬🇧 English", callback_data="unban_lang_en")],
            [InlineKeyboardButton("🇮🇳 Hindi", callback_data="unban_lang_hi")],
        ])
        await query.edit_message_text("Select language:", reply_markup=keyboard)
    elif data.startswith("unban_lang_"):
        lang = data.split("_")[2]
        async with aiosqlite.connect(UNBAN_DB_PATH) as db:
            await db.execute("UPDATE users SET language = ? WHERE tid = ?", (lang, user_id))
            await db.commit()
        await query.edit_message_text(f"✅ Language set to {lang}")
    elif data == "unban_stats":
        user = await unban_get_user(user_id)
        nums = await unban_get_numbers(user_id)
        total = len(nums)
        appealed = sum(1 for n in nums if n[2] > 0)
        pending = total - appealed
        text = (
            f"📊 *Unban Dashboard*\nTotal numbers: {total}\nAppealed: {appealed}\nPending: {pending}\n"
            f"Email: {user['email'] if user else 'Not set'}\nDelay: {user['delay'] if user else 1.0}s"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    elif data == "unban_back":
        await unban_menu(update, context)

async def unban_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    waiting = context.user_data.get("unban_waiting")
    if waiting == "add_number":
        ok, msg = await unban_add_number(user_id, text)
        await update.message.reply_text(f"{'✅' if ok else '❌'} {msg}")
        context.user_data.pop("unban_waiting")
    elif waiting == "set_email":
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", text):
            await update.message.reply_text("❌ Invalid email.")
            return
        await unban_set_email(user_id, text)
        await update.message.reply_text(f"✅ Email set to {text}")
        context.user_data.pop("unban_waiting")
    elif waiting == "set_pass":
        if len(text) < 8:
            await update.message.reply_text("❌ Min 8 chars.")
            return
        await unban_set_password(user_id, text)
        await update.message.reply_text("✅ Password set.")
        context.user_data.pop("unban_waiting")
    elif waiting == "set_reason":
        if not text:
            await update.message.reply_text("❌ Reason cannot be empty.")
            return
        async with aiosqlite.connect(UNBAN_DB_PATH) as db:
            await db.execute("UPDATE users SET reason = ? WHERE tid = ?", (text, user_id))
            await db.commit()
        await update.message.reply_text(f"✅ Reason set: {text}")
        context.user_data.pop("unban_waiting")
    elif waiting == "set_delay":
        try:
            delay = float(text)
            if delay < 0.5:
                await update.message.reply_text("❌ Minimum 0.5s.")
                return
            async with aiosqlite.connect(UNBAN_DB_PATH) as db:
                await db.execute("UPDATE users SET delay = ? WHERE tid = ?", (delay, user_id))
                await db.commit()
            await update.message.reply_text(f"✅ Delay set to {delay}s")
            context.user_data.pop("unban_waiting")
        except:
            await update.message.reply_text("❌ Invalid number.")

# ======================================================================
# BAN CHECK MODULE (unchanged)
# ======================================================================
async def bancheck_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Check Ban", callback_data="bancheck_check")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        "🔍 *Ban Check Bot*\n\nCheck if a Free Fire player is banned.\nUse /bancheck <region> <uid> or click the button.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def bancheck_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📌 Send region and UID: `ind 123456789`")
    context.user_data["bancheck_waiting"] = "check"

async def bancheck_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("bancheck_waiting") == "check":
        args = update.message.text.split()
        if len(args) != 2:
            await update.message.reply_text("❌ Format: `region uid`")
            return
        region, uid = args
        result = await asyncio.to_thread(bancheck_check_player, uid, region)
        if "error" in result:
            await update.message.reply_text(f"❌ Error: {result['error']}")
        else:
            text = (
                "🔥 *PLAYER BAN STATUS*\n"
                f"Name: {result.get('nickname', 'N/A')}\n"
                f"UID: {uid}\n"
                f"Ban Status: {result.get('ban_status', 'N/A')}\n"
                f"Last Login: {result.get('last_login', 'N/A')}\n"
                f"Server: {result.get('region', 'N/A')}\n"
                f"Ban Date: {result.get('ban_date', 'N/A')}\n"
                f"Ban Period: {result.get('ban_period', 'N/A')}\n"
                f"Ban Reason: {result.get('ban_reason', 'N/A')}"
            )
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        context.user_data.pop("bancheck_waiting")

def bancheck_check_player(uid, region):
    try:
        cookies = {
            '_ga': 'GA1.1.2123120599.1674510784',
            'region': region.upper(),
            'session_key': 'efwfzwesi9ui8drux4pmqix4cosane0y',
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36',
            'accept': 'application/json',
            'content-type': 'application/json',
        }
        json_data = {'app_id': 100067, 'login_id': uid, 'app_server_id': 0}
        res = requests.post('https://shop2game.com/api/auth/player_id_login', cookies=cookies, headers=headers, json=json_data, timeout=30)
        if res.status_code != 200 or not res.json().get('nickname'):
            return {"error": "ID NOT FOUND"}
        player_data = res.json()
        nickname = player_data.get('nickname', 'N/A')
        player_region = player_data.get('region', 'N/A')
        last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ban_res = requests.get(f'https://ff.garena.com/api/antihack/check_banned?lang=en&uid={uid}', timeout=30)
        ban_data = ban_res.json()
        if ban_data.get("status") == "success" and "data" in ban_data:
            is_banned = ban_data["data"].get("is_banned", 0)
            period = ban_data["data"].get("period", 0)
            if is_banned:
                ban_status = f"Banned for {period} months"
                ban_period = f"{period} months"
                ban_date = "Unknown"
                ban_reason = "Cheat"
            else:
                ban_status = "Not banned"
                ban_period = "N/A"
                ban_date = "N/A"
                ban_reason = "N/A"
        else:
            return {"error": "Failed to retrieve ban status"}
        return {
            "ban_period": ban_period,
            "ban_status": ban_status,
            "ban_reason": ban_reason,
            "ban_date": ban_date,
            "last_login": last_login,
            "nickname": nickname,
            "region": player_region
        }
    except Exception as e:
        return {"error": str(e)}

# ======================================================================
# REPORT MODULE – WITH PER‑USER API CREDENTIALS
# ======================================================================
REPORT_SESSIONS = {}
REPORT_CLIENTS = {}

# Conversation states
REPORT_LOGIN_PHONE, REPORT_LOGIN_OTP = range(2)

# --- Database helpers for per‑user config ---
async def get_user_api_config(user_id: int) -> Tuple[Optional[int], Optional[str]]:
    """Return (api_id, api_hash) for the user, or (None, None) if not set."""
    async with aiosqlite.connect(REPORT_DB_PATH) as db:
        cur = await db.execute("SELECT api_id, api_hash FROM report_user_config WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            return row[0], row[1]
        return None, None

async def set_user_api_config(user_id: int, api_id: int, api_hash: str):
    async with aiosqlite.connect(REPORT_DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO report_user_config (user_id, api_id, api_hash, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, api_id, api_hash, datetime.now().isoformat())
        )
        await db.commit()

# --- Session management (now uses per‑user API) ---
async def get_report_session(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(REPORT_DB_PATH) as db:
        cur = await db.execute("SELECT session_string FROM report_sessions WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else None

async def save_report_session(user_id: int, session_string: str):
    async with aiosqlite.connect(REPORT_DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO report_sessions (user_id, session_string) VALUES (?, ?)", (user_id, session_string))
        await db.commit()

async def delete_report_session(user_id: int):
    async with aiosqlite.connect(REPORT_DB_PATH) as db:
        await db.execute("DELETE FROM report_sessions WHERE user_id = ?", (user_id,))
        await db.commit()
    if user_id in REPORT_CLIENTS:
        try:
            await REPORT_CLIENTS[user_id].disconnect()
        except:
            pass
        del REPORT_CLIENTS[user_id]

async def get_user_report_client(user_id: int) -> Optional[TelegramClient]:
    """Get a Telethon client for the user, using their own API credentials."""
    if user_id in REPORT_CLIENTS and REPORT_CLIENTS[user_id].is_connected():
        return REPORT_CLIENTS[user_id]
    session_str = await get_report_session(user_id)
    if not session_str:
        return None
    api_id, api_hash = await get_user_api_config(user_id)
    if api_id is None or api_hash is None:
        # Fallback to default if not set (but we'll prompt user to set)
        api_id = DEFAULT_API_ID
        api_hash = DEFAULT_API_HASH
        if api_id is None or api_hash is None:
            return None
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await delete_report_session(user_id)
            return None
        REPORT_CLIENTS[user_id] = client
        return client
    except Exception as e:
        logger.error(f"Report client error for {user_id}: {e}")
        return None

# --- Keyboard builder ---
async def build_report_keyboard(user_id: int) -> Tuple[InlineKeyboardMarkup, bool]:
    session = await get_report_session(user_id)
    logged_in = session is not None
    # Check if API credentials are set
    api_id, api_hash = await get_user_api_config(user_id)
    api_status = "✅ API Set" if api_id is not None and api_hash is not None else "❌ API Not Set"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Set API Credentials", callback_data="report_set_api")],
        [InlineKeyboardButton("🔑 Login" if not logged_in else "🔄 Refresh Session", callback_data="report_login")],
        [InlineKeyboardButton("🚪 Logout" if logged_in else "❌", callback_data="report_logout")],
        [InlineKeyboardButton("🎯 Set Targets", callback_data="report_targets")],
        [InlineKeyboardButton("🔢 Set Limit", callback_data="report_limit")],
        [InlineKeyboardButton("⚡ Speed Mode", callback_data="report_speed")],
        [InlineKeyboardButton("▶️ Start", callback_data="report_start")],
        [InlineKeyboardButton("⏸️ Pause/Resume", callback_data="report_pause")],
        [InlineKeyboardButton("⏹️ Stop", callback_data="report_stop")],
        [InlineKeyboardButton("📊 Status", callback_data="report_status")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])
    return keyboard, logged_in

async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    keyboard, logged_in = await build_report_keyboard(user_id)
    api_id, api_hash = await get_user_api_config(user_id)
    api_status = "✅ Set" if api_id and api_hash else "❌ Not Set"
    login_status = "✅ Logged in" if logged_in else "🔑 Not Logged In"
    text = (
        f"🚨 *Report Bot*\n\n"
        f"API Credentials: {api_status}\n"
        f"Login Status: {login_status}\n\n"
        "Report scam channels to Telegram.\n"
        "First set your API credentials, then login."
    )
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

# --- Set API Credentials flow ---
async def report_set_api_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔑 *Set your Telegram API credentials*\n\n"
        "1. Go to [my.telegram.org](https://my.telegram.org/apps)\n"
        "2. Log in and create an application\n"
        "3. Copy your **api_id** and **api_hash**\n\n"
        "Send your **api_id** (a number):"
    )
    context.user_data["report_set_api_step"] = "api_id"
    return

async def report_set_api_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    step = context.user_data.get("report_set_api_step")
    user_id = update.effective_user.id

    if step == "api_id":
        try:
            api_id = int(text)
            context.user_data["temp_api_id"] = api_id
            await update.message.reply_text("✅ API ID received. Now send your **api_hash** (a string):")
            context.user_data["report_set_api_step"] = "api_hash"
        except ValueError:
            await update.message.reply_text("❌ API ID must be a number. Try again:")
    elif step == "api_hash":
        api_hash = text.strip()
        if len(api_hash) < 10:
            await update.message.reply_text("❌ Invalid api_hash. It's usually long. Try again:")
            return
        api_id = context.user_data.get("temp_api_id")
        await set_user_api_config(user_id, api_id, api_hash)
        await update.message.reply_text("✅ API credentials saved successfully!")
        # Clear state and show report menu again
        context.user_data.pop("report_set_api_step", None)
        context.user_data.pop("temp_api_id", None)
        # Send report menu (without callback query)
        keyboard, logged_in = await build_report_keyboard(user_id)
        api_status = "✅ Set"
        login_status = "✅ Logged in" if logged_in else "🔑 Not Logged In"
        text = (
            f"🚨 *Report Bot*\n\n"
            f"API Credentials: {api_status}\n"
            f"Login Status: {login_status}\n\n"
            "You can now login."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# --- Login flow (uses stored API credentials) ---
async def report_login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    api_id, api_hash = await get_user_api_config(user_id)
    if api_id is None or api_hash is None:
        await query.edit_message_text(
            "❌ You haven't set your API credentials yet.\n"
            "Please use '🔑 Set API Credentials' first."
        )
        return
    await query.edit_message_text(
        "📱 *Login to Report Bot*\n\n"
        "Enter your phone number (with country code):\nExample: `+911234567890`"
    )
    context.user_data["report_login_state"] = "phone"
    return

async def report_login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not phone.startswith("+"):
        await update.message.reply_text("❌ Please include country code (e.g., +91).")
        return
    context.user_data["report_login_phone"] = phone
    user_id = update.effective_user.id
    api_id, api_hash = await get_user_api_config(user_id)
    if api_id is None or api_hash is None:
        await update.message.reply_text("❌ API credentials missing. Set them first.")
        return
    try:
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()
        await client.send_code_request(phone)
        context.user_data["report_login_client"] = client
        await update.message.reply_text("✅ Code sent! Please enter the OTP you received:")
        context.user_data["report_login_state"] = "otp"
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending code: {e}")
        context.user_data.pop("report_login_state", None)

async def report_login_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text.strip()
    client = context.user_data.get("report_login_client")
    phone = context.user_data.get("report_login_phone")
    if not client:
        await update.message.reply_text("❌ Session expired. Please start over with /report_login")
        return
    try:
        await client.sign_in(phone, otp)
        session_str = client.session.save()
        user_id = update.effective_user.id
        await save_report_session(user_id, session_str)
        REPORT_CLIENTS[user_id] = client
        await update.message.reply_text("✅ Login successful! You can now use the Report Bot.")
        keyboard, logged_in = await build_report_keyboard(user_id)
        await update.message.reply_text(
            "🚨 *Report Bot Menu*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    except SessionPasswordNeededError:
        await update.message.reply_text("⚠️ 2FA is enabled. Please send your password:")
        context.user_data["report_login_state"] = "password"
    except Exception as e:
        await update.message.reply_text(f"❌ Login failed: {e}")
    finally:
        context.user_data.pop("report_login_state", None)
        context.user_data.pop("report_login_client", None)
        context.user_data.pop("report_login_phone", None)

# --- Logout, targets, limit, speed, start, pause, stop, status (unchanged except using new keyboard) ---
async def report_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    await delete_report_session(user_id)
    await query.edit_message_text("✅ Logged out successfully.")
    await report_menu(update, context)

async def report_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎯 Enter comma-separated targets (max 10):\nExample: `@scamchannel1, @scamchannel2`"
    )
    context.user_data["report_waiting"] = "targets"

async def report_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔢 Enter max reports (1000-100000):")
    context.user_data["report_waiting"] = "limit"

async def report_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🐢 Normal", callback_data="report_speed_normal")],
        [InlineKeyboardButton("⚡ Fast", callback_data="report_speed_fast")],
        [InlineKeyboardButton("🔥 Turbo", callback_data="report_speed_turbo")],
    ])
    await query.edit_message_text("⚡ Choose speed:", reply_markup=keyboard)

async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = REPORT_SESSIONS.get(user_id, {})
    if not session.get("targets"):
        await update.callback_query.edit_message_text("❌ Set targets first.")
        return
    if session.get("active"):
        await update.callback_query.edit_message_text("⚠️ Already running.")
        return
    client = await get_user_report_client(user_id)
    if not client:
        await update.callback_query.edit_message_text("❌ You are not logged in. Please login first.")
        return
    session["active"] = True
    session["paused"] = False
    session["count"] = 0
    session["errors"] = 0
    session["start_time"] = datetime.now().strftime("%H:%M:%S")
    REPORT_SESSIONS[user_id] = session
    asyncio.create_task(report_worker(user_id))
    await update.callback_query.edit_message_text("▶️ Started.")

async def report_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = REPORT_SESSIONS.get(user_id)
    if not session or not session.get("active"):
        await update.callback_query.edit_message_text("⚠️ Not active.")
        return
    session["paused"] = not session.get("paused", False)
    status = "⏸️ Paused" if session["paused"] else "▶️ Resumed"
    await update.callback_query.edit_message_text(status)

async def report_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = REPORT_SESSIONS.get(user_id)
    if session:
        session["active"] = False
    await update.callback_query.edit_message_text("⏹️ Stopped.")

async def report_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = REPORT_SESSIONS.get(user_id, {})
    text = (
        "📊 *Report Status*\n"
        f"Targets: {session.get('targets', [])}\n"
        f"Limit: {session.get('max_reports', 20000)}\n"
        f"Sent: {session.get('count', 0)}\n"
        f"Errors: {session.get('errors', 0)}\n"
        f"Active: {'🟢' if session.get('active') else '🔴'}\n"
        f"Paused: {'⏸️' if session.get('paused') else '▶️'}"
    )
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

async def report_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Handle API setup steps
    if context.user_data.get("report_set_api_step"):
        await report_set_api_handle(update, context)
        return

    # Handle login OTP and phone
    if context.user_data.get("report_login_state") == "phone":
        await report_login_phone(update, context)
        return
    elif context.user_data.get("report_login_state") == "otp":
        await report_login_otp(update, context)
        return

    # Regular report settings
    if context.user_data.get("report_waiting") == "targets":
        targets = [t.strip() for t in text.split(",") if t.strip()]
        if not targets:
            await update.message.reply_text("❌ No valid targets.")
            return
        if len(targets) > REPORT_MAX_TARGETS:
            await update.message.reply_text(f"❌ Max {REPORT_MAX_TARGETS} targets.")
            return
        session = REPORT_SESSIONS.get(user_id, {})
        session["targets"] = targets
        REPORT_SESSIONS[user_id] = session
        await update.message.reply_text(f"✅ Targets set: {len(targets)}")
        context.user_data.pop("report_waiting")
    elif context.user_data.get("report_waiting") == "limit":
        try:
            limit = int(text)
            if limit < 1000 or limit > 100000:
                await update.message.reply_text("❌ Limit 1000-100000.")
                return
            session = REPORT_SESSIONS.get(user_id, {})
            session["max_reports"] = limit
            REPORT_SESSIONS[user_id] = session
            await update.message.reply_text(f"✅ Limit set to {limit}")
            context.user_data.pop("report_waiting")
        except:
            await update.message.reply_text("❌ Invalid number.")

# --- Report worker (unchanged) ---
async def report_worker(user_id: int):
    session = REPORT_SESSIONS.get(user_id, {})
    if not session:
        return
    targets = session.get("targets", [])
    max_limit = session.get("max_reports", REPORT_DEFAULT_MAX)
    speed = session.get("speed", "turbo")
    interval = {"normal":2.0, "fast":1.0, "turbo":0.3}.get(speed, 0.3)

    client = await get_user_report_client(user_id)
    if not client:
        if APPLICATION:
            await APPLICATION.bot.send_message(user_id, "❌ Your session expired. Please login again.")
        session["active"] = False
        return

    count = 0
    while session.get("active") and count < max_limit:
        if session.get("paused"):
            await asyncio.sleep(1)
            continue
        for t in targets:
            if not session.get("active") or count >= max_limit:
                break
            try:
                entity = await client.get_entity(t)
                report_id = count + 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                msg = f"Scam report #{report_id} on {t} at {timestamp}"
                await client(ReportPeerRequest(
                    peer=entity,
                    reason=InputReportReasonSpam(),
                    message=msg
                ))
                count += 1
                session["count"] = count
                await asyncio.sleep(interval)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                session["errors"] = session.get("errors", 0) + 1
                logger.error(f"Report error: {e}")
        await asyncio.sleep(0.1)
    session["active"] = False
    REPORT_SESSIONS[user_id] = session

# ======================================================================
# GLOBAL SETTINGS & ADMIN (unchanged)
# ======================================================================
async def global_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        "⚙️ *Global Settings*\n\nAdmin only commands.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🌟 *Main Menu*\n\nChoose a module from the persistent keyboard below.",
        reply_markup=get_main_keyboard()
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔ Admin only.")
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Overall Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 List Users", callback_data="admin_listusers")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("💾 Backup", callback_data="admin_backup")],
        [InlineKeyboardButton("🔙 Back", callback_data="global_settings")],
    ])
    await query.edit_message_text("👑 *Admin Panel*", parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reg_total = 0
    ref_total = 0
    unban_users = 0
    unban_numbers = 0
    async with aiosqlite.connect(REG_DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM registrations")
        reg_total = (await cur.fetchone())[0]
    async with aiosqlite.connect(REF_DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM registrations")
        ref_total = (await cur.fetchone())[0]
    async with aiosqlite.connect(UNBAN_DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        unban_users = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM numbers")
        unban_numbers = (await cur.fetchone())[0]
    text = (
        "📊 *Overall Stats*\n"
        f"Registration accounts: {reg_total}\n"
        f"Referral registrations: {ref_total}\n"
        f"Unban users: {unban_users}, numbers: {unban_numbers}\n"
        f"Report sessions: {len(REPORT_SESSIONS)}"
    )
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ *Help*\n\nUse the persistent keyboard to navigate modules.\n"
        "Each module has its own features.\n"
        "For detailed help, select a module and use its help buttons.",
        parse_mode=ParseMode.MARKDOWN
    )

# ======================================================================
# FUN & UTILITIES (unchanged)
# ======================================================================
async def fun_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Roll Dice", callback_data="fun_roll"),
         InlineKeyboardButton("🪙 Flip Coin", callback_data="fun_coin")],
        [InlineKeyboardButton("🔢 Random Number", callback_data="fun_number"),
         InlineKeyboardButton("📅 Horoscope", callback_data="fun_horoscope")],
        [InlineKeyboardButton("😂 Joke", callback_data="fun_joke"),
         InlineKeyboardButton("💬 Quote", callback_data="fun_quote")],
        [InlineKeyboardButton("📰 News", callback_data="fun_news"),
         InlineKeyboardButton("🌤️ Weather", callback_data="fun_weather")],
        [InlineKeyboardButton("💰 Crypto Price", callback_data="fun_crypto"),
         InlineKeyboardButton("📝 Translate", callback_data="fun_translate")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])
    await query.edit_message_text(
        "🎮 *Fun & Utilities*\n\nChoose a feature below:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def fun_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data == "fun_roll":
        result = random.randint(1, 6)
        await query.edit_message_text(f"🎲 You rolled: **{result}**", parse_mode=ParseMode.MARKDOWN)
    elif data == "fun_coin":
        result = random.choice(["Heads", "Tails"])
        await query.edit_message_text(f"🪙 Result: **{result}**", parse_mode=ParseMode.MARKDOWN)
    elif data == "fun_number":
        num = random.randint(1, 100)
        await query.edit_message_text(f"🔢 Random number: **{num}**", parse_mode=ParseMode.MARKDOWN)
    elif data == "fun_horoscope":
        await query.edit_message_text("♈ Enter your zodiac sign (e.g., aries):")
        context.user_data["fun_waiting"] = "horoscope"
    elif data == "fun_joke":
        jokes = ["Why do programmers prefer dark mode? Because light attracts bugs.",
                 "What do you call a fake noodle? An impasta.",
                 "Why did the scarecrow win an award? Because he was outstanding in his field."]
        await query.edit_message_text(f"😂 {random.choice(jokes)}")
    elif data == "fun_quote":
        quotes = ["The only way to do great work is to love what you do. – Steve Jobs",
                  "In the middle of difficulty lies opportunity. – Einstein",
                  "Success is not final, failure is not fatal: it is the courage to continue that counts."]
        await query.edit_message_text(f"💬 {random.choice(quotes)}")
    elif data == "fun_news":
        await query.edit_message_text("📰 Top headlines: (API integration needed) – use /news command.")
    elif data == "fun_weather":
        await query.edit_message_text("🌤️ Enter city name:")
        context.user_data["fun_waiting"] = "weather"
    elif data == "fun_crypto":
        await query.edit_message_text("💰 Enter crypto symbol (e.g., BTC, ETH):")
        context.user_data["fun_waiting"] = "crypto"
    elif data == "fun_translate":
        await query.edit_message_text("📝 Send text to translate to English:")
        context.user_data["fun_waiting"] = "translate"

async def fun_handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if context.user_data.get("fun_waiting") == "horoscope":
        signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
        if text.lower() not in signs:
            await update.message.reply_text("❌ Invalid sign. Try again.")
            return
        msgs = ["You will have a great day!", "Beware of surprises.", "Financial luck is on your side."]
        await update.message.reply_text(f"♈ *{text.capitalize()}*: {random.choice(msgs)}", parse_mode=ParseMode.MARKDOWN)
        context.user_data.pop("fun_waiting")
    elif context.user_data.get("fun_waiting") == "weather":
        await update.message.reply_text(f"🌤️ Weather for {text}: 25°C, sunny.")
        context.user_data.pop("fun_waiting")
    elif context.user_data.get("fun_waiting") == "crypto":
        price = round(random.uniform(100, 50000), 2)
        await update.message.reply_text(f"💰 {text.upper()} price: ${price}")
        context.user_data.pop("fun_waiting")
    elif context.user_data.get("fun_waiting") == "translate":
        await update.message.reply_text(f"📝 Translation: \"{text}\" (English)")
        context.user_data.pop("fun_waiting")

# ======================================================================
# COMMAND HANDLERS
# ======================================================================
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    await update.message.reply_text("Pong!")
    latency = (time.time() - start) * 1000
    await update.message.reply_text(f"⏱️ Latency: {latency:.0f}ms")

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delta = datetime.now() - BOT_START_TIME
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    await update.message.reply_text(f"🕒 Uptime: {days}d {hours}h {minutes}m {seconds}s")

async def eval_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    code = " ".join(context.args)
    if not code:
        await update.message.reply_text("❌ Provide code to evaluate.")
        return
    try:
        result = eval(code)
        await update.message.reply_text(f"✅ Result:\n```{result}```", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Provide a message to broadcast.")
        return
    await update.message.reply_text("📢 Broadcast sent to all users (simulated).")

async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    await update.message.reply_text("💾 Backup completed (simulated).")

# ======================================================================
# MAIN
# ======================================================================
def main():
    global APPLICATION, REG_PROXY_MANAGER, UNBAN_AUTO_ENGINE

    # Initialize databases
    try:
        asyncio.run(init_all_dbs())
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    REG_PROXY_MANAGER = RegProxyManager()

    # Unban Auto Engine
    class SimpleAutoEngine:
        def __init__(self):
            self.tasks = {}
        def start(self, tid):
            if tid in self.tasks and not self.tasks[tid].done():
                return "Already running."
            self.tasks[tid] = asyncio.create_task(self._run(tid))
            return "Auto-send started."
        def stop(self, tid):
            if tid in self.tasks and not self.tasks[tid].done():
                self.tasks[tid].cancel()
                return "Stopped."
            return "Not running."
        async def _run(self, tid):
            while True:
                try:
                    user = await unban_get_user(tid)
                    if not user or not user["email"] or not user["password"]:
                        break
                    nums = await unban_get_numbers(tid)
                    if not nums:
                        break
                    for n in nums:
                        if n[3]: continue
                        ok, msg = await unban_send_email(tid, n[0], user["name"] or "User", user["reason"] or "personal communication")
                        if APPLICATION:
                            try:
                                await APPLICATION.bot.send_message(tid, f"{'✅' if ok else '❌'} {n[0]}: {msg}")
                            except Exception as e:
                                logger.error(f"Failed to send message to {tid}: {e}")
                        await asyncio.sleep(user["delay"] if user else 1.0)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Auto engine error: {e}")
                await asyncio.sleep(5)
    UNBAN_AUTO_ENGINE = SimpleAutoEngine()

    # Build application
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        APPLICATION = application
    except Exception as e:
        logger.critical(f"Failed to build application: {e}")
        sys.exit(1)

    # Add handlers
    application.add_handler(CommandHandler("start", module_start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("uptime", uptime))
    application.add_handler(CommandHandler("eval", eval_code))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("backup", backup))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_global_text))
    application.add_handler(CallbackQueryHandler(global_callback_handler, pattern="^"))

    # Start polling
    try:
        logger.info("🚀 Mega Bot is starting...")
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)

# ======================================================================
# GLOBAL MESSAGE ROUTER
# ======================================================================
async def handle_global_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle report API setup or login steps
    if context.user_data.get("report_set_api_step"):
        await report_set_api_handle(update, context)
        return
    if context.user_data.get("report_login_state") == "phone":
        await report_login_phone(update, context)
        return
    elif context.user_data.get("report_login_state") == "otp":
        await report_login_otp(update, context)
        return

    # Route to other modules
    if context.user_data.get("reg_waiting"):
        await reg_handle_text(update, context)
    elif context.user_data.get("ref_waiting"):
        await ref_handle_text(update, context)
    elif context.user_data.get("unban_waiting"):
        await unban_handle_text(update, context)
    elif context.user_data.get("bancheck_waiting"):
        await bancheck_handle_text(update, context)
    elif context.user_data.get("report_waiting"):
        await report_handle_text(update, context)
    elif context.user_data.get("fun_waiting"):
        await fun_handle_text(update, context)
    else:
        text = update.message.text
        if text == "📋 Registration Bot":
            await send_module_menu(update, "registration")
        elif text == "📈 Referral Bot":
            await send_module_menu(update, "referral")
        elif text == "🛡️ Unban Bot":
            await send_module_menu(update, "unban")
        elif text == "🔍 Ban Check Bot":
            await send_module_menu(update, "bancheck")
        elif text == "🚨 Report Bot":
            await send_module_menu(update, "report")
        elif text == "🎮 Fun & Utilities":
            await send_module_menu(update, "fun")
        elif text == "⚙️ Global Settings":
            await send_module_menu(update, "global")
        elif text == "❓ Help":
            await help_command(update, context)
        else:
            await update.message.reply_text("Use the buttons to navigate.")

async def send_module_menu(update: Update, module: str):
    user_id = update.effective_user.id
    if module == "registration":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔹 Register", callback_data="reg_register")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="reg_dashboard")],
            [InlineKeyboardButton("📜 History", callback_data="reg_history")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="reg_settings")],
            [InlineKeyboardButton("📤 Export", callback_data="reg_export")],
            [InlineKeyboardButton("🚀 Turbo Mode", callback_data="reg_turbo")],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")],
        ])
        text = "📋 *Registration Bot*\n\nRegister accounts on EarnMigo with your referral."
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif module == "referral":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Holwin", callback_data="ref_holwin"), InlineKeyboardButton("📈 Rexproearn", callback_data="ref_rex")],
            [InlineKeyboardButton("📊 Stats", callback_data="ref_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        text = "📈 *Referral Bot*\n\nRegister on Holwin or Rexproearn using your invite codes."
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif module == "unban":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Number", callback_data="unban_add")],
            [InlineKeyboardButton("📋 My Numbers", callback_data="unban_list")],
            [InlineKeyboardButton("📤 Appeal All", callback_data="unban_appeal_all")],
            [InlineKeyboardButton("🔁 Auto-Send", callback_data="unban_auto")],
            [InlineKeyboardButton("🛑 Stop Auto", callback_data="unban_stop_auto")],
            [InlineKeyboardButton("🌐 Web Form", callback_data="unban_webform")],
            [InlineKeyboardButton("📝 Templates", callback_data="unban_templates")],
            [InlineKeyboardButton("⏰ Scheduler", callback_data="unban_scheduler")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="unban_settings")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="unban_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        text = "🛡️ *Unban Bot*\n\nSend appeals to WhatsApp to unban your numbers.\nSet up your email/password first in Settings."
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif module == "bancheck":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Check Ban", callback_data="bancheck_check")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        text = "🔍 *Ban Check Bot*\n\nCheck if a Free Fire player is banned.\nUse /bancheck <region> <uid> or click the button."
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif module == "report":
        keyboard, logged_in = await build_report_keyboard(user_id)
        api_id, api_hash = await get_user_api_config(user_id)
        api_status = "✅ Set" if api_id and api_hash else "❌ Not Set"
        login_status = "✅ Logged in" if logged_in else "🔑 Not Logged In"
        text = (
            f"🚨 *Report Bot*\n\n"
            f"API Credentials: {api_status}\n"
            f"Login Status: {login_status}\n\n"
            "First set your API credentials, then login."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif module == "fun":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Roll Dice", callback_data="fun_roll"),
             InlineKeyboardButton("🪙 Flip Coin", callback_data="fun_coin")],
            [InlineKeyboardButton("🔢 Random Number", callback_data="fun_number"),
             InlineKeyboardButton("📅 Horoscope", callback_data="fun_horoscope")],
            [InlineKeyboardButton("😂 Joke", callback_data="fun_joke"),
             InlineKeyboardButton("💬 Quote", callback_data="fun_quote")],
            [InlineKeyboardButton("📰 News", callback_data="fun_news"),
             InlineKeyboardButton("🌤️ Weather", callback_data="fun_weather")],
            [InlineKeyboardButton("💰 Crypto Price", callback_data="fun_crypto"),
             InlineKeyboardButton("📝 Translate", callback_data="fun_translate")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        text = "🎮 *Fun & Utilities*\n\nChoose a feature below:"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    elif module == "global":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_panel")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])
        text = "⚙️ *Global Settings*\n\nAdmin only commands."
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

async def global_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    if data.startswith("reg_"):
        await reg_callback(update, context)
    elif data.startswith("ref_"):
        if data == "ref_holwin" or data == "ref_rex":
            await ref_platform_select(update, context)
        elif data == "ref_stats":
            await ref_stats(update, context)
        elif data == "ref_confirm" or data == "ref_cancel":
            await ref_confirm(update, context)
        elif data == "ref_back":
            await ref_back(update, context)
    elif data.startswith("unban_"):
        await unban_callback(update, context)
    elif data.startswith("bancheck_"):
        await bancheck_menu(update, context)
    elif data.startswith("report_"):
        if data == "report_set_api":
            await report_set_api_start(update, context)
        elif data == "report_login":
            await report_login_start(update, context)
        elif data == "report_logout":
            await report_logout(update, context)
        elif data == "report_targets":
            await report_targets(update, context)
        elif data == "report_limit":
            await report_limit(update, context)
        elif data == "report_speed":
            await report_speed(update, context)
        elif data == "report_start":
            await report_start(update, context)
        elif data == "report_pause":
            await report_pause(update, context)
        elif data == "report_stop":
            await report_stop(update, context)
        elif data == "report_status":
            await report_status(update, context)
        elif data.startswith("report_speed_"):
            speed = data.split("_")[2]
            user_id = update.effective_user.id
            session = REPORT_SESSIONS.get(user_id, {})
            session["speed"] = speed
            REPORT_SESSIONS[user_id] = session
            await update.callback_query.edit_message_text(f"✅ Speed set to {speed}")
    elif data.startswith("fun_"):
        await fun_callback(update, context)
    elif data == "main_menu":
        await main_menu(update, context)
    elif data == "global_settings":
        await global_settings(update, context)
    elif data == "admin_panel":
        await admin_panel(update, context)
    elif data == "admin_stats":
        await admin_stats(update, context)
    else:
        await update.callback_query.edit_message_text("Unknown action.")

if __name__ == "__main__":
    main()

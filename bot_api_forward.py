#!/usr/bin/env python3

from dotenv import load_dotenv
load_dotenv()

import os
import json
import pytz
import tzlocal
from telethon import TelegramClient, events
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ─── Monkey‐patch tzlocal to use pytz UTC ─────────────────────────────────────
tzlocal.get_localzone = lambda: pytz.UTC

# ─── Load environment variables ───────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")
T_API_ID = int(os.getenv("API_ID", "0"))
T_API_HASH = os.getenv("API_HASH")

# ─── Settings storage ────────────────────────────────────────────────────────
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def load_all_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    defaults = {}
    with open(SETTINGS_FILE, "w") as f:
        json.dump(defaults, f)
    return defaults

def save_all_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

all_settings = load_all_settings()

# ─── Initialize Telethon client ─────────────────────────────────────────────
TCLIENT = TelegramClient("filter", T_API_ID, T_API_HASH)

# ─── Initialize python-telegram-bot application ─────────────────────────────
app = ApplicationBuilder().token(BOT_TOKEN).build()

# ─── Command handlers to configure forwarding ────────────────────────────────
async def set_src(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = str(update.effective_chat.id)
    cfg = all_settings.setdefault(chat, {})
    cfg["src_channel"] = int(context.args[0])
    save_all_settings(all_settings)
    await update.message.reply_text(f"✅ Source channel set to {cfg['src_channel']}")

async def set_dst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = str(update.effective_chat.id)
    cfg = all_settings.setdefault(chat, {})
    cfg["dst_channel"] = int(context.args[0])
    save_all_settings(all_settings)
    await update.message.reply_text(f"✅ Destination channel set to {cfg['dst_channel']}")

async def set_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = str(update.effective_chat.id)
    cfg = all_settings.setdefault(chat, {})
    cfg["from_id"] = int(context.args[0])
    save_all_settings(all_settings)
    await update.message.reply_text(f"✅ Forward-from user set to {cfg['from_id']}")

async def set_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = str(update.effective_chat.id)
    cfg = all_settings.setdefault(chat, {})
    cfg["to_id"] = int(context.args[0])
    save_all_settings(all_settings)
    await update.message.reply_text(f"✅ Forward-to user set to {cfg['to_id']}")

async def check_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = str(update.effective_chat.id)
    cfg = all_settings.get(chat, {})
    missing = [k for k in ("src_channel","dst_channel","from_id","to_id") if cfg.get(k) is None]
    if missing:
        await update.message.reply_text(f"⚠️ Missing settings: {', '.join(missing)}")
    else:
        await update.message.reply_text("✅ All settings are configured correctly.")

# Register commands
app.add_handler(CommandHandler("setsrc", set_src))
app.add_handler(CommandHandler("setdst", set_dst))
app.add_handler(CommandHandler("setfrom", set_from))
app.add_handler(CommandHandler("setto", set_to))
app.add_handler(CommandHandler("checksettings", check_settings))

# ─── Telethon event listener for forwarding ─────────────────────────────────
@TCLIENT.on(events.NewMessage())
async def forward_event(event):
    for chat, cfg in all_settings.items():
        if (event.chat_id == cfg.get("src_channel") and
            event.sender_id == cfg.get("from_id")):
            await TCLIENT.send_message(cfg.get("dst_channel"), event.message)
            break

# ─── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start Telethon (synchronous wrapper)
    TCLIENT.start(bot_token=BOT_TOKEN)

    # Start Telegram Bot polling
    app.run_polling()

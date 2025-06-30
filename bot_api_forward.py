#!/usr/bin/env python3
import os
import json
import asyncio
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
load_dotenv()

# Path to settings.json
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Default settings template
DEFAULTS = {
    "src_channel": None,    # numeric chat_id, e.g. -1001234567890
    "dst_channel": None,    # numeric chat_id
    "from_id":    None,     # integer message_id
    "to_id":      None,     # integer message_id
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *ForwardBot* ready!\n\n"
        "Use /settings to view or update:\n"
        "`/setsrc <chat_id>`\n"
        "`/setdst <chat_id>`\n"
        "`/setrange <from_id> <to_id>`\n"
        "Then `/forward` to begin.",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = load_settings()
    text = (
        "*Current Settings*\n"
        f"- Source chat_id: `{s['src_channel']}`\n"
        f"- Destination chat_id: `{s['dst_channel']}`\n"
        f"- Range: `{s['from_id']} → {s['to_id']}`\n\n"
        "Use `/setsrc`, `/setdst`, `/setrange` to update."
    )
    await update.message.reply_text(text, parse_mode=constants.ParseMode.MARKDOWN)

async def setsrc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].lstrip("-").isdigit():
        return await update.message.reply_text(
            "Usage: `/setsrc <numeric_chat_id>`",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    s = load_settings()
    s["src_channel"] = int(context.args[0])
    save_settings(s)
    await update.message.reply_text(
        f"✅ Source chat_id set to `{s['src_channel']}`",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def setdst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].lstrip("-").isdigit():
        return await update.message.reply_text(
            "Usage: `/setdst <numeric_chat_id>`",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    s = load_settings()
    s["dst_channel"] = int(context.args[0])
    save_settings(s)
    await update.message.reply_text(
        f"✅ Destination chat_id set to `{s['dst_channel']}`",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def setrange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2 or not all(arg.isdigit() for arg in context.args):
        return await update.message.reply_text(
            "Usage: `/setrange <from_id> <to_id>`",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    frm, to = map(int, context.args)
    if frm > to:
        return await update.message.reply_text(
            "⚠️ `from_id` must be ≤ `to_id`.",
            parse_mode=constants.ParseMode.MARKDOWN
        )
    s = load_settings()
    s["from_id"], s["to_id"] = frm, to
    save_settings(s)
    await update.message.reply_text(
        f"✅ Range set: `{frm}` → `{to}`",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def forward_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = load_settings()
    if not all([s["src_channel"], s["dst_channel"], s["from_id"], s["to_id"]]):
        return await update.message.reply_text(
            "⚠️ Please configure all settings first with `/settings`.",
            parse_mode=constants.ParseMode.MARKDOWN
        )

    total = s["to_id"] - s["from_id"] + 1
    done = 0
    prog = await update.message.reply_text(f"🚀 Forwarding 0 / {total}")

    for mid in range(s["from_id"], s["to_id"] + 1):
        try:
            await context.bot.forward_message(
                chat_id=s["dst_channel"],
                from_chat_id=s["src_channel"],
                message_id=mid,
            )
        except:
            pass
        done += 1
        if done % 5 == 0 or done == total:
            await prog.edit_text(f"🚀 Forwarding {done} / {total}")
        await asyncio.sleep(0.1)

    await prog.edit_text(f"✅ Done! Forwarded {done} messages.")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN env var is required")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("setsrc",   setsrc))
    app.add_handler(CommandHandler("setdst",   setdst))
    app.add_handler(CommandHandler("setrange", setrange))
    app.add_handler(CommandHandler("forward",  forward_cmd))

    print("🔗 Bot-API forwarder is up!")
    app.run_polling()

if __name__ == "__main__":
    main()

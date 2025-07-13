#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os, json, asyncio, pytz, tzlocal
from telegram import constants, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import logging
from telethon.errors import FloodWaitError
from telegram.error import RetryAfter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

# ─── Telethon client setup ───────────────────────────────────────────────────
from telethon import TelegramClient

API_ID   = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
# session name 'forwardbot.session' will be created locally
TCLIENT = TelegramClient('forwardbot.session', API_ID, API_HASH)
# start Telethon sync before polling
TCLIENT.start(bot_token=os.getenv("BOT_TOKEN"))

# ─── Monkey-patch tzlocal to use pytz UTC ──────────────────────────────────
tzlocal.get_localzone = lambda: pytz.UTC

# ─── File where we store *all* users’ settings ──────────────────────────────
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

# Template for one user’s settings
USER_DEFAULTS = {
    "src_channel": None,    # numeric chat_id, e.g. -1001234567890
    "dst_channel": None,    # numeric chat_id
    "from_id":    None,     # integer
    "to_id":      None,     # integer
    "forward":    False,     # ← new flag: False = copy, True = forward
}

def load_all_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({}, f, indent=2)
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_all_settings(all_settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(all_settings, f, indent=2)

def get_user_settings(user_id: int):
    all_s = load_all_settings()
    return all_s.get(str(user_id), USER_DEFAULTS.copy())

def set_user_settings(user_id: int, user_s: dict):
    all_s = load_all_settings()
    all_s[str(user_id)] = user_s
    save_all_settings(all_s)

# ─── Handlers ──────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>Advance ForwardBot</b>!\n\n"
        "I’ll help you forward documents & videos from one channel to another.\n\n"
        "<b>How to use</b>:\n"
        "1️⃣ <code>/setsrc &lt;chat_id&gt;</code>\n"
        "   • Choose the source channel (where I’ll pull messages from).\n\n"
        "2️⃣ <code>/setdst &lt;chat_id&gt;</code>\n"
        "   • Choose the destination channel (where I’ll copy messages to).\n\n"
        "3️⃣ <code>/setrange &lt;from_id&gt; &lt;to_id&gt;</code>\n"
        "   • Specify the message ID range you want to forward (e.g. 100 to 200).\n\n"
        "4️⃣ <code>/forward</code>\n"
        "   • I’ll process every ID in your range, copy only documents & videos, and skip everything else.\n\n"
        "<b>Example</b>:\n"
        "<code>/setsrc -1276473254378</code>  \n"
        "<code>/setdst -78124723t4237</code>  \n"
        "<code>/setrange 50 150</code>        \n"
        "<code>/forward</code>                \n\n"
        "⚙️ Need to check your settings? Use <code>/settings</code>\n"
        "<b>❓ Contact @THe_vK_3 if any problem or Query</b>",
        parse_mode=constants.ParseMode.HTML
    )

async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    s   = get_user_settings(uid)
    await update.message.reply_text(
        "<b>Your Settings</b>\n"
        f"• Source chat_id: <code>{s['src_channel']}</code>\n"
        f"• Destination chat_id: <code>{s['dst_channel']}</code>\n"
        f"• Range: <code>{s['from_id']} → {s['to_id']}</code>",
        parse_mode=constants.ParseMode.HTML
    )

async def setsrc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if len(context.args) != 1 or not context.args[0].lstrip("-").isdigit():
        return await update.message.reply_text(
            "Usage: <code>/setsrc &lt;numeric_chat_id&gt;</code>",
            parse_mode=constants.ParseMode.HTML
        )
    s = get_user_settings(uid)
    s["src_channel"] = int(context.args[0])
    set_user_settings(uid, s)
    await update.message.reply_text(
        f"✅ Source chat_id set to <code>{s['src_channel']}</code>",
        parse_mode=constants.ParseMode.HTML
    )

async def setdst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if len(context.args) != 1 or not context.args[0].lstrip("-").isdigit():
        return await update.message.reply_text(
            "Usage: <code>/setdst &lt;numeric_chat_id&gt;</code>",
            parse_mode=constants.ParseMode.HTML
        )
    s = get_user_settings(uid)
    s["dst_channel"] = int(context.args[0])
    set_user_settings(uid, s)
    await update.message.reply_text(
        f"✅ Destination chat_id set to <code>{s['dst_channel']}</code>",
        parse_mode=constants.ParseMode.HTML
    )

async def setrange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if len(context.args) != 2 or not all(arg.isdigit() for arg in context.args):
        return await update.message.reply_text(
            "Usage: <code>/setrange &lt;from_id&gt; &lt;to_id&gt;</code>",
            parse_mode=constants.ParseMode.HTML
        )
    frm, to = map(int, context.args)
    if frm > to:
        return await update.message.reply_text(
            "⚠️ <code>from_id</code> must be ≤ <code>to_id</code>.",
            parse_mode=constants.ParseMode.HTML
        )
    s = get_user_settings(uid)
    s["from_id"], s["to_id"] = frm, to
    set_user_settings(uid, s)
    await update.message.reply_text(
        f"✅ Range set: <code>{frm} → {to}</code>",
        parse_mode=constants.ParseMode.HTML
    )


async def foption_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
      [
        InlineKeyboardButton("Yes (show header)", callback_data="fopt_yes"),
        InlineKeyboardButton("No (hide header)",   callback_data="fopt_no"),
      ]
    ]
    await update.message.reply_text(
        "🔀 Do you want to **forward** with a header or **copy** without it?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=constants.ParseMode.MARKDOWN,
    )

async def foption_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    s = get_user_settings(uid)
    if query.data == "fopt_yes":
        s["forward"] = True
        text = "✅ Will **forward** messages (with header)."
    else:
        s["forward"] = False
        text = "✅ Will **copy** messages (no header)."
    set_user_settings(uid, s)
    await query.edit_message_text(text, parse_mode=constants.ParseMode.MARKDOWN)

async def forward_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    s   = get_user_settings(uid)

    # ensure config complete
    if not all([s["src_channel"], s["dst_channel"], s["from_id"], s["to_id"]]):
        return await update.message.reply_text(
            "⚠️ Your settings are incomplete. Use <b>/settings</b> to check.",
            parse_mode=constants.ParseMode.HTML
        )

    frm, to = s["from_id"], s["to_id"]
    total   = to - frm + 1
    done    = 0
    good    = 0

    status = await update.message.reply_text(
        f"🚀 Processing 0/{total}, forwarded 0"
    )

    for mid in range(frm, to + 1):
        done += 1

        # 1) back off every 10 messages
        if done % 10 == 0:
            await asyncio.sleep(5)

        # 2) update status asap
        await status.edit_text(f"🚀 Processed {done}/{total}, forwarded {good}")

        # 3) small throttle
        await asyncio.sleep(0.1)

        # 4) fetch via Telethon
        orig_list = await TCLIENT.get_messages(s["src_channel"], ids=[mid])
        orig = orig_list[0] if orig_list else None

        # 5) skip if not a document/video/animation/video_note
        if not (
            orig
            and (
                orig.document
                or orig.video
                or getattr(orig, "animation", None)
                or getattr(orig, "video_note", None)
            )
        ):
            logging.info(f"Skipping ID {mid}: no supported media")
            continue

        # 6) attempt copy, retrying on rate-limit until success or fatal error
        while True:
            try:
                if s.get("forward"):
                    await context.bot.forward_message(
                        chat_id      = s["dst_channel"],
                        from_chat_id = s["src_channel"],
                        message_id   = mid,
                    )
                else:
                    await context.bot.copy_message(
                        chat_id      = s["dst_channel"],
                        from_chat_id = s["src_channel"],
                        message_id   = mid,
                    )
                good += 1
                break

            except RetryAfter as e:
                logging.warning(f"RateLimit on ID {mid}, sleeping {e.retry_after}s")
                await asyncio.sleep(e.retry_after + 1)
            # then retry same mid

            except FloodWaitError as e:
                logging.warning(f"Telethon FloodWait on ID {mid}, sleeping {e.seconds}s")
                await asyncio.sleep(e.seconds + 1)
                # then retry

            except Exception as e:
                logging.error(f"Failed to forward ID {mid}: {e!r}")
                break

    await status.edit_text(f"✅ Done! Processed {done}, forwarded {good} doc/video(s).")

# ─── Application setup ────────────────────────────────────────────────────────

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN env var required")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CommandHandler("setsrc",   setsrc))
    app.add_handler(CommandHandler("setdst",   setdst))
    app.add_handler(CommandHandler("setrange", setrange))
    app.add_handler(CommandHandler("Foption",   foption_cmd))
    app.add_handler(CallbackQueryHandler(foption_callback, pattern="^fopt_"))
    app.add_handler(CommandHandler("forward",  forward_cmd))

    print("🔗 Multi-user forwarder is up!")
    app.run_polling()

if __name__ == "__main__":
    main()

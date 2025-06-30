import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH
from store import load_settings, save_settings
from forwarder import forward_range
from logger import logger

client = TelegramClient('session', API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def on_start(event):
    await event.reply(
        "🤖 *ForwardBot* ready!\n\n"
        "Use /settings to view or update:\n"
        "`/setsrc @source_channel`\n"
        "`/setdst @target_channel`\n"
        "`/setrange <from_id> <to_id>`\n"
        "Then `/forward` to begin."
    )

@client.on(events.NewMessage(pattern='/settings'))
async def on_settings(event):
    s = load_settings()
    text = (
        f"**Current Settings**\n"
        f"- Source: {s['src_channel']}\n"
        f"- Destination: {s['dst_channel']}\n"
        f"- Range: {s['from_id']} → {s['to_id']}\n\n"
        "Use `/setsrc`, `/setdst`, `/setrange` to update."
    )
    await event.reply(text)

@client.on(events.NewMessage(pattern=r'/setsrc (.+)'))
async def on_setsrc(event):
    chan = event.pattern_match.group(1).strip()
    s = load_settings(); s['src_channel'] = chan; save_settings(s)
    await event.reply(f"✅ Source channel set to `{chan}`")

@client.on(events.NewMessage(pattern=r'/setdst (.+)'))
async def on_setdst(event):
    chan = event.pattern_match.group(1).strip()
    s = load_settings(); s['dst_channel'] = chan; save_settings(s)
    await event.reply(f"✅ Destination channel set to `{chan}`")

@client.on(events.NewMessage(pattern=r'/setrange (\d+) (\d+)'))
async def on_setrange(event):
    frm = int(event.pattern_match.group(1))
    to  = int(event.pattern_match.group(2))
    s = load_settings(); s['from_id'] = frm; s['to_id'] = to; save_settings(s)
    await event.reply(f"✅ Range set: `{frm}` → `{to}`")

@client.on(events.NewMessage(pattern='/forward'))
async def on_forward(event):
    s = load_settings()
    if not all([s['src_channel'], s['dst_channel'], s['from_id'], s['to_id']]):
        return await event.reply("⚠️ Please configure all settings first with `/settings`.")
    await event.reply(f"🚀 Forwarding `{s['from_id']}`→`{s['to_id']}` from `{s['src_channel']}` to `{s['dst_channel']}`…")
    try:
        await forward_range(client, s['src_channel'], s['dst_channel'], s['from_id'], s['to_id'])
        await event.reply("✅ Forwarding completed!")
    except Exception as e:
        logger.exception("Forward error")
        await event.reply(f"❌ Error: {e}")

async def main():
    # if BOT_TOKEN is set, start in bot mode
    if BOT_TOKEN:
        await client.start(bot_token=BOT_TOKEN)
    else:
        await client.start()          # falls back to user-session
    print("🔗 Bot is up!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

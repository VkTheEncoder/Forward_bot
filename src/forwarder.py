# src/forwarder.py

import asyncio
import re
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.types import InputPeerChannel
from logger import logger

async def _resolve_channel(client, identifier: str) -> InputPeerChannel:
    """
    Accepts either:
      - A username like '@mychannel'
      - A numeric ID like '-1001234567890'
    Returns InputPeerChannel(id, access_hash).
    """
    if re.fullmatch(r"-?\d+", identifier):
        cid = int(identifier)
        dialogs = await client.get_dialogs()
        for d in dialogs:
            ent = d.entity
            if getattr(ent, "id", None) == cid:
                return InputPeerChannel(ent.id, ent.access_hash)
        raise ValueError(f"Channel ID {cid} not found in bot’s dialogs")

    uname = identifier.lstrip("@")
    res   = await client(GetChannelsRequest(channels=[uname]))
    ch    = res.chats[0]
    return InputPeerChannel(ch.id, ch.access_hash)

async def forward_range(client, src_id, dst_id, frm, to):
    src_peer = await _resolve_channel(client, src_id)
    dst_peer = await _resolve_channel(client, dst_id)

    total, forwarded = to - frm + 1, 0
    status = await client.send_message("me", f"Starting forward: 0 / {total}")

    batch = 100
    for start in range(frm, to + 1, batch):
        end  = min(start + batch - 1, to)
        ids  = list(range(start, end + 1))
        msgs = await client.get_messages(src_peer, ids=ids, reverse=True)

        for msg in msgs:
            if msg.document or msg.video:
                try:
                    await client.forward_messages(dst_peer, msg)
                    forwarded += 1
                    await status.edit(f"Forwarded {forwarded} / {total}")
                except Exception as e:
                    logger.error(f"Failed to forward {msg.id}: {e}")
                    await asyncio.sleep(1)

    await status.edit(f"Done! Forwarded {forwarded} / {total}")

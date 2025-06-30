import asyncio
import re
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.types import InputPeerChannel
from logger import logger

async def _resolve_channel(client, identifier: str) -> InputPeerChannel:
    """
    Accepts either:
      - A username string like '@mychannel'
      - A numeric ID string like '-1001234567890'

    Returns an InputPeerChannel with id and access_hash.
    """
    # 1) Numeric ID path
    if re.fullmatch(r'-?\d+', identifier):
        cid = int(identifier)
        # fetch dialogs so we find the channel in bot's chats
        dialogs = await client.get_dialogs()
        for d in dialogs:
            ent = d.entity
            if getattr(ent, 'id', None) == cid:
                return InputPeerChannel(ent.id, ent.access_hash)
        raise ValueError(f"Channel ID {cid} not found in bot’s dialogs")

    # 2) Public username path
    uname = identifier.lstrip('@')
    res = await client(GetChannelsRequest(channels=[uname]))
    ch  = res.chats[0]  # e.g. a Channel object
    return InputPeerChannel(ch.id, ch.access_hash)

async def forward_range(client, src_identifier, dst_identifier, from_id, to_id):
    # Resolve both endpoints to peers
    src_peer = await _resolve_channel(client, src_identifier)
    dst_peer = await _resolve_channel(client, dst_identifier)

    total     = to_id - from_id + 1
    forwarded = 0
    status    = await client.send_message('me', f'Starting forward: 0 / {total}')

    batch_size = 100
    for batch_start in range(from_id, to_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, to_id)
        ids = list(range(batch_start, batch_end + 1))
        msgs = await client.get_messages(src_peer, ids=ids, reverse=True)

        for msg in msgs:
            # only forward documents and videos
            if msg.document or msg.video:
                try:
                    await client.forward_messages(dst_peer, msg)
                    forwarded += 1
                    await status.edit(f'Forwarded {forwarded} / {total}')
                except Exception as e:
                    logger.error(f'Failed to forward {msg.id}: {e}')
                    # brief pause before retrying next message
                    await asyncio.sleep(1)

    await status.edit(f'Done! Forwarded {forwarded} / {total}')

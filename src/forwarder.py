import asyncio
from telethon.tl.functions.channels import GetChannelsRequest
from telethon.tl.types import InputPeerChannel
from logger import logger

async def _resolve_channel(client, username: str) -> InputPeerChannel:
    uname = username.lstrip('@')
    res = await client(GetChannelsRequest(channels=[uname]))
    channel = res.chats[0]
    return InputPeerChannel(channel.id, channel.access_hash)

async def forward_range(client, src_username, dst_username, from_id, to_id):
    src_peer = await _resolve_channel(client, src_username)
    dst_peer = await _resolve_channel(client, dst_username)

    total     = to_id - from_id + 1
    forwarded = 0
    status    = await client.send_message('me', f'Starting forward: 0 / {total}')

    batch_size = 100
    for batch_start in range(from_id, to_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, to_id)
        ids = list(range(batch_start, batch_end + 1))
        msgs = await client.get_messages(src_peer, ids=ids, reverse=True)

        for msg in msgs:
            if msg.document or msg.video:
                try:
                    await client.forward_messages(dst_peer, msg)
                    forwarded += 1
                    await status.edit(f'Forwarded {forwarded} / {total}')
                except Exception as e:
                    logger.error(f'Failed to forward {msg.id}: {e}')
                    await asyncio.sleep(1)

    await status.edit(f'Done! Forwarded {forwarded} / {total}')

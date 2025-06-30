import asyncio
from logger import logger

async def forward_range(client, src_username, dst_username, from_id, to_id):
    src = await client.get_entity(src_username)
    dst = await client.get_entity(dst_username)

    total = to_id - from_id + 1
    forwarded = 0
    status_msg = await client.send_message('me', f'Starting forward: {forwarded} / {total}')

    batch_size = 100
    for batch_start in range(from_id, to_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, to_id)
        ids = list(range(batch_start, batch_end + 1))
        msgs = await client.get_messages(src, ids=ids, reverse=True)

        for msg in msgs:
            if msg.document or msg.video:
                try:
                    await client.forward_messages(dst, msg)
                    forwarded += 1
                    await status_msg.edit(f'Forwarded {forwarded} / {total}')
                except Exception as e:
                    logger.error(f'Failed to forward {msg.id}: {e}')
                    await asyncio.sleep(1)

    await status_msg.edit(f'Done! Forwarded {forwarded} / {total}')

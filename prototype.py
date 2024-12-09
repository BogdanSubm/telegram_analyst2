"""
module for experiments
"""

from telethon import TelegramClient
import asyncio
import time

import config

api_id = config.API_ID
api_hash = config.API_HASH
client = TelegramClient('test_tg', api_id, api_hash, system_version="5.9 x64")

async def main():
    me = await client.get_me()

    # You can pretty-print any Telegram object with the "stringify" method
    print(me.stringify())

    # You can access all attributes of Telegram objects with the dot operator
    username= me.username
    print(username)
    print(me.phone)

    # You can print all the dialogs/conversations that you are part of:
    async for d in client.iter_dialogs():
        print(d.name, 'has ID', d.id)

    # You can send messages to yourself (markdown is available)...
    await client.send_message('me', 'Hello, **V !**', link_preview=False)

if __name__ == '__main__':
    with client :
        client.loop.run_until_complete(main())

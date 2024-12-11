"""
module for experiments
"""

from telethon import TelegramClient
import asyncio
import time

from telethon.tl.functions.channels import GetFullChannelRequest

import config

api_id = config.API_ID
api_hash = config.API_HASH
client = TelegramClient('test_tg', api_id, api_hash, system_version="5.9 x64")


async def main() :
    # me = await client.get_me()
    # #
    # # You can pretty-print any Telegram object with the "stringify" method
    # print(me.stringify())

    # You can access all attributes of Telegram objects with the dot operator
    # username= me.username
    # print(username)
    # print(me.phone)

    # You can print all the dialogs/conversations that you are part of:
    # async for d in client.iter_dialogs():
    #     print(d.name, 'has ID', d.id)

    # You can send messages to yourself (markdown is available)...
    # await client.send_message('me', 'Hello, **V !**', link_preview=False)

    channels = [-1001373128436, -1001920826299, -1001387835436, -1001490689117]

    for ch_id in channels :
        try :
            ch_entity = await client.get_entity(ch_id)
            # print(ch_entity.stringify())
        except Exception as e :
            print(f"Не удалось получить сущность канала: {e}")
            return

        # Получение полной информации о канале
        try:
            full_info = await client(GetFullChannelRequest(ch_entity))
            subscribers_count = full_info.full_chat.participants_count
            print("Число подписчиков канала:", subscribers_count)
        except Exception as e:
            print(f"Не удалось получить информацию о канале: {e}")

        break

if __name__ == '__main__' :
    with client :
        client.loop.run_until_complete(main())

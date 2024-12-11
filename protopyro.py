import asyncio
import betterlogging as logging

from pyrogram import Client, idle, filters, raw, types
from pyrogram.types import Message, Chat
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from typing import Dict, Union
from pyrogram.errors import FloodWait
from pyrogram import Client, emoji, filters

from datetime import datetime, date
import config

api_id = config.API_ID
api_hash = config.API_HASH
# app = Client('test_pyrogram')
app = Client('test_pyrogram', api_id, api_hash)


def get_work_channels() -> list[int]:
    channels = [-1001373128436, -1001920826299, -1001387835436, -1001490689117]
    return channels[0:1]


async def main():
    logging.basic_colorized_config(level=logging.INFO)
    async with app:

        for ch in get_work_channels():
            chat: Chat = await app.get_chat(ch)
            if chat:
                # print(f'Успешно прочитан чат #: {ch}.')
                logging.info(f'Успешно прочитан чат #: {chat.id} | {chat.username} | {chat.type.value}.')
                logging.info(f'Численность по состоянию на {datetime.now()}: {chat.members_count}')
                logging.info(f'Число постов по состоянию на {datetime.now()}: {await app.get_chat_history_count(chat.id)}')
            else:
                # print(f'Чат #: {ch} не обнаружен.')
                logging.info(f'Чат #: {ch} не обнаружен.')
#
# async def main2():
#     async with Client('test_pyrogram', api_id, api_hash) as app:
#         await app.send_message('me', f'{emoji.HEART_ON_FIRE} Greetings from **Pyrogram** again! {emoji.SPARKLES}')
#
#
# async def main3():          # всего сообщений в канале
#     # Target channel/supergroup
#     TARGET = -1001373128436     # simulative
#     async with app:
#         res = await app.get_chat_history_count(TARGET)
#         print(res)


app.run(main())
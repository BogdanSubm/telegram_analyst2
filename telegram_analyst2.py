"""
main module
"""
import logging
from logger import get_logger, mylogger
mylogger = get_logger(logging.DEBUG, to_file=False)
mylogger.debug('Loading <mylogger> module')
mylogger.debug('Starting main module <telegram_analyst2>')


import asyncio
from pyrogram import Client, idle, filters, raw, types
from pyrogram.types import Message, Dialog
from pyrogram.enums import ParseMode, ChatType
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from typing import Dict, Union
from pyrogram.errors import FloodWait


from config_py import settings
from pgdb import Database
from database import db



channels = [-1001373128436, -1001920826299, -1001387835436, -1001490689117]

plugins = dict(root=settings.pyrogram.plugins.root,
               include=settings.pyrogram.plugins.include,
               exclude=settings.pyrogram.plugins.exclude)

# chats_for_filters = ['me', my_group]

app = Client(name='test_pyrogram',
             api_id=settings.telegram.api_id,
             api_hash=settings.telegram.api_hash,
             plugins=plugins)

my_group = 'My_test_group20242003'
my_group_id = -1002330451219
simulative_chl = 'simulative_official'  # an outside channel
simulative_chl_id = -1001373128436
simulative_cht = 'itresume_chat'       # an outside supergroup

# async def outbox_message(client: Client, message: Message):
#     await message.edit_text(text=f'--{message.text}--', parse_mode=ParseMode.MARKDOWN)
#     mylogger.info(f'handling new typing message: {message.id}, {message.text}')

async def get_channels(client: Client) -> list[int]:
    # Iterate through all dialogs
    i = 0
    res = []
    async for dialog in client.get_dialogs() :
        if i < settings.analyst.numb_channels_process:
                                #     FOR DEBUGGING
            if dialog.chat.id in (-1001373128436, -1001920826299, -1001387835436, -1001490689117) :
            # if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :
                mylogger.info(f'channel/group has been added for downloading: {dialog.chat.id} - {dialog.chat.title}')
                res.append(int(dialog.chat.id))
                i += 1
    return res


async def main() :

    async with app :
        await app.send_message('me', 'Telegram_analyst2 is running, to find out the commands, type: /help')

        #     FOR DEBUGGING
        print(await get_channels(app))

        # await idle()


if __name__ == '__main__':
    app.run(main())

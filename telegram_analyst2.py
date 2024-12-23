"""
main module
"""
import logging
from logger import get_logger, logger
logger = get_logger(logging.DEBUG, to_file=False)
logger.debug('Loading <mylogger> module')
logger.debug('Starting main module <telegram_analyst2>')


import asyncio
from pyrogram import Client, idle, filters, raw, types
from pyrogram.types import Message, Dialog
from pyrogram.enums import ParseMode, ChatType
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from typing import Dict, Union
from pyrogram.errors import FloodWait

from config_py import settings
from app_status import app_status, AppStatusType


plugins = dict(root=settings.pyrogram.plugins.root,
               include=settings.pyrogram.plugins.include,
               exclude=settings.pyrogram.plugins.exclude)

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


async def main() :

    async with app :
        await app.send_message('me', 'Telegram_analyst2 is running, to find out the commands, type: /help')

        await idle()


if __name__ == '__main__':
    app.run(main())

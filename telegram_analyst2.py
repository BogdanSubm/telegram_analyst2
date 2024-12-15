"""
main module
"""
import logging

from pyrogram import Client, idle, filters, raw, types
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from typing import Dict, Union
from pyrogram.errors import FloodWait

import asyncio


from config_py import settings
from logger import get_logger


logger = get_logger(logging.INFO, to_file=True)


async def outbox_message(client: Client, message: Message):
    await message.edit_text(text=f'--{message.text}--', parse_mode=ParseMode.MARKDOWN)
    logger.info(f'handling new typing message: {message.id}, {message.text}')


async def main() :
    app = Client(name='test_pyrogram',
                 api_id=settings.telegram.api_id,
                 api_hash=settings.telegram.api_hash)

    app.add_handler(MessageHandler(outbox_message, filters.me & filters.text))

    logger.debug('info')
    logger.info('info')
    logger.warning('warning')
    logger.error('error')

    await app.start()
    await idle()
    await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
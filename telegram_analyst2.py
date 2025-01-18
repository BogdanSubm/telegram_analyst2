"""
main module
"""
import asyncio
from pyrogram import Client

from config_py import settings
from logger import logger
logger.debug('Loading and starting main module <telegram_analyst2>')

from app_status import app_status, running_status, AppStatusType
from scheduler import main_schedule


plugins = dict(root=settings.pyrogram.plugins.root,
               include=settings.pyrogram.plugins.include,
               exclude=settings.pyrogram.plugins.exclude)

app = Client(name='telegram_analyst2',
             api_id=settings.telegram.api_id,
             api_hash=settings.telegram.api_hash,
             plugins=plugins)


async def main() :

    # async with app :
    await app.start()
    await app.send_message('me', 'Telegram_analyst2 is running, to find out the commands, type: /help')
        # await idle()
    main_schedule.start()

    while running_status.status :
        await asyncio.sleep(1)

    main_schedule.stop()   #wait=False)
    await app.stop()

    logger.info('The application was stopped at the user\'s command.')

if __name__ == '__main__':
    app.run(main())

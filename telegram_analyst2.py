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



# my_group = 'My_test_group20242003'
# my_group_id = -1002330451219
# simulative_chl = 'simulative_official'  # an outside channel
# simulative_chl_id = -1001373128436
# simulative_cht = 'itresume_chat'       # an outside supergroup

# async def outbox_message(client: Client, message: Message):
#     await message.edit_text(text=f'--{message.text}--', parse_mode=ParseMode.MARKDOWN)
#     mylogger.info(f'handling new typing message: {message.id}, {message.text}')

# def tick():
#     print(f"Tick! The time is: {datetime.now()}")
#
# def tick2():
#     print(f"Tick! The time is: {datetime.now()} 2!")

#
# app_scheduler = AppScheduler()
# app_scheduler.add_task(func=tick, trigger='interval', seconds=4)
# for i in range(60) :
#     for j in range(10) :
#         minute = 23
#         app_scheduler.add_task(func=tick2, trigger='cron', hour=14, minute=minute+j, second=i)


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

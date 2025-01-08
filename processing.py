
from logger import logger
logger.debug('Loading <processing> module')

from datetime import datetime
from pyrogram import Client

from scheduler import main_schedule
from channel import channels_update
from config_py import settings



def tick1(number):
    print(f'Tick! The time of number {number} is: {datetime.now()}')


async def create_channel_schedule(client: Client) :
    main_schedule.add_job(
        func=channels_update,
        kwargs={'client': client},
        trigger='cron',
        hour=settings.schedules.update_channels.hour,
        minute=settings.schedules.update_channels.minute,
        second=settings.schedules.update_channels.second
    )
    return True


async def create_post_schedule(client: Client) :
    hours: list = settings.schedules.update_posts.hours
    minutes: list = settings.schedules.update_posts.minutes
    seconds: list = settings.schedules.update_posts.seconds
    if not(len(hours) == len(minutes) == len(seconds)) :
        logger.error('Bad schedules time param.')
        return False

    for i, h in enumerate(hours) :
        main_schedule.add_job(
            func=tick1,     #   FOR DEBUG
            kwargs={'number' : i},
            trigger='cron',
            hour=h,
            minute=minutes[i],
            second=seconds[i]
        )

    return True


async def create_processing_schedule(client: Client) -> bool :
    if await create_channel_schedule(client=client) :
        logger.info(f'Channels schedule was creating successful')
        if await create_post_schedule(client=client) :
            logger.info(f'Posts schedule was creating successful')
        else :
            return False
    else :
        return False
    return True
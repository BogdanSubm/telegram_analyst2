
from logger import logger
logger.debug('Loading <processing> module')

from pyrogram import Client

from pgdb import Database
from config_py import settings
from app_types import DBTaskPlan

from channel import channels_update
from task import get_tasks_to_upload
from post import posts_update, upload_tasks_in_pipeline
from scheduler import main_schedule

TaskType = DBTaskPlan


async def create_update_channel_schedule(client: Client) :
    main_schedule.add_job(
        func=channels_update,
        kwargs={'client': client},
        trigger='cron',
        hour=settings.schedules.update_channels.hour,
        minute=settings.schedules.update_channels.minute,
        second=settings.schedules.update_channels.second
    )
    return True


async def create_update_post_schedule(client: Client) :
    hours: list = settings.schedules.update_posts.hours
    minutes: list = settings.schedules.update_posts.minutes
    seconds: list = settings.schedules.update_posts.seconds
    if not(len(hours) == len(minutes) == len(seconds)) :
        logger.error('Bad schedules time param.')
        return False

    for i, h in enumerate(hours) :
        main_schedule.add_job(
            func=posts_update,
            kwargs={'client': client},
            trigger='cron',
            hour=h,
            minute=minutes[i],
            second=seconds[i]
        )

    return True


async def create_task_schedule(client: Client) :
    # open database connection
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    # reading all post tasks that have not been completed yet
    tasks_to_upload: list[TaskType] = await get_tasks_to_upload(db=db)

    return await upload_tasks_in_pipeline(client=client, tasks=tasks_to_upload)


async def create_processing_schedule(client: Client) -> bool :
    logger.info('<create_processing_schedule> was run.')
    main_schedule.scheduler.pause()
    if await create_update_channel_schedule(client=client) :
        logger.info(f'Channels update schedule was creating successful.')
        if await create_update_post_schedule(client=client) :
            logger.info(f'Posts update schedule was creating successful.')
            if await create_task_schedule(client=client) :
                logger.info(f'The creation of a task schedule for posts observation was successful.')
            else :
                logger.error(f'Couldn\'t create task schedule for posts observation...')
                return False
        else :
            logger.error(f'Couldn\'t create posts update schedule...')
            return False
    else :
        logger.info(f'Couldn\'t create channels update schedule...')
        return False
    main_schedule.scheduler.resume()
    return True
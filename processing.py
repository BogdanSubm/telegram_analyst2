
from logger import set_logger, logger
logger.debug('Loading <processing> module')

from pyrogram import Client
from datetime import datetime

from pgdb import Database
from config_py import settings
from app_types import DBTaskPlan

from channel import channels_update
from task import get_tasks
from post import posts_update, upload_tasks_in_pipeline
from scheduler import main_schedule
from exceptions import AppDBError

TaskType = DBTaskPlan


# async def print_used_memory(client: Client) :
#     report = f'Used memory: {psutil.Process().memory_info().rss / 1024 ** 2:.2f} Mb'
#     logger.info(report)
#     await client.send_message('me', report)


async def update_log_file() :
    main_schedule.pause()
    set_logger(level=settings.logging.level_logging, to_file=settings.logging.to_file)
    main_schedule.resume()


async def create_update_log_file() :
    main_schedule.add_job(
        func=update_log_file,
        trigger='cron',
        hour=settings.schedules.update_log_file.hour,
        minute=settings.schedules.update_log_file.minute,
        second=settings.schedules.update_log_file.second
    )
    return True


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


async def channels_posts_update(client: Client) -> bool:
    return await channels_update(client=client) and await posts_update(client=client)


async def create_update_post_schedule(client: Client) :
    hours: list = settings.schedules.update_posts.hours
    minutes: list = settings.schedules.update_posts.minutes
    seconds: list = settings.schedules.update_posts.seconds
    if not(len(hours) == len(minutes) == len(seconds)) :
        logger.error('Bad schedules time param.')
        return False

    for i, h in enumerate(hours) :
        main_schedule.add_job(
            func=channels_posts_update,
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
    try :
        # reading all post tasks that have not been completed yet
        tasks_to_upload: list[TaskType] = await get_tasks(db=db)

    except AppDBError as e :
        logger.error(f'Error: {e}')
        return False

    return await upload_tasks_in_pipeline(client=client, tasks=tasks_to_upload)


async def create_processing_schedule(client: Client) -> bool :
    logger.info('<create_processing_schedule> was run.')
    time_start = datetime.now()
    main_schedule.pause()

    if settings.logging.to_file :
        if await create_update_log_file() :
            logger.info(f'Log file update schedule was creating successful.')
        else :
            logger.info(f'Couldn\'t create log file update schedule...')
            return False

    if await create_update_channel_schedule(client=client) :
        logger.info(f'Channels update schedule was creating successful.')
    else :
        logger.info(f'Couldn\'t create channels update schedule...')
        return False

    if await create_update_post_schedule(client=client) :
        logger.info(f'Posts update schedule was creating successful.')
    else :
        logger.error(f'Couldn\'t create posts update schedule...')
        return False

    if await create_task_schedule(client=client) :
        logger.info(f'The creation of a task schedule for posts observation was successful.')
    else :
        logger.error(f'Couldn\'t create task schedule for posts observation...')
        return False

    main_schedule.resume()
    logger.info(f'<create_processing_schedule> was completed, '
                f'execution time - {(datetime.now() - time_start).total_seconds()} seconds.')
    return True
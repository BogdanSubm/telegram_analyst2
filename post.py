
from logger import logger
logger.debug('Loading <post> module')

import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Message

from pgdb import Database
from config_py import settings
from normalizer import normalizer
from app_types import media_types_encoder, DBPost, DBTaskPlan
from chunk import Chunk
from exceptions import AppDBError

from channel import get_db_channels_dict
from task import tasks_update, set_post_drop_time, post_day_observation
from scheduler import main_schedule


TaskType = DBTaskPlan


async def get_db_channel_posts_list(db:Database, chat_id: int) -> dict[int, bool] :
    # reading all posts of this channel from the database
    start_time = settings.analyst.analyzing_from
    res = db.read_rows(
        table_name='post',
        columns_statement='post_id, is_planned',
        condition_statement=f'True '
                            f'and creation_time >= \'{start_time}\' '
                            f'and channel_id = {chat_id} '
                            f'and drop_time isnull '
    )
    if not res.is_successful :
        raise AppDBError(f'Database operation error: couldn\'t read list of posts of the channel channel_id[{chat_id}].')

    return {_[0]:_[1] for _ in res.value}  # creating a dictionary for a post and its <planned> attribute


async def get_tg_channel_posts_dict(client: Client, chat_id:int) -> dict[int, Message] :
    # reading all posts of this channel from Telegram starting from the date - <analyzing_from>
    start_time = settings.analyst.analyzing_from
    logger.debug(f'start reading messages of the channel channel_id[{chat_id}]:')
    messages: list[Message] = []
    chunk = Chunk(normalizer)
    rd = 0
    async for msg in client.get_chat_history(chat_id=chat_id) :
        rd += 1
        if msg.date >= start_time :
            if msg.service :
                logger.debug(f'service msg # {msg.id}')
                continue  # we exclude service message
            else :
                messages.append(msg)
        else :
            break

        await chunk.one_reading()   # antiflood reading pause

    logger.debug(f'readed {rd} messages, added {len(messages)} messages:')
    if len(messages) > 0 :
        messages.reverse()
        logger.debug(f'   from msg id [{messages[0].id}], date[{messages[0].date}]')
        logger.debug(f'     to msg id [{messages[-1].id}], date[{messages[-1].date}]')

    media_group_flag: int | None = None
    posts: dict[int, Message] = {}

    for msg in messages :
        # a block of code for working with group posts of media groups
        append_flag = True
        if msg.media_group_id :
            if media_group_flag and media_group_flag == msg.media_group_id :
                append_flag = False
            else :
                media_group_flag = msg.media_group_id

        if append_flag :
            posts[msg.id]= msg

    return posts


async def add_post_to_database(db: Database, client: Client, msg: Message) -> bool :

    # identifying advertising posts
    text = (msg.text or msg.caption or '').encode('utf-16').decode('utf-16')
    low_text = text.lower()
    if 'реклама.' in low_text or 'erid' in low_text or 'utm' in low_text :
        is_advertising = True
    else :
        is_advertising = False

    post_record = DBPost(
        channel_id=msg.chat.id,
        post_id=msg.id,
        forward_from_chat=(msg.forward_from_chat.id if msg.forward_from_chat else None),
        creation_time=msg.date,
        drop_time=None,
        is_advertising=is_advertising,
        media_group_id=msg.media_group_id,
        media_type=(media_types_encoder.get(msg.media, None) if msg.media else None),
        post_text=text[:settings.analyst.size_text_fragment_for_save],
        text_len=len(text),
        text_entities_count=len(msg.entities or msg.caption_entities or []),
        # post_url=f'https://t.me/{await get_channel_username(msg.chat)}/{msg.id}'
        post_url=msg.link,
        is_planned=False
    )
    res = db.insert_rows(table_name='post', values=(post_record,))
    if not res.is_successful :
        logger.info(f'Couldn\'t add post post_id[{post_record.post_id}] channel_id[{post_record.channel_id}] '
                    f'in <post> table, we leave it without planning.')
        return False

    logger.info(f'Post post_id[{post_record.post_id}] channel_id[{post_record.channel_id}] '
                f'was added in <post> table, we will plan.')
    return True


async def upload_tasks_in_pipeline(client: Client, tasks: list[TaskType]) -> bool :
    try :
        for task in tasks:
            main_schedule.add_job(
                func=post_day_observation,
                kwargs={'db': None, 'client': client, 'task': task},
                trigger='cron',
                year=task.planned_at.year,
                month=task.planned_at.month,
                day=task.planned_at.day,
                hour=task.planned_at.hour,
                minute=task.planned_at.minute,
                second=task.planned_at.second
            )
    except Exception as e:
        logger.error(f'Error: {e}')
        return False

    return True


async def add_post_tasks_in_schedule(
        db:Database,
        client:Client,
        chat_id: int,
        post_id: int,
        uploading_tasks: bool
) -> bool :
    res = db.read_rows(
        table_name='post',
        columns_statement='creation_time',
        condition_statement=f'True '
                            f'and channel_id = {chat_id} '
                            f'and post_id = {post_id} '
                            f'and drop_time isnull '
    )
    if not res.is_successful or len(res.value) == 0:
        return False

    base_time = res.value[0][0]    # the post creation time
    current_time = datetime.now()

    # creating tasks for a schedule
    task_records: list[DBTaskPlan] = []
    for day in settings.schedules.post_observation_days :
        if ((base_time + timedelta(days=day) >= current_time)
                or (day == settings.schedules.post_observation_days[-1])):
            # adding a task to the schedule if the scheduled time is greater than or equal to the current time
            # or if it is the last day of all observation days.
            task_records.append(
                DBTaskPlan(
                    channel_id=chat_id,
                    post_id=post_id,
                    observation_day=day,
                    # task_in_pipline=False,
                    planned_at=base_time + timedelta(days=day),
                    # started_at=None,
                    completed_at=None
                    ),
            )

    res = db.insert_rows(table_name='task_plan', values=tuple(task_records))
    if not res.is_successful :
        logger.info(f'Couldn\'t scheduled task for post post_id[{post_id}] channel_id[{chat_id}] in <task_plan> table.')
        return False

    logger.info(f'The task for post post_id[{post_id}] channel_id[{chat_id}] has been successfully scheduled '
                f'in the <task_plan> table.')

    if uploading_tasks :
        if await upload_tasks_in_pipeline(client=client, tasks=task_records) :
            logger.info(f'The post tasks has also been uploaded to the running scheduler.')
        else :
            logger.error(f'The post tasks could not be uploaded to the running scheduler.')

    return True


async def turn_on_is_planned_flag(db:Database, chat_id: int, post_id: int) -> bool :
    res = db.update_data(
        table_name='post',
        set_statement=f'is_planned=TRUE',
        condition_statement=f'True '
                            f'and channel_id={chat_id} '
                            f'and post_id={post_id} '
    )
    return res.is_successful


async def updating_posts_and_schedule(
        db: Database,
        client: Client,
        update_posts: list[int],
        db_unplanned_posts: list[int],
        tg_posts: dict[int, Message],
        chat_id: int,
        uploading_tasks: bool
) :
    for pst in update_posts :
        need_planning = True
        if pst not in db_unplanned_posts :
            # adding new post to database
            need_planning = await add_post_to_database(db=db, client=client, msg=tg_posts[pst])

        else :
            # unplanned post in database
            ...
        # putting observation tasks for post into the schedule
        if need_planning :
            if await add_post_tasks_in_schedule(db=db, client=client, chat_id=chat_id, post_id=pst, uploading_tasks=uploading_tasks) :
                # updating the <is_planned> flag for the post, in case the scheduling was completed successfully
                await turn_on_is_planned_flag(db=db, chat_id=chat_id, post_id=pst)
    return


async def posts_update(client: Client, is_first: bool = False) -> bool :
    logger.info('<posts_update> was run.')
    time_start = datetime.now()
    # open database connection
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    try:
        # reading all working channels from the database into the dictionary: <key> - id, <value> - title
        db_channels = await get_db_channels_dict(db=db)

        for ch, title in db_channels.items() :
            logger.info(f'Reading posts of the channel channel_id[{ch}] title[{title}]')
            async with asyncio.TaskGroup() as tg :
                task1 = tg.create_task(get_tg_channel_posts_dict(client=client, chat_id=ch))
                task2 = tg.create_task(get_db_channel_posts_list(db=db, chat_id=ch))

            tg_posts = task1.result()
            db_posts = task2.result()
            db_planned_posts = [post for post, planned in db_posts.items() if planned]
            db_unplanned_posts = [post for post, planned in db_posts.items() if not planned]

            # we check the differences between the database planned posts and telegram posts
            need_update_posts = len(set(db_planned_posts) ^ set(tg_posts.keys())) > 0

            if need_update_posts :
                # creating a list of dropped posts in database (putting label about delete post from Telegram)
                dropping_posts = list(set(db_posts.keys()) - set(tg_posts.keys()))
                logger.info(f'Total posts to dropping: {len(dropping_posts)} for channel channel_id[{ch}] title[{title}]')
                # dropping selected posts and canceling scheduled tasks
                for pst in dropping_posts :
                    await set_post_drop_time(db=db, chat_id=ch, post_id=pst)
                # creating a list of post to add or update and add scheduled tasks to the schedule database
                update_posts = list(set(tg_posts.keys()) - set(db_planned_posts))
                logger.info(f'Channel channel_id[{ch}] title[{title}] - number of posts for add '
                            f'to scheduler: {len(update_posts)}')
                # adding and updating selected posts in the database and the schedule
                await updating_posts_and_schedule(
                    db=db,
                    client=client,
                    update_posts=update_posts,
                    db_unplanned_posts=db_unplanned_posts,
                    tg_posts=tg_posts,
                    chat_id=ch,
                    uploading_tasks=not is_first
                )

    except AppDBError as e:
        logger.error(f'Error: {e}')
        return False

    await tasks_update(db=db, client=client, is_first=is_first)

    logger.info(f'<posts_update> was completed, '
                f'execution time - {(datetime.now() - time_start).total_seconds()} seconds.')

    if not is_first :
        # notification of successful operation of the application
        await client.send_message('me', 'I\'m online...')
        await client.send_message('me', f'{main_schedule.print_stat()}\n{main_schedule.print_memory()}')

    return True

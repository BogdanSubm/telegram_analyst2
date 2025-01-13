
from logger import logger
logger.debug('Loading <task> module')

from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Message, Chat, Username
from pyrogram.errors import BadRequest

from pgdb import Database, Row, Rows
from config_py import settings
from normalizer import normalizer
from reaction import get_post_reactions
from exceptions import AppDBError

from app_types import DBPostHist, DBMediaGroup, DBTaskPlan

TaskType = DBTaskPlan


async def post_is_dropped(db: Database, chat_id: int, post_id: int) -> bool:
    # checking "drop_time" of the post
    res = db.read_rows(
        table_name='post',
        columns_statement='drop_time',
        condition_statement=f'True '
                            f'and channel_id = {chat_id} '
                            f'and post_id = {post_id} '
                            f'and drop_time notnull '
    )
    if not res.is_successful :
        raise AppDBError(f'Database operation error: couldn\'t read dropped status of the post post_id[{post_id}] '
                         f'channel_id[{chat_id}].')
    return len(res.value) == 1


async def set_post_drop_time(db: Database, chat_id: int, post_id: int) -> bool:
    # setting "drop_time" of the post
    res = db.update_data(
        table_name='post',
        set_statement=f'drop_time=\'{datetime.now()}\'',
        condition_statement=f'True '
                            f'and channel_id={chat_id} '
                            f'and post_id={post_id} '
    )
    if res.is_successful :
        logger.info(f'The post post_id[{post_id}] channel_id[{chat_id}] was dropped.')
    else :
        logger.info(f'Couldn\'t dropped post_id[{post_id}] channel_id[{chat_id}].')
    return res.is_successful


async def update_post_and_media_frames(db: Database, client: Client, task: TaskType, msg:Message) -> bool :
    # adding main observation in database
    post_comments = 0
    try :
        post_comments = await normalizer.run(
            client.get_discussion_replies_count,
            chat_id=msg.chat.id,
            message_id=msg.id
        )
    except BadRequest :
        logger.info(f'<No comments> status for the post_id[{msg.id}] channel_id[{msg.chat.id}] title[{msg.chat.title}]')
    # except FloodWait as e:
    #     await asyncio.sleep(e.value)
    if post_comments is None :
        post_comments = 0

    post_reactions = await get_post_reactions(msg)
    posts_hist_record = DBPostHist(
        channel_id=msg.chat.id,
        post_id=msg.id,
        update_time=datetime.now(),
        observation_day=task.observation_day,
        post_comments=post_comments,
        post_views=msg.views,
        stars=post_reactions.stars,
        positives=post_reactions.positives,
        negatives=post_reactions.negatives,
        neutrals=post_reactions.neutrals,
        customs=post_reactions.customs,
        reposts=msg.forwards,
    )

    # checking the media group
    media_frames: list[Message]
    media_records: list[DBMediaGroup] = []
    if msg.media_group_id :
        try:
            media_frames = await normalizer.run(client.get_media_group, chat_id=msg.chat.id, message_id=msg.id)
            if len(media_frames) > 0 :

                # TODO: check below code
                # media_frames.sort(key=lambda f: f.id)

                for i, fr in enumerate(media_frames, start=settings.analyst.media_group_post_ordering_base) :
                    media_records.append(
                        DBMediaGroup(
                            media_group_id=msg.media_group_id,
                            update_time=datetime.now(),
                            post_id=fr.id,
                            observation_day=task.observation_day,
                            post_order=i,
                            post_views=fr.views,
                            reposts=fr.forwards
                        )
                    )

        except ValueError :
            logger.info(f'incorrect media group post post_id[{msg.id}] channel_id[{msg.chat.id}] '
                        f'title[{msg.chat.title}]')

    res = db.insert_rows(table_name='post_hist', values=(posts_hist_record,)).is_successful

    if len(media_records) > 0 :
        res &= db.insert_rows(table_name='media_group', values=tuple(media_records)).is_successful

    return res


async def set_task_status_is_completed(db:Database, chat_id: int, post_id: int, observation_day: int) -> bool:
    # setting "completed_at" of the task
    res = db.update_data(
        table_name='task_plan',
        set_statement=f'completed_at=\'{datetime.now()}\'',
        condition_statement=f'True '
                            f'and channel_id={chat_id} '
                            f'and post_id={post_id} '
                            f'and observation_day={observation_day}'
    )
    if res.is_successful :
        logger.info(f'Planned observation for the post_id [{post_id}] channel_id[{chat_id}] '
                    f'observation_day[{observation_day}] was completed.')
    else :
        raise AppDBError(f'Couldn\'t write the completed status of the planned task for post_id[{post_id}] '
                         f'channel_id[{chat_id}] observation_day[{observation_day}].')
    return res.is_successful


async def post_day_observation(db: Database|None, client: Client, task: TaskType) -> bool:
    # the main function of observation
    if db is None :
        db: Database = Database(settings.database_connection)
        if not db.is_connected :
            return False
    try :
        if await post_is_dropped(db=db, chat_id=task.channel_id, post_id=task.post_id) :
            # the post in database have value in <drop_time> field
            return True
    except AppDBError:
        pass

    msg: Message = await normalizer.run(client.get_messages, chat_id=task.channel_id, message_ids=task.post_id)
    if msg.empty :
        # the Telegram message has been deleted
        await set_post_drop_time(db=db, chat_id=task.channel_id, post_id=task.post_id)
        await set_task_status_is_completed(
            db=db,
            chat_id=task.channel_id,
            post_id=task.post_id,
            observation_day=task.observation_day
        )
    else :
        if await update_post_and_media_frames(db=db, client=client, task=task, msg=msg) :
            await set_task_status_is_completed(
                db=db,
                chat_id=task.channel_id,
                post_id=task.post_id,
                observation_day=task.observation_day
            )
    return True


async def get_tasks_to_launch(db: Database) -> list[TaskType]:
    current_time = datetime.now()

    tasks_to_launch: list[TaskType] = []
    res = db.read_rows(
        table_name='task_plan',
        columns_statement='*',
        condition_statement=f'True '
                f'and planned_at <= \'{current_time+timedelta(seconds=settings.schedules.delay_for_tasks_update)}\' '
                            f'and completed_at isnull '
    )
    if not res.is_successful :
        raise AppDBError(f'Database operation error: couldn\'t read list of planned task.')

    # elif len(res.value) > 0 :
    #     tasks_to_launch: list[TaskType] = res.value

    elif len(res.value) > 0:
        tasks_to_launch = [TaskType(*val) for val in res.value]

    return tasks_to_launch


async def get_tasks_to_upload(db: Database) -> list[TaskType]:
    tasks_to_upload = []
    res = db.read_rows(
        table_name='task_plan',
        columns_statement='*',
        condition_statement=f'True '
                            f'and completed_at isnull '
    )
    if not res.is_successful :
        raise AppDBError(f'Database operation error: couldn\'t read list of planned task for uploading.')

    elif len(res.value) > 0 :
        tasks_to_upload = [TaskType(*val) for val in res.value]

    return tasks_to_upload


async def tasks_update(client: Client) :
    logger.info('<tasks_update> was run.')
    time_start = datetime.now()
    # open database connection
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    try :
        # reading all the tasks that should have already been completed
        tasks_to_launch : list[TaskType] = await get_tasks_to_launch(db=db)

        for task in tasks_to_launch :
            await post_day_observation(db=db, client=client, task=task)

    except AppDBError as e :
        logger.error(f'Error: {e}')
        return False

    logger.info(f'<tasks_update> was completed, '
                f'execution time - {(datetime.now() - time_start).total_seconds()} seconds.')
    return True

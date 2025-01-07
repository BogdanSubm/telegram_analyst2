
from logger import logger
logger.debug('Loading <post> module')

import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Message, Chat, Username
from pyrogram.enums import MessageMediaType, ParseMode, ChatType


from pgdb import Database, Row, Rows
from config_py import settings
from normalizer import normalizer
from app_types import media_types_encoder
from chunk import Chunk, chunks
from reaction import TGReactions, get_post_reactions
from channel import get_db_channels_dict
from exceptions import AppDBError



async def get_db_channel_posts_list(db:Database, chat_id: int) -> dict[int, bool] :
    # reading all posts of this channel from the database
    start_time = settings.analyst.analyzing_from
    res = db.read_rows(
        table_name='post',
        columns_statement='post_id, planned',
        condition_statement=f'creation_time >= \'{start_time}\' '
                            f'and channel_id = {chat_id} '
                            f'and drop_time isnull'
    )
    if not res.is_successful :
        raise AppDBError(f'Database operation error: couldn\'t read list of posts of the channel - id[{chat_id}].')

    return {_[0]:_[1] for _ in res.value}  # creating a dictionary for a post and its <planned> attribute


async def get_tg_channel_posts_dict(client: Client, chat_id:int) -> dict[int, Message] :
    # reading all posts of this channel from Telegram starting from the date - <analyzing_from>
    start_time = settings.analyst.analyzing_from
    logger.debug(f'Start reading messages of the channel - id[{chat_id}]:')
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

        await chunk.one_reading()   # anti flood reading pause

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


async def drop_posts(db:Database, dropping_posts: list, db_posts: dict[int, bool], chat_id: Chat) :
    # dropping selected posts
    for pst in dropping_posts :
        res = db.update_data(
            table_name='post',
            set_statement=f'drop_time=\'{datetime.now()}\'',
            condition_statement=f'channel_id={chat_id} and post_id={pst}'
        )
        if res.is_successful :
            if db_posts[pst] :
                # planned post
                # TODO: Выключить все задачи запланированные по посту
                ...

            logger.info(f'  the post id [{pst}] was dropped.')
        else :
            logger.info(f'  couldn\'t dropped post id [{pst}].')


async def updating_posts_and_schedule(
        db: Database,
        client: Client,
        update_posts: list,
        db_unplanned_posts: list,
        tg_posts: dict[int, Message],
        chat_id: int
) :
    for pst in update_posts :
        if pst not in db_unplanned_posts :
            # adding new post to database
            ...
        else :
            # unplanned post in database
            ...


async def posts_update(client: Client) -> bool :
    # open database connection
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    try:
        # reading all working channels from the database into the dictionary: <key> - id, <value> - title
        db_channels = await get_db_channels_dict(db=db)

        for ch, title in db_channels.items() :
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
                logger.info(f'total posts to dropping: {len(dropping_posts)} from channel id [{ch}] title [{title}]')
                # dropping selected posts and canceling scheduled tasks
                await drop_posts(db=db, dropping_posts=dropping_posts, db_posts=db_posts, chat_id=ch)

                # creating a list of post to add or update and add scheduled tasks to the schedule database
                update_posts = list(set(tg_posts.keys()) - set(db_planned_posts))
                logger.info(f'channel id[{ch}] title[{title}] - number of posts for add '
                            f'to scheduler: {len(update_posts)}')
                # adding and updating selected posts in the database and the schedule
                await updating_posts_and_schedule(
                    db=db,
                    client=client,
                    update_posts=update_posts,
                    db_unplanned_posts=db_unplanned_posts,
                    tg_posts=tg_posts,
                    chat_id=ch
                )

        # await tasks_update(db=db, client=client)


    except AppDBError as e:
        logger.error(f'Error: {e}')
        return False

    db.close_connection()

    return True

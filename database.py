"""
main database module
"""
import logging
from asyncio import TaskGroup

from logger import logger
logger.debug('Loading <database> module')

import asyncio
import datetime
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Message, Chat, Username
from pyrogram.enums import MessageMediaType, ParseMode, ChatType
from dataclasses import dataclass
from pyrogram.errors import FloodWait

from typing import NamedTuple

from pgdb import Database, Row, Rows
from config_py import settings
from normalizer import Normalizer
from app_status import app_status, AppStatusType
from app_types import media_types_encoder
from chunk import Chunk, chunks

# db: Database | None = None   # global Database object
normalizer = Normalizer()


# The data structures for save in database
class DBChannel(Row) :       # record in <channel> table
    id: int     # channel id    - primary key

    username: str   # name for telegram channel login
    title: str  # title of the channel
    category: str   # 'Аналитика' - channel category
    creation_time: datetime     # channel creation time


class DBChannelHist(Row) :       # record in <channel_hist> table
    channel_id: int     # channel id    - foreign key

    update_time: datetime   # update time
    subscribers: int    # number of subscribers of the channel
    msgs_count: int     # number of messages of the channel


class DBPost(Row) :       # record in <post> table
    channel_id: int     # channel id  - part of the group primary key
    post_id: int     # post id      - part of the group primary key

    forward_from_chat : int | None    # channel id from where the post was forwarded (if any)
    creation_time: datetime     # post creation time
    drop_time: datetime | None    # time to delete a post
    is_advertising: bool    # the sign of an advertising post
    media_group_id: int      # media group id if the post is a group post
    media_type : str   # type of content
    post_text: str | None     # content of a text or a caption field if any
    text_len: int | None    # the length of the text content string
    text_entities_count: int | None     # the number of formatting entities in the text or caption field
    post_url: str |None     # the url-link to the post (for example, https://t.me/simulative_official/2109)


class DBPostHist(Row) :       # record in <post_hist> table
    channel_id: int     # channel id  - part of the group foreign key
    post_id: int     # post id      - part of the group foreign key

    update_time: datetime   # update time
    post_comments: int     # number of comments
    post_views: int     # number of views
    stars: int     # number of <stars> reactions
    positives: int  # number of positive emoji
    negatives: int  # number of negative emoji
    neutrals: int   # number of neutrals emoji
    customs: int  # number of custom emoji
    reposts: int  # the number of reposts of this post


class DBMediaGroup(Row) :       # record in <post_hist> table
    media_group_id: int      # media group id if the post is a group post  - primary key

    update_time: datetime   # update time
    post_id: int     # post id
    post_order: int     # serial number of the post in the media group
    post_views: int     # number of views
    reposts: int    # the number of reposts of this post


start_analytics_time = settings.analyst.analyzing_from


async def get_channel_creation_time(client, channel) -> datetime | None :
    first_message: datetime | None = None
    try:
        async for msg in client.get_chat_history(channel, limit=2, offset_id=2) :
            first_message: Message = msg
    except Exception as e:
        logger.error('')
    return first_message.date


async def get_channel_username(channel: Chat) -> str :
    if channel.username :
        return channel.username
    elif channel.usernames :
        for user in channel.usernames :
            if user.active :
                return user.username
    logger.error(f'Error: couldn\'t get the <username> of the channel')
    return ''


async def get_channel_information(client: Client, channel: int) -> DBChannel | None :
    try :
        ch = await normalizer.run(client.get_chat, channel)
        channel_first_post_time = await get_channel_creation_time(client, channel)
        record = DBChannel(id=ch.id,
                           username=ch.username,
                           title=ch.title,
                           category='DA',
                           creation_time=channel_first_post_time
                           )

    except Exception as e:
        logger.error(f'Error_get_channel_information: {e}')
        return None

    return record


async def update_all(client: Client, channels: list[int] | None, update_time: datetime | None) -> bool:
    global normalizer
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    if channels is None:
        # The value None of this parameter means that we will process channels from the <channel> table.
        res = db.read_rows(table_name='channel')
        if res.is_successful :
            if len(res.value)>0 :
                channels = [_[0] for _ in res.value]
                logger.debug(f'<channels> parameter is None, channels are ready for process: {channels}')
            else:
                logger.error('Error: channel <table> is empty')
                return False
        else:
            logger.error('Error: <channel> table reading error')
            return False

    for ch in channels :

        if db.search_rows(table_name='channel', search_column='id', search_value=ch) :
            logger.debug(f'channel with id # {ch} success found')
        else:
            logger.debug(f'channel with id # {ch} not found, let\'s add him')

            insert_channel = await get_channel_information(client=client, channel=ch)
            if insert_channel :
                res = db.insert_rows(table_name='channel', values=(insert_channel,))
                logger.info(f'channel with id # {ch} has {"" if res.is_successful else "not "}'
                            f'been added')
            else:
                logger.error(f'Error: it is not possible to get information to add'
                             f' on the channel with the ID #: {ch}')

        # await asyncio.sleep(delay=1)


    # TO DO: Для всех каналов произвести апдейт таблицы channel_hist
    #

    # TO DO: Выполнить обновление постов и истории для всей базы
    #
    # i=0
    # while i<len(channels) :
    #     ch=channels[i]
    # # for ch in channels :
    #     try :
    #         logger.debug(f'channel/group in process: {ch}')
    #
    #
    #
    #         chat = await client.get_chat(ch)
    #         print(chat)
    #
    #         ch += 1
    #         # break
    #         # ch_rec = DBChannel(id=w)
    #
    #     except FloodWait as e :
    #         logger.warning(f'Channel # {i} processing - the request limit has been exceeded. Pause for {e.value} seconds.')
    #         await asyncio.sleep(e.value)
    #
    #     except Exception as e :
    #         logger.error(f'An error has occurred: {e}')
    #         return False
    #
    return True


async def get_channels(client: Client) -> list[int]:
    # Iterate through all dialogs
    i = 0
    res = []
    async for dialog in client.get_dialogs() :

        if i < settings.analyst.numb_channels_process:

                                #     FOR DEBUGGING
            if dialog.chat.id in (-1001373128436, -1001920826299, -1001387835436, -1001490689117) :
                                #       FOR PROD
            # if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :
                logger.info(f'channel/group has been added for downloading: {dialog.chat.id} - {dialog.chat.title}')
                res.append(dialog.chat.id)
                i += 1

    logger.debug(f'channels in the selection: {res}')


    return res


async def recreate_tables() -> bool:
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    if not db.create_table(table_name='channel',
                           columns_statement='''
                                id int8 NOT NULL,
                                username varchar NOT NULL,
                                title varchar NOT NULL,
                                category varchar NULL,
                                creation_time timestamp NULL,
                                CONSTRAINT channel_pk PRIMARY KEY (id)
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='channel_hist',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                subscribers int4 NULL,
                                msgs_count int4 NULL,
                                CONSTRAINT channel_hist_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    #                                 id bigserial NOT NULL,
    if not db.create_table(table_name='post',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                post_id int4 NOT NULL,
                                forward_from_chat int8 NULL,
                                creation_time timestamp NOT NULL,
                                drop_time timestamp NULL,
                                is_advertising bool DEFAULT false NOT NULL,
                                media_group_id int8 NULL,
                                media_type varchar NULL,
                                post_text varchar NULL,
                                text_len int4 NULL,
                                text_entities_count int4 NULL,
                                post_url varchar NULL,
                                CONSTRAINT post_pk PRIMARY KEY (channel_id, post_id),
                                CONSTRAINT post_unique UNIQUE (media_group_id),
                                CONSTRAINT post_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='post_hist',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                post_id int4 NOT NULL,
                                update_time timestamp NOT NULL,
                                post_comments int4 DEFAULT 0 NOT NULL,
                                post_views int4 DEFAULT 0 NOT NULL,
                                stars int4 DEFAULT 0 NOT NULL,
                                positives int4 DEFAULT 0 NOT NULL,
                                negatives int4 DEFAULT 0 NOT NULL,
                                neutrals int4 DEFAULT 0 NOT NULL,
                                customs int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT post_hist_post_fk FOREIGN KEY (channel_id, post_id)
                                    REFERENCES public.post(channel_id, post_id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='media_group',
                           columns_statement='''                            
                                media_group_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                post_id int4 NOT NULL,
                                post_order int2 NOT NULL,
                                post_views int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT media_group_post_fk FOREIGN KEY (media_group_id) 
                                    REFERENCES public.post(media_group_id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    return True


def get_full_day_time_stamp(time_now: datetime = datetime.now()) -> datetime:
    time = time_now - timedelta(days=1)
    return datetime(time.year, time.month, time.day, 23, 59, 59, 0)


async def put_to_base_posts(db: Database, messages: list[Message]) -> bool :

    logger.debug(f'Size of the list of <Messages>: {len(messages)}')

    media_group_flag: int | None = None

    values: list[Row] = []
    for msg in messages :

        # a block of code for working with group posts of media groups
        append_flag = True
        if msg.media_group_id :
            if media_group_flag and media_group_flag == msg.media_group_id :
                append_flag = False
            else :
                media_group_flag = msg.media_group_id

        if append_flag :

            # a block of code for identifying advertising posts
            text = (msg.text or msg.caption or '').encode('utf-16').decode('utf-16')
            low_text = text.lower()
            if 'реклама.' in low_text or 'erid' in low_text or 'utm' in low_text :
                is_advertising = True
            else :
                is_advertising = False

            values.append(
                DBPost(
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
                    post_url=f'https://t.me/{await get_channel_username(msg.chat)}/{msg.id}'
                )
            )

    logger.debug(f'Size of the list of <values>: {len(values)}')
    res = []
    async for vls in chunks(lst=values, chunk_size=settings.analyst.chunk_size_for_db_ops) :
        res.append(db.insert_rows(table_name='post', values=tuple(vls)).is_successful)
    return all(res)


async def put_to_base_media(db: Database, messages: list[Message], upload_time: datetime) :

    logger.debug(f'Size of the list of media group <Messages>: {len(messages)}')

    values: list[Row] = []
    media_group_flag = None
    post_order = None
    for msg in messages :
        # a block of code for working with group posts of media groups
        if media_group_flag and media_group_flag == msg.media_group_id :
            post_order += 1
        else :
            post_order = settings.analyst.media_group_post_ordering_base    # 0 or 1 - base for numbering
        media_group_flag = msg.media_group_id

        values.append(
            DBMediaGroup(
                media_group_id=media_group_flag,
                update_time=upload_time,
                post_id=msg.id,
                post_order=post_order,
                post_views=msg.views ,
                reposts=msg.forwards
            )
        )

    logger.debug(f'Size of the list of media group <values>: {len(values)}')
    res = []
    async for vls in chunks(lst=values, chunk_size=settings.analyst.chunk_size_for_db_ops) :
        res.append(db.insert_rows(table_name='media_group', values=tuple(vls)).is_successful)
    return all(res)


async def upload_all(client: Client, upload_time: datetime) -> bool:
    global normalizer
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    async for dialog in client.get_dialogs() :

            #     FOR DEBUGGING
        # if dialog.chat.id in (-1001373128436, -1001920826299, -1001387835436, -1001490689117) :
        if dialog.chat.id in (-1001150636847,-1001999600137,-1001407735984,-1001387835436,-1001434942369,-1001247460025,-1001269328727,-1001119907458,-1002173481054,-1001140040257,-1001720833502,-1001786987818,-1001039255739,-1001684696497,-1001375960541,-1001684146975,-1001646511362,-1001852630630,-1002075081423,-1001863771680,-1001507734288,-1001164672298,-1001555979359,-1001654432419,-1001713271750,-1002061202990,-1001329188755,-1001648137205,-1002017388853,-1002160874756,-1001513592482,-1001178238337,-1001601022378,-1001756387595,-1001408836166,-1001638862576,-1001610037070,-1001580761898,-1001920826299,-1001373128436,-1001490689117,-1001618735800,-1001117681513,-1001573892445,-1002243195124,-1001542820616,-1001195518065,-1001937140822,-1001286050825,-1001788488602,-1001052741705,-1001439011975,-1001451120475,-1001081286887,-1001682401578,-1001160069287,-1001702796681,-1002100634882,-1001983260268,-1002125857137,-1001544737980,-1001576767771,-1001850344604,-1001903546969,-1001417960831,-1002146883464,-1001533350227,-1001752641311,-1001503786901,-1001212864285,-1001217403746,-1001638304350,-1001556054484,-1001414693404,-1001375051700,-1001217426310,-1001972927572,-1001860277066,-1001155412393,-1001223651429,-1001240501786,-1001336087232,-1001526752830,-1002329275862,-1002479064953,-1001265941657,-1001567847129,-1002312481032,-1001586330290,-1001354117866,-1001706328181,-1001625951959,-1002376985514,-1001633110548,-1001315746544,-1001314600216,-1001576490999,-1002038340948,-1001066811392,-1001181269908,-1001437741565,-1002188344885,-1002319527378,-1001621747845) :

        # if dialog.chat.id in (-1001373128436, -1001788488602) :    # Simulative, Клуб анонимных аналитиков
        #     logger.info(f'{dialog}')
        #     break

            #       FOR PROD
        # if dialog.chat.type == ChatType.CHANNEL :
            # if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :

            logger.info(f'channel loading: {dialog.chat.id} - {dialog.chat.title}')

            # channel_creation_time = await normalizer.run(
            #     get_channel_creation_time,
            #     client,
            #     dialog.chat.id
            # )

            res = db.insert_rows(
                table_name='channel',
                values=(
                    DBChannel(
                        id=dialog.chat.id,
                        username=await get_channel_username(dialog.chat),
                        title=dialog.chat.title,
                        category='DA',
                        creation_time=await normalizer.run(
                            get_channel_creation_time,
                            client,
                            dialog.chat.id
                        )
                    ),
                )
            )

            await normalizer.run()
            upload_time =datetime.now()
            msgs_count = await client.get_chat_history_count(dialog.chat.id)

            res = db.insert_rows(
                table_name='channel_hist',
                values=(
                    DBChannelHist(
                        channel_id=dialog.chat.id,
                        update_time=upload_time,
                        subscribers=dialog.chat.members_count,
                        msgs_count=msgs_count
                    ),
                )
            )

            logger.info(f'channel has {"" if res.is_successful else "not "} been added ')

            messages: list[Message] = []
            media_groups_messages: list[Message] = []
            upload_time = datetime.now()

            chunk_reading = Chunk(normalizer)
            async for msg in client.get_chat_history(chat_id=dialog.chat.id) :
                if msg.date >= start_analytics_time :
                    if msg.service :
                        continue      # we exclude service message
                else :
                    break

                messages.append(msg)

                if msg.media_group_id :
                    media_groups_messages.append(msg)

                await chunk_reading.one_reading()   # anti flood reading pause

            messages.reverse()
            media_groups_messages.reverse()

            # try:
                # async with asyncio.TaskGroup() as tg :
                #     task1 = tg.create_task(
                #         put_to_base_posts(
                #             db=db,
                #             messages=messages
                #         )
                #     )
                #     task2 = tg.create_task(
                #         put_to_base_media(
                #             db=db,
                #             messages=media_groups_messages,
                #             upload_time=upload_time
                #         )
                #     )
                # if not (task1.result() and task2.result()) :

            res1 = res2 = False
            try:
                res1 = await put_to_base_posts(db=db, messages=messages)
            except Exception as e :
                logger.error(f'Error in put_to_base_posts: {e}')
            try:
                res2 = await put_to_base_media(db=db, messages=media_groups_messages, upload_time=upload_time)
            except Exception as e :
                logger.error(f'Error put_to_base_media: {e}')

            if not (res1 and res2) :
                logger.error(f'Error when adding channel history {dialog.chat.id} - {dialog.chat.title}')

            # except Exception as e:
            #     logger.error(f'Error task group context: {e}')

            # logger.info(f'channel history ({""} posts) has {"" if res.is_successful else "not "}been added')
            # print(len(messages))
            # await asyncio.sleep(delay=1)


    return True


async def run_processing(client: Client) :
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    match app_status.status :
        case AppStatusType.FIRST_RUN :
            logger.info('First run, uploading all data has been started...')
            # if not await upload_all(client=client, upload_time=get_full_day_time_stamp()) :
            if not await upload_all(client=client, upload_time=datetime.now()) :
                logger.error('Error: updating of all database\'s tables has been unsuccessful...')
                return False
            logger.info('Uploading - ok!')

        case AppStatusType.PROCESS_RUN :
            pass

        case AppStatusType.UPDATE_RUN :
            pass

        case _: pass


    return True


async def list_channels_update(client: Client) -> bool:
    return True


if __name__ == '__mail__' :
    pass
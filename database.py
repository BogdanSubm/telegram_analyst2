"""
main database module
"""
from pyexpat.errors import messages

from logger import logger
logger.debug('Loading <database> module')

import asyncio
import datetime
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType
from dataclasses import dataclass
from pyrogram.errors import FloodWait

from typing import NamedTuple

from pgdb import Database, Row, Rows
from config_py import settings
from normalizer import Normalizer
from app_status import app_status, AppStatusType

# db: Database | None = None   # global Database object
normalizer = Normalizer()

# The data structures for save in database
class DBChannel(Row) :       # record in <channel> table
    id: int     # channel id
    username: str   # name for telegram channel login
    title: str  # title of the channel
    category: str   # 'Аналитика' - channel category
    creation_time: datetime     # channel creation time

class DBChannelHist(Row) :       # record in <channel_hist> table
    channel_id: int     # channel id
    update_time: datetime   # update time
    subscribers: int    # number of subscribers of the channel
    msgs_count: int     # number of messages of the channel

class DBPost(Row) :       # record in <channel> table
    # id: int     # channel id
    post_id: int     # post id
    channel_id: int     # channel id
    creation_time: datetime     # post creation time
    drop_time: datetime | None    # post creation time
    is_advertising: bool    # the sign of an advertising post
    group_post_id: int      # the sign of a group post
    content_type : str      # type of content
    content: str | None     # title of the channel
    link: str |None     # 'Аналитика' - channel category

start_analytics_time = settings.analyst.analyzing_from

async def get_channel_first_post_time(client, channel) -> datetime :
    async for msg in client.get_chat_history(channel, limit=2, offset_id=2) :
        first_message: Message = msg
    return first_message.date


async def get_channel_information(client: Client, channel: int) -> DBChannel | None :
    try :
        ch = await normalizer.run(client.get_chat, channel)
        channel_first_post_time = await get_channel_first_post_time(client, channel)
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
                                username varchar NULL,
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

    if not db.create_table(table_name='post',
                           columns_statement='''
                                id bigserial NOT NULL,
                                post_id int4 NOT NULL,
                                channel_id int8 NOT NULL,
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
                                CONSTRAINT post_pk PRIMARY KEY (id),
                                CONSTRAINT post_unique UNIQUE (media_group_id),
                                CONSTRAINT post_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='post_hist',
                           columns_statement='''                            
                                post_raw_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                post_comments int4 DEFAULT 0 NOT NULL,
                                post_views int4 DEFAULT 0 NOT NULL,
                                stars int4 DEFAULT 0 NOT NULL,
                                positives int4 DEFAULT 0 NOT NULL,
                                negatives int4 DEFAULT 0 NOT NULL,
                                neutrals int4 DEFAULT 0 NOT NULL,
                                customs int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT post_hist_post_fk FOREIGN KEY (post_raw_id) 
                                    REFERENCES public.post(id) ON UPDATE CASCADE
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


async def upload_all(client: Client, upload_time: datetime) -> bool:
    global normalizer
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    async for dialog in client.get_dialogs() :

            #     FOR DEBUGGING
        if dialog.chat.id in (-1001373128436, -1001920826299, -1001387835436, -1001490689117) :
        # if dialog.chat.id in (-1001920826299,) :
            #       FOR PROD
        # if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :
            logger.info(f'channel loading: {dialog.chat.id} - {dialog.chat.title}')
            channel_first_post_time = await normalizer.run(get_channel_first_post_time,
                                                                client,
                                                                dialog.chat.id)

            res = db.insert_rows(
                table_name='channel',
                values=(
                    DBChannel(
                        id=dialog.chat.id,
                        username=dialog.chat.username,
                        title=dialog.chat.title,
                        category='DA',
                        creation_time=channel_first_post_time
                    ),
                )
            )
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
            async for msg in client.get_chat_history(chat_id=dialog.chat.id) :
                if msg.date >= start_analytics_time :
                    if msg.service :
                        continue      # we exclude service message
                else :
                    break

                messages.append(msg)
                #
                # comments = await client.get_discussion_replies_count(
                #     chat_id=dialog.chat.id,
                #     message_id=msg.id
                # )

                # print(comments)

            # messages.reverse()

            # for msg in messages :
            #     if msg.text :
            #         if ('реклама' in msg.text.lower() or 'erid' in msg.text.lower()
            #                 or 'utm' in msg.text.lower()):
            #             is_advertising = True
            #         else:
            #             is_advertising = False






            logger.info(f'channel history ({""} posts) has {"" if res.is_successful else "not "}been added')
            print(len(messages))


            # class DBPost(Row) :  # record in <channel> table
            #     # id: int     # channel id
            #     post_id: int  # post id
            #     channel_id: int  # channel id
            #     creation_time: datetime  # post creation time
            #     drop_time: datetime | None  # post creation time
            #     is_advertising: bool  # the sign of an advertising post
            #     group_post_id: int  # the sign of a group post
            #     content_type: str  # type of content
            #     content: str | None  # title of the channel
            #     link: str | None  # 'Аналитика' - channel category
            #
            # else:
            #     logger.error(f'Error: it is not possible to get information to add'
            #                  f' on the channel with the ID #: {ch}')

        # await asyncio.sleep(delay=1)

    return True


async def run_processing(client: Client) :
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    match app_status.status :
        case AppStatusType.FIRST_RUN :
            logger.info('First run, uploading all data has been started...')
            if not await upload_all(client=client, upload_time=get_full_day_time_stamp()) :
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
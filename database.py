"""
main module
"""
from logger import logger
logger.debug('Loading <database> module')

import asyncio
import datetime
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType
from dataclasses import dataclass
from pyrogram.errors import FloodWait

from typing import NamedTuple

from pgdb import Database, Row, Rows
from config_py import settings, FirstRunFlag
from normalizer import Normalizer

first_run_flag = FirstRunFlag() # let's find out: is this the first launch of our application

db: Database | None = None   # global Database object
normalizer = Normalizer()


# The data structures for save in database
class DBChannel(Row) :       # record in <channel> table
    id: int     # channel id
    username: str   # name for telegram channel login
    title: str  # title of the channel
    category: str   # 'Аналитика' - channel category
    creation_time: datetime     # channel creation time


async def get_channel_first_post_time(client, channel) -> datetime :
    # TO DO: Определить время первой активности на канале
    async for msg in client.get_chat_history(channel, limit=2, offset_id=2) :
        first_message: Message = msg
    logger.debug(f'first message id: {first_message.id}')
    return first_message.date
    # return datetime.fromisoformat('2024-01-01 00:00:00.000')


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
            # if dialog.chat.id in (-1001373128436, -1001920826299, -1001387835436, -1001490689117) :
                                #       FOR PROD
            if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :
                logger.info(f'channel/group has been added for downloading: {dialog.chat.id} - {dialog.chat.title}')
                res.append(dialog.chat.id)
                i += 1

    logger.debug(f'channels in the selection: {res}')


    return res


async def recreate_all_table() -> bool:
    global db
    if not db.create_table(table_name='channel',
                           columns_statement='''
                                id int8 NOT NULL,
                                username varchar(50) NULL,
                                title varchar(100) NOT NULL, 
                                category varchar(25) NULL, 
                                creation_time timestamp NULL,
                                CONSTRAINT channel_pk PRIMARY KEY(id)
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='channel_hist',
                           columns_statement='''
                                channel_id int8 NOT NULL,
	                            update_time timestamp NOT NULL,
	                            subscribers int4 NULL,
	                            msg_count int4 NULL,
	                            CONSTRAINT channel_hist_channel_fk FOREIGN KEY (channel_id) 
	                                REFERENCES public.channel(id) ON UPDATE CASCADE
	                            ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='post',
                           columns_statement='''
                                id bigserial NOT NULL,
                                post_id int4 NOT NULL,
                                channel_id int8 NOT NULL,
                                creation_time timestamp NOT NULL,
                                drop_time timestamp NULL,
                                is_advertising bool DEFAULT false NOT NULL,
                                group_post_id varchar(15) NULL,
                                content_type varchar(15) NOT NULL,
                                "content" varchar(100) NULL,
                                CONSTRAINT post_pk PRIMARY KEY (id),
                                CONSTRAINT post_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
	                            ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='post_hist',
                           columns_statement='''                            
                                post_raw_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                "comments" int4 DEFAULT 0 NOT NULL,
                                "views" int4 DEFAULT 0 NOT NULL,
                                positives int4 DEFAULT 0 NOT NULL,
                                negatives int4 DEFAULT 0 NOT NULL,
                                neutrals int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT post_hist_post_fk FOREIGN KEY (post_raw_id) 
                                    REFERENCES public.post(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False
    return True


async def first_run(client: Client) -> Database | bool :
    global db
    db = Database(settings.database_connection)
    if not db.is_connected :
        logger.error('Error: there is no connection to the database...')
        return False

    if first_run_flag.is_first() :
        logger.info('The first launch, the beginning of initialization and filling')
        logger.info('Resetting of all database\'s tables get started...')
        if not (await recreate_all_table()) :
            logger.error('Error: resetting of all database\'s tables has been unsuccessful...')
            return False
        logger.info('Resetting - ok!')
        channels = await get_channels(client)
        logger.info('Filling of all database\'s tables get started...')
        if not (await update_all(client=client, channels=channels, update_time=datetime.now())) :
            logger.error('Error: filling of all database\'s tables has been unsuccessful...')
            return False
        logger.info('Filling - ok!')
        logger.info('Successful installation!')

        #    FOR DEBUGGING, PLACE A COMMENT SYMBOL IN FRONT OF THE LINE BELOW
        # first_run_flag.set_not_first()

        return True
    else :
        logger.info('This is not the first launch app, the database is connected...')
        return True


async def another_run(client: Client) :
    global db

    if first_run_flag.is_first() :
        logger.warning('Error: the first launch, initialization and filling is required.')
        return False
    else :
        db = Database(settings.database_connection)
        if not db.is_connected :
            logger.error('Error: there is no connection to the database...')
            return False

        channels = await get_channels(client)
        # channels = [-1001373128436, -1001920826299, -1001387835436, -1001490689117]

        if not (await update_all(client=client, channels=channels, update_time=datetime.now())) :
            logger.error('Error: updating of all database\'s tables has been unsuccessful...')
            return False
        logger.info('Updating - ok!')


        return True


if __name__ == '__mail__' :
    pass
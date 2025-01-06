
from logger import logger
logger.debug('Loading <channel> module')

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
from exceptions import AppDBError


# The data structures for save in database
class DBChannel(Row) :       # record in <channel> table
    id: int     # channel id    - primary key

    username: str   # name for telegram channel login
    title: str  # title of the channel
    category: str   # 'Аналитика' - channel category
    creation_time: datetime     # channel creation time
    turn_on_time: datetime     # channel time of start analysis
    turn_off_time: datetime | None    # channel time of ending analysis


class DBChannelHist(Row) :       # record in <channel_hist> table
    channel_id: int     # channel id    - foreign key

    update_time: datetime   # update time
    subscribers: int    # number of subscribers of the channel
    msgs_count: int     # number of messages of the channel


def tick():
    print(f"Tick! The time is: {datetime.now()}")


async def get_db_channels_dict(db: Database) -> dict :
    # reading all working channels from the database
    res = db.read_rows(
        table_name='channel',
        columns_statement='id, title',
        condition_statement='turn_off_time isnull'
    )
    if not res.is_successful :
        raise AppDBError('Database operation error: couldn\'t read channel list.')

    return {_[0]:_[1] for _ in res.value}     # creating a dict. with channels: <key> - id, <value> - title


async def get_tg_channels_dict(client: Client, selected_channels: tuple[int, ...] = None) -> dict[int, Chat] :
    # reading all subscribed channels in Telegram
    tg_channels = {}
    async for dialog in client.get_dialogs() :
        if (dialog.chat.type == ChatType.CHANNEL and
                ((dialog.chat.id in selected_channels) if isinstance(selected_channels, tuple) else True)):
                # if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :
            tg_channels[dialog.chat.id] = dialog.chat
            logger.debug(f'channel id: {dialog.chat.id} channel title: {dialog.chat.title}')
        # await asyncio.sleep(0)

    return tg_channels


async def turn_off_channel(db: Database, off_channel: list[int], db_channels: dict) :
    # turning off selected channels
    for ch in off_channel :
        res = db.update_data(
            table_name='channel',
            set_statement=f'turn_off_time=\'{datetime.now()}\'',
            condition_statement=f'id={ch}'
        )
        if res.is_successful :
            # TODO: Выключить все задачи запланированные по каналу

            logger.info(f'The channel was turned off: id[{ch}] title[{db_channels[ch]}]')
        else :
            logger.info(f'Сouldn\'t turn off the channel: id[{ch}] title_in_database[{db_channels[ch]}]')


async def get_channel_username(channel: Chat) -> str :
    if channel.username :
        return channel.username
    elif channel.usernames :
        for user in channel.usernames :
            if user.active :
                return user.username
    logger.info(f'Couldn\'t get the <username> of the channel: id[{channel.id}] title[{channel.title}].')
    return ''


async def adding_channel(db: Database, client: Client, add_channels: list[int], tg_channels: dict[int, Chat]) :
    # adding selected channels to the database
    add_list = []
    for ch in add_channels :
        channel = tg_channels[ch]
        add_list.append(
            DBChannel(
                id=channel.id,
                username=await get_channel_username(channel),
                title=channel.title,
                category='DA',
                creation_time=(await client.get_messages(chat_id=channel.id, message_ids=1)).date,
                turn_on_time=datetime.now(),
                turn_off_time=None
            )
        )

    res = db.insert_rows(table_name='channel', values=tuple(add_list))
    if res.is_successful :
        logger.info(f'{res.value} channels have been successfully added to the database.')
    else :
        raise AppDBError('Database operation error: couldn\'t add new channels to the database.')


async def update_channel_hist(db: Database, client: Client, db_channels: dict[int, str], tg_channels: dict[int, Chat]) :
    # adding new records to the <channel_hist>
    # await normalizer.run()

    add_hist = []
    for ch in db_channels.keys() :
        channel = tg_channels[ch]
        upload_time = datetime.now()
        msgs_count = await normalizer.run(client.get_chat_history_count, channel.id)
        add_hist.append(
            DBChannelHist(
                channel_id=channel.id,
                update_time=upload_time,
                subscribers=channel.members_count,
                msgs_count=msgs_count
            )
        )
        logger.debug(f'append channel_hist record for channel: {channel.id}')

    res = db.insert_rows(table_name='channel_hist', values=tuple(add_hist))
    if res.is_successful :
        logger.info(f'The history records of {res.value} channels have been successfully added to the database.')
    else :
        raise AppDBError('Database operation error: couldn\'t add new history records of channels to the database.')


async def channel_title_update(db: Database, check_list: list[int], db_channels: dict, tg_channels: dict[int, Chat]) :
    # updating the channel title if necessary
    for ch in check_list :
        if db_channels[ch] != tg_channels[ch].title:
            res = db.update_data(
                table_name='channel',
                set_statement=f'title=\'{tg_channels[ch].title}\'',
                condition_statement=f'id={ch}'
            )
            if res.is_successful :
                logger.info(f'The channel title has been updated: id[{ch}] old title [{db_channels[ch]}] -> '
                            f'new title[{tg_channels[ch].title}]')
            else :
                logger.info(f'Сouldn\'t update channel name: id[{ch}] title_in_database[{db_channels[ch]}] '
                            f'actual_title_in_Telegram[{tg_channels[ch].title}]')


async def channels_update(client: Client, is_first: bool = False) -> bool :
    # open database connection
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    try:
        # reading all working channels from the database into the dictionary: <key> - id, <value> - title
        db_channels = await get_db_channels_dict(db=db)

        # reading all subscribed channels in Telegram
        #      FOR DEBUG
        # filtered_channels = (
        #     -1001720833502, -1001121902388, -1001684696497, -1001457597091, -1001373128436, -1001163756937,
        #     -1001684146975, -1001407735984, -1001198940680, -1001387835436, -1001178238337, -1001451120475,
        #     -1001973032155, -1001638862576, -1001434942369, -1001654432419, -1001490689117, -1001920826299,
        #     -1002177572398, -1001408836166
        # )
        # tg_channels = await get_tg_channels_dict(client=client, selected_channels=filtered_channels)
        #   FOR PROD
        tg_channels = await get_tg_channels_dict(client=client)

        # we check the differences between the database and telegram subscriptions
        need_update_channels_list = len(set(db_channels.keys()) ^ set(tg_channels.keys())) > 0

        if need_update_channels_list :
            # creating a list of channels to turn off in database
            off_channel = list(set(db_channels.keys()) - set(tg_channels.keys()))
            logger.info(f'channels turn off: {off_channel}')
            # turning off selected channels
            await turn_off_channel(db=db, off_channel=off_channel, db_channels=db_channels)

            # creating a list of channels to adding into database
            add_channels = list(set(tg_channels.keys()) - set(db_channels.keys()))
            logger.info(f'channels adding: {add_channels}')
            # adding selected channels to the database
            await adding_channel(db=db, client=client, add_channels=add_channels, tg_channels=tg_channels)

            # creating a list to check if the channel name needs to be updated (...or other params)
            check_list = list(set(db_channels.keys()) & set(tg_channels.keys()))
        else :
            check_list = db_channels.keys()

        logger.info(f'channels title updating: {check_list}')
        # updating the channel title if necessary (...or other params)
        await channel_title_update(db=db, check_list=check_list, db_channels=db_channels, tg_channels=tg_channels)

        if not is_first :
            if need_update_channels_list :
                db_channels = await get_db_channels_dict(db=db)
            await update_channel_hist(db=db, client=client, db_channels=db_channels, tg_channels=tg_channels)

    except AppDBError as e:
        logger.error(f'Error: {e}')
        return False

    db.close_connection()

    return True

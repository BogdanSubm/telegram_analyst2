# Channel module

from logger import logger
logger.debug('Loading <channel> module')

import asyncio
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.types import Message, Chat, Username
from pyrogram.enums import MessageMediaType, ParseMode, ChatType

from pgdb import Database
from config_py import settings
from normalizer import normalizer
from exceptions import AppDBError

from app_types import DBChannel, DBChannelHist


# def tick():
#     print(f"Tick! The time is: {datetime.now()}")


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

            logger.info(f'The channel channel_id[{ch}] title[{db_channels[ch]}] was turned off.')
        else :
            logger.info(f'Сouldn\'t turn off the channel channel_id[{ch}] title_in_database[{db_channels[ch]}]')


async def get_channel_username(channel: Chat) -> str :
    if channel.username :
        return channel.username
    elif channel.usernames :
        for user in channel.usernames :
            if user.active :
                return user.username
    logger.info(f'Couldn\'t get the <username> of the channel channel_id[{channel.id}] title[{channel.title}].')
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
                logger.info(f'The channel title has been updated channel_id[{ch}] old title[{db_channels[ch]}] -> '
                            f'new title[{tg_channels[ch].title}]')
            else :
                logger.info(f'Сouldn\'t update channel name channel_id[{ch}] title_in_database[{db_channels[ch]}] '
                            f'actual_title_in_Telegram[{tg_channels[ch].title}]')


async def channels_update(client: Client, is_first: bool = False) -> bool :
    # open database connection
    logger.info('<channels_update> was run.')
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    try:
        # reading all working channels from the database into the dictionary: <key> - id, <value> - title
        db_channels = await get_db_channels_dict(db=db)

        #      FOR DEBUG
        # filtered_channels = (
        #     -1001150636847,-1001999600137,-1001407735984,-1001387835436,-1001434942369,-1001247460025,-1001269328727,
        #     -1001119907458,-1002173481054,-1001140040257,-1001720833502,-1001786987818,-1001039255739,-1001684696497,
        #     -1001375960541,-1001684146975,-1001646511362,-1001852630630,-1002075081423,-1001863771680,-1001507734288,
        #     -1001164672298,-1001555979359,-1001654432419,-1001713271750,-1002061202990,-1001329188755,-1001648137205,
        #     -1002017388853,-1002160874756,-1001513592482,-1001178238337,-1001601022378,-1001756387595,-1001408836166,
        #     -1001638862576,-1001610037070,-1001580761898,-1001920826299,-1001373128436,-1001490689117,-1001618735800,
        #     -1001117681513,-1001573892445,-1002243195124,-1001542820616,-1001195518065,-1001937140822,-1001286050825,
        #     -1001788488602,-1001052741705,-1001439011975,-1001451120475,-1001081286887,-1001682401578,-1001160069287,
        #     -1001702796681,-1002100634882,-1001983260268,-1002125857137,-1001544737980,-1001576767771,-1001850344604,
        #     -1001903546969,-1001417960831,-1002146883464,-1001533350227,-1001752641311,-1001503786901,-1001212864285,
        #     -1001217403746,-1001638304350,-1001556054484,-1001414693404,-1001375051700,-1001217426310,-1001972927572,
        #     -1001860277066,-1001155412393,-1001223651429,-1001240501786,-1001336087232,-1001526752830,-1002329275862,
        #     -1002479064953,-1001265941657,-1001567847129,-1002312481032,-1001586330290,-1001354117866,-1001706328181,
        #     -1001625951959,-1002376985514,-1001633110548,-1001315746544,-1001314600216,-1001576490999,-1002038340948,
        #     -1001066811392,-1001181269908,-1001437741565,-1002188344885,-1002319527378,-1001621747845
        # )
        # tg_channels = await get_tg_channels_dict(client=client, selected_channels=filtered_channels)

        #   FOR PROD
        # reading all subscribed channels in Telegram
        tg_channels = await get_tg_channels_dict(client=client)

        # we check the differences between the database and telegram subscriptions
        need_update_channels_list = len(set(db_channels.keys()) ^ set(tg_channels.keys())) > 0

        if need_update_channels_list :
            # creating a list of channels to turn off in database
            off_channel = list(set(db_channels.keys()) - set(tg_channels.keys()))
            logger.info(f'Channels turn off: {off_channel}')
            # turning off selected channels
            await turn_off_channel(db=db, off_channel=off_channel, db_channels=db_channels)

            # creating a list of channels to adding into database
            add_channels = list(set(tg_channels.keys()) - set(db_channels.keys()))
            logger.info(f'Channels adding: {add_channels}')
            # adding selected channels to the database
            await adding_channel(db=db, client=client, add_channels=add_channels, tg_channels=tg_channels)

            # creating a list to check if the channel name needs to be updated (...or other params)
            check_list = list(set(db_channels.keys()) & set(tg_channels.keys()))
        else :
            check_list = db_channels.keys()

        logger.info(f'Channels title updating: {check_list}')
        # updating the channel title if necessary (...or other params)
        await channel_title_update(db=db, check_list=check_list, db_channels=db_channels, tg_channels=tg_channels)

        if not is_first :
            if need_update_channels_list :
                db_channels = await get_db_channels_dict(db=db)
            await update_channel_hist(db=db, client=client, db_channels=db_channels, tg_channels=tg_channels)

    except AppDBError as e:
        logger.error(f'Error: {e}')
        return False

    return True

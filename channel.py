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

from app_types import DBChannel, DBChannelHist, DBChannelPlan


# def tick():
#     print(f"Tick! The time is: {datetime.now()}")


async def get_db_channels_dict(db: Database) -> dict :
    # reading all working channels from the database
    res = db.read_rows(
        table_name='channel',
        # columns_statement='id, title, turn_on_time',
        columns_statement='id, title',
        condition_statement='turn_off_time isnull'
    )
    if not res.is_successful :
        raise AppDBError('Database operation error: couldn\'t read channel list.')

    # # creating a dict. with channels: <key> - id, <value> : dict with keys: 'title' and 'turn_on_time'
    # return {v[0]:dict(title=v[1], turn_on_time=v[2]) for v in res.value}

    return {_[0]:_[1] for _ in res.value}     # creating a dict. with channels: <key> - id, <value> - title


async def get_tg_channels_dict(client: Client, selected_channels: list[int]) -> dict[int, Chat] :
    # reading all subscribed channels in Telegram
    tg_channels = {}
    async for dialog in client.get_dialogs() :
        if (dialog.chat.type == ChatType.CHANNEL and
                ((dialog.chat.id in selected_channels) if (isinstance(selected_channels, list)
                                                           and len(selected_channels) > 0) else True)):
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
            # after turning off, the channel and its posts will stop updating
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


async def update_channel_hist(
        db: Database,
        client: Client,
        db_channels: dict[int, str],
        tg_channels: dict[int, Chat],
        update_time: datetime
) :
    # adding new records to the <channel_hist>
    # await normalizer.run()

    add_hist = []
    for ch in db_channels.keys() :
        channel = tg_channels[ch]
        # upload_time = datetime.now()
        msgs_count = await normalizer.run(client.get_chat_history_count, channel.id)
        add_hist.append(
            DBChannelHist(
                channel_id=channel.id,
                # update_time=upload_time
                update_time=update_time,
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

    return True


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


async def get_channel_plan_day(db:Database) -> datetime:
    res = db.read_rows(
        table_name='channel_plan',
        columns_statement='planned_at',
        condition_statement=f'True '
                            f'and completed_at isnull '
    )
    if not res.is_successful or len(res.value) == 0:
        raise AppDBError(f'Couldn\'t read or missing the day of the channel update plan.')

    return res.value[0][0]


async def update_channel_plan(db:Database, current_time_plan: datetime = None) -> bool :
    current_time = datetime.now()
    if current_time_plan :
        res = db.update_data(
            table_name='channel_plan',
            set_statement=f'completed_at=\'{current_time}\'',
            condition_statement=f'True '
                                f'and planned_at=\'{current_time_plan}\' '
                                f'and completed_at isnull '
        )
        if not res.is_successful :
            raise AppDBError(f'Failed to record the status of a completed scheduled task for channels update.')

        current_time = current_time_plan + timedelta(days=1)

    new_time_plan = datetime(
        year=current_time.year,
        month=current_time.month,
        day=current_time.day,
        hour=settings.schedules.update_channels.hour,
        minute=settings.schedules.update_channels.minute,
        second=settings.schedules.update_channels.second)

    res = db.insert_rows(
        table_name='channel_plan',
        values=(
            DBChannelPlan(
                planned_at=new_time_plan,
                completed_at=None
            ),
        )
    )
    if not res.is_successful :
        raise AppDBError(f'Couldn\'t add a new day to the channels update plan.')

    return True


async def channels_update(client: Client, is_first: bool = False) -> bool :
    # open database connection
    logger.info('<channels_update> is running.')
    time_start = datetime.now()
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    try:
        async with asyncio.TaskGroup() as tg :
            task1 = tg.create_task(get_tg_channels_dict(
                client=client,
                selected_channels=settings.analyst.channel_selection_filter)
            )
            task2 = tg.create_task(get_db_channels_dict(db=db))

        tg_channels = task1.result()
        db_channels = task2.result()

        # # reading all working channels from the database into the dictionary: <key> - id, <value> - title
        # db_channels = await get_db_channels_dict(db=db)
        # # reading all or only filtered (by config.json) subscribed channels in Telegram
        # tg_channels = await get_tg_channels_dict(
        #     client=client,
        #     selected_channels=settings.analyst.channel_selection_filter
        # )

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

        logger.info(f'Channels title updating check.')
        # updating the channel title if necessary (...or other params)
        await channel_title_update(db=db, check_list=check_list, db_channels=db_channels, tg_channels=tg_channels)

        if is_first :
            # creating the first task for channels update
            await update_channel_plan(db=db)
        else :
            logger.info(f'Channels history updating.')
            update_time = await get_channel_plan_day(db=db)
            if update_time and datetime.now() >= update_time :
                if need_update_channels_list :
                    db_channels = await get_db_channels_dict(db=db)
                if await update_channel_hist(
                        db=db,
                        client=client,
                        db_channels=db_channels,
                        tg_channels=tg_channels,
                        update_time=update_time
                ) :
                    await update_channel_plan(db=db, current_time_plan=update_time)

    except AppDBError as e:
        logger.error(f'Error: {e}')
        return False

    logger.info(f'<channels_update> was completed, '
                f'execution time - {(datetime.now() - time_start).total_seconds():.2f} seconds.')
    return True
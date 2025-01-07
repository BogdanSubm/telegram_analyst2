# Handlers module

from logger import logger
logger.debug('Loading <handlers> module')

from pyrogram import Client, filters
from pyrogram.types import Message
import enum

from database import recreate_tables, run_processing, list_channels_update, run_debug
from app_status import app_status, running_status, AppStatusType
from scheduler import main_schedule
from processing import create_processing_schedule

from channel import channels_update

class BotCommand(enum.StrEnum) :
    INSTALL = '/install'
    START = '/start'
    UPDATE = '/update'
    HELP = '/help'
    STOP = '/stop'
    DEBUG = '/debug'

command_list = [ _[1:] for _ in [BotCommand.INSTALL,
                                 BotCommand.START,
                                 BotCommand.UPDATE,
                                 BotCommand.HELP,
                                 BotCommand.STOP,
                                 BotCommand.DEBUG]]


# Filters
#
# async def func_is_processing(_, __, query: Message) -> bool:
#     return app_status.status == AppStatusType.PROCESS_RUN
#
# is_processing_filter = filters.create(func_is_processing)
#
#
# async def func_channel_filter(_, __, message: Message) -> bool:
#     return message.chat.id in channels.lst
#
# from_channel_filter = filters.create(func_channel_filter)




# Handlers

@Client.on_message(filters.command(command_list))
async def command_handler(client: Client, message: Message) :
    logger.info(f'the "{message.text}" command has been entered')

    match message.text :
        case BotCommand.INSTALL :

            match app_status.status :
                case AppStatusType.NOT_RUNNING | AppStatusType.FIRST_RUN :

                    if await recreate_tables() :
                        app_status.status = AppStatusType.FIRST_RUN
                        logger.info('Resetting - ok.')
                        await message.reply('Resetting - ok!\nWe are ready to start.')
                    else :
                        logger.info('Error resetting database...')
                        await message.reply('Error resetting database...')

                case _:

                    logger.info('<app_status.status> has inappropriate value. '
                                'Resetting tables has not been performed.')
                    await message.reply('The resetting was unsuccessful...\n'
                                    'This may not be the first time the application has been '
                                    'launched, and resetting tables and processing have already '
                                    'been performed.\n'
                                    'For reset all tables delete <.app_status> file '
                                    'in root app directory.')

        case BotCommand.START :

            match app_status.status :
                case AppStatusType.FIRST_RUN :

                    await message.reply('First run processing, uploading data, please wait...')
                    # if await run_processing(client) :
                    if (await channels_update(client=client, is_first=True)
                            and await create_processing_schedule(client=client)) :
                        app_status.status = AppStatusType.PROCESS_RUN
                        await message.reply('Processing has been started successful.')
                    else :
                        await message.reply('Error when starting processing...')

                case AppStatusType.APP_STOPPED :

                    # starting after stopping from the app
                    if await run_processing(client) :
                        app_status.status = AppStatusType.PROCESS_RUN
                        await message.reply('Processing has been started successful (starting after stopping from the app).')
                    else :
                        await message.reply('Error when starting processing...')

                case AppStatusType.PROCESS_RUN :

                    # starting after crash the app
                    if await run_processing(client) :
                        app_status.status = AppStatusType.PROCESS_RUN
                        await message.reply('Processing has been started successful (starting after crash the app).')
                    else :
                        await message.reply('Error when starting processing...')

                case AppStatusType.NOT_RUNNING:

                    logger.info('The first launch, resetting is required.')
                    await message.reply('Sorry, the first launch, resetting is required...')

        case BotCommand.UPDATE :
            await list_channels_update(client)
        #         await message.reply('The update was successful...')
        #     else :
        #         await message.reply('Sorry, updating has not been successfully ...')
        # else :
        #     await message.reply('It will be available after the main processing is started...')

        case BotCommand.HELP :

            await message.reply(
                f'Available commands:\n'
                f'  {BotCommand.INSTALL} - 1-th run (reset all database\'s tables)\n'
                f'  {BotCommand.START} - starting processing\n'
                f'  {BotCommand.UPDATE} - updating the list of processing channels\n'
                f'  {BotCommand.HELP} - list of commands\n'
                f'  {BotCommand.STOP} - stopping processing\n'
            )

        case BotCommand.STOP :

            app_status.status = AppStatusType.APP_STOPPED
            running_status.set_off()
            await message.reply('Processing has been stopped...')

        case BotCommand.DEBUG :
            # logger.debug(await create_processing_schedule(client=client))
            # main_schedule.add_job(
            #     func=channels_update,
            #     trigger='interval',
            #     seconds=300,
            #     kwargs=dict(client='client')
            # )
            # main_schedule.add_job(
            #     func=channels_update,
            #     kwargs={'client':client},
            #     trigger='cron', hour=22, minute=15, second=30)
            await run_debug(client)
            # main_schedule.print_jobs()


# @Client.on_message(is_processing_filter & filters.chat(chats=channels.lst))
# @Client.on_message(is_processing_filter & from_channel_filter & ~filters.service)
# async def echo(client, message: Message) :
#     logger.debug(message)
#     await client.send_message('me', f'Новое сообщение в канале: {message.chat.title} > {message.id}')

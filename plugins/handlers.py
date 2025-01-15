# Handlers module

from logger import logger
from scheduler import main_schedule, AppScheduler

logger.debug('Loading <handlers> module')

from pyrogram import Client, filters
from pyrogram.types import Message
import enum

from database import recreate_tables, run_debug
from app_status import app_status, running_status, AppStatusType

from channel import channels_update
from post import posts_update
from processing import create_processing_schedule #, print_used_memory

class BotCommand(enum.StrEnum) :
    INSTALL = '/install'
    START = '/start'
    RESTART = '/restart'
    STAT = '/stat'
    HELP = '/help'
    STOP = '/stop'
    DEBUG = '/debug'

command_list = [ _[1:] for _ in [BotCommand.INSTALL,
                                 BotCommand.START,
                                 BotCommand.RESTART,
                                 BotCommand.STAT,
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
                    if (await channels_update(client=client, is_first=True)
                            and await posts_update(client=client, is_first=True)
                            and await create_processing_schedule(client=client)) :
                        app_status.status = AppStatusType.PROCESS_RUN
                        await message.reply('The processing was started successfully for the first time.')
                        await message.reply(f'{main_schedule.print_stat()}\n{main_schedule.print_memory()}')
                    else :
                        await message.reply('Error when starting processing...')

                case AppStatusType.APP_STOPPED | AppStatusType.PROCESS_RUN :

                    # starting after stopping from the app or after crash the app
                    await message.reply('Preparation and uploading data. Please wait...')
                    if (await posts_update(client=client, is_first=True)
                            and await create_processing_schedule(client=client)) :
                        app_status.status = AppStatusType.PROCESS_RUN
                        await message.reply('Processing has been started successful.')
                        await message.reply(f'{main_schedule.print_stat()}\n{main_schedule.print_memory()}')
                    else :
                        await message.reply('Error when starting processing...')

                # case AppStatusType.PROCESS_RUN :
                #
                    # # starting after crash the app
                    # if (await posts_update(client=client, is_first=True)
                    #         and await tasks_update(client=client)
                    #         and await create_processing_schedule(client=client)) :
                    #     app_status.status = AppStatusType.PROCESS_RUN
                    #     await message.reply('Processing has been started successful (starting after crash the app).')
                    # else :
                    #     await message.reply('Error when starting processing...')

                case AppStatusType.NOT_RUNNING:

                    logger.info('The first launch, installing is required.')
                    await message.reply('Sorry, the first launch, installing is required...')

        case BotCommand.RESTART :
            match app_status.status :

                case AppStatusType.PROCESS_RUN:
                    # restarting app during normal working
                    main_schedule.reset()
                    await message.reply('Preparation, please wait...')
                    if (await posts_update(client=client, is_first=True)
                            and await create_processing_schedule(client=client)) :
                        app_status.status = AppStatusType.PROCESS_RUN
                        await message.reply('Processing has been restarted successful.')
                        await message.reply(f'{main_schedule.print_stat()}\n{main_schedule.print_memory()}')
                    else :
                        await message.reply('Error when restarting processing...')

        case BotCommand.STAT :
            match app_status.status :

                case AppStatusType.PROCESS_RUN:
                    await message.reply(f'{main_schedule.print_stat()}\n{main_schedule.print_memory()}')

        case BotCommand.HELP :

            await message.reply(
                f'Available commands:\n'
                f'  {BotCommand.INSTALL} - 1-th run (reset all database\'s tables)\n'
                f'  {BotCommand.START} - starting processing\n'
                f'  {BotCommand.RESTART} - updating the post list and tasks schedule\n'
                f'  {BotCommand.STAT} - show how many tasks are on the schedule\n'
                f'  {BotCommand.HELP} - list of commands\n'
                f'  {BotCommand.STOP} - stopping processing\n'
            )

        case BotCommand.STOP :

            app_status.status = AppStatusType.APP_STOPPED
            running_status.set_off()
            await message.reply('Processing has been stopped...')

        case BotCommand.DEBUG :
            await run_debug(client)

        # case _:
        #     await message.reply('Unknown command, type [\\help] for more information...')


# @Client.on_message()

# @Client.on_message(is_processing_filter & filters.chat(chats=channels.lst))
# @Client.on_message(is_processing_filter & from_channel_filter & ~filters.service)
# async def echo(client, message: Message) :
#     logger.debug(message)
#     await client.send_message('me', f'Новое сообщение в канале: {message.chat.title} > {message.id}')

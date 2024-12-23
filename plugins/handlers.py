# Handlers module

from logger import logger
logger.debug('Loading handlers module')

from pyrogram import Client, filters
from pyrogram.types import Message
import enum

from database import recreate_tables, run_processing, list_channels_update
from app_status import app_status, AppStatusType


class BotCommand(enum.StrEnum) :
    INSTALL = '/install'
    START = '/start'
    UPDATE = '/update'
    HELP = '/help'
    STOP = '/stop'

command_list = [ _[1:] for _ in [BotCommand.INSTALL,
                                 BotCommand.START,
                                 BotCommand.UPDATE,
                                 BotCommand.HELP,
                                 BotCommand.STOP]]


# is_started = False      # start main bot process flag
# is_stopped = False      # stop main bot process flag


# Filters
# async def func_is_started(_, __, query: Message) -> bool:
#     return is_started

# is_started_filter = filters.create(func_is_started)

# async def func_bot_filter(_, __, message: Message) -> bool:
#     return not message.from_user.is_bot
#
# msg_bot_filter = filters.create(func_bot_filter)


# Handlers
@Client.on_message(filters.command(command_list))
async def command_handler(client: Client, message: Message) :
    logger.info(f'the "{message.text}" command has been entered')

    if app_status.status != AppStatusType.APP_STOPPED :
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
                                        'This may not be the first time the application has been\n'
                                        'launched, and resetting tables and processing have already\n'
                                        'been performed.'
                                        'For reset all tables delete <.app_status> file '
                                        'in root app directory.')

            case BotCommand.START :
                match app_status.status :
                    case AppStatusType.FIRST_RUN :
                        await message.reply('First run processing, uploading data, please wait...')
                        if await run_processing(client) :
                            app_status.status = AppStatusType.PROCESS_RUN
                            await message.reply('Processing has been started successful.')
                        else :
                            await message.reply('Error when starting processing...')

                    case AppStatusType.PROCESS_RUN :
                        if await run_processing(client) :
                            app_status.status = AppStatusType.PROCESS_RUN
                            await message.reply('Processing has been started successful.')
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
                # if db:
                #     db.close_connection()
                # is_stopped = True
                app_status.status = AppStatusType.APP_STOPPED
                await message.reply('Processing has been stopped...')
                # await client.stop()
    else :
        logger.info(f'Processing has already been stopped.')
        await message.reply('Processing is stopped, commands are unavailable!')


# @Client.on_message(is_started_filter & filters.chat('me') & msg_bot_filter)
# async def echo(client, message: Message) :
#     await client.send_message('me', f'Новое сообщение в канале: {message.chat.title} >  '
#                            f'{message.text}')
# Handlers module

from logger import mylogger
mylogger.debug('Loading handlers module')

from pyrogram import Client, filters
from pyrogram.types import Message

from database import db, first_run, another_run

is_started = False      # start main bot process flag
is_stopped = False      # stop main bot process flag


# Filters
async def func_is_started(_, __, query: Message) -> bool:
    return is_started

is_started_filter = filters.create(func_is_started)

async def func_bot_filter(_, __, message: Message) -> bool:
    return not message.from_user.is_bot

msg_bot_filter = filters.create(func_bot_filter)


# Handlers
@Client.on_message(filters.command(['install', 'start', 'help', 'stop']))
async def command_handler(client: Client, message: Message) :
    global is_started, is_stopped
    if not is_stopped:
        if message.text == '/install' and not is_started:
            mylogger.info('the "/install" command has been entered')
            if await first_run(client) :
                await message.reply('Initialization was successful!')
            else :
                await message.reply('Sorry, initialization failed.\n Try restarting the application!')

        elif message.text == '/start' and not is_started :
            mylogger.info('the "/start" command has been entered')
            if await another_run(client) :
                is_started = True
                await message.reply('Processing started...')
            else :
                await message.reply('Sorry, processing has not started (you may need to install)...')

        elif message.text == '/help' :
            mylogger.info('the "/help" command has been entered')
            if not is_started :
                await message.reply('Available commands:\n'
                                    '  /install - 1th run & reset all database\n'
                                    '  /start - starting processing\n'
                                    '  /help - list of commands\n'
                                    '  /stop - stopping processing\n'
                                    )
            else :
                await message.reply('Available commands:\n'
                                    '  /help - list of commands\n'
                                    '  /stop - stopping processing\n'
                                    )

        elif message.text == '/stop' :
            mylogger.info('the "/stop" command has been entered')
            if db:
                db.close_connection()
            is_stopped = True
            await message.reply('Processing has been stopped...')
            # await client.stop()
    else :
        await message.reply('Processing is stopped, commands are unavailable!')


@Client.on_message(is_started_filter & filters.chat('me') & msg_bot_filter)
async def echo(client, message: Message) :
    await client.send_message('me', f'Новое сообщение в канале: {message.chat.title} >  '
                           f'{message.text}')
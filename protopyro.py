import time
from webbrowser import BackgroundBrowser

import asyncio
import pyrogram.types as PyroTypes

# from pyrogram import Client, idle, filters, raw, types
# from pyrogram.filters import Filter
# from pyrogram.types import Message, Chat
# from pyrogram.enums import ParseMode
# from pyrogram.handlers import MessageHandler, RawUpdateHandler
# from typing import Dict, Union
# from pyrogram.errors import FloodWait
# from pyrogram import emoji, enums
from pyrogram import Client, filters

# Модуль для автоматизации
# import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from datetime import datetime, date

from config_py import settings
import logging
from logger import get_logger

# import pyrogram.utils as utils
#
# def get_peer_type(peer_id: int) -> str:
#     print('get_peer_type call')
#     peer_id_str = str(peer_id)
#     if not peer_id_str.startswith("-"):
#         return "user"
#     elif peer_id_str.startswith("-100"):
#         return "channel"
#     else:
#         return "chat"
#
# utils.get_peer_type = get_peer_type


channels = [-1001373128436, -1001920826299, -1001387835436, -1001490689117]

logger = get_logger(logging.INFO, to_file=False)

plugins = dict(root=settings.pyrogram.plugins.root,
               include=settings.pyrogram.plugins.include,
               exclude=settings.pyrogram.plugins.exclude)

# chats_for_filters = ['me', my_group]

# plugins = dict(root='plugins')

app = Client(name='test_pyrogram',
             api_id=settings.telegram.api_id,
             api_hash=settings.telegram.api_hash,
             plugins=plugins)


my_group = 'My_test_group20242003'
my_group_id = -1002330451219
simulative_chl = 'simulative_official'  # an outside channel
simulative_chl_id = -1001373128436
simulative_cht = 'itresume_chat'       # an outside supergroup



# @app.on_message()
# def echo(client, message):
#     app.send_video(message.chat.id, "https://tina.batseva.ru/Video/whiteGuiNew.mp4")
# async def main():
#     async with app :
#         # ошибка - для канала требует права администратора (только для каналов)
        # async for member in app.get_chat_members(simulative_chl, limit=5) :
        # для супергруппы отработало норм
        # async for member in app.get_chat_members(simulative_cht, limit=5) :
        #     print(member)
        # Get bots (работает для супергруппы / для канала нужны права админа)
#         async for bot in app.get_chat_members(simulative_chl, filter=enums.ChatMembersFilter.BOTS) :
#             print(bot)
# app.run(main())

# with app :
    # загрузка медиа (на примере фото чата)
    # with open(file='python-lib.jpg', mode='rb') as file:
         # app.set_chat_photo(my_group, photo=file)

    # история канала (все сообщения сразу или по частям)
    # hist = app.get_chat_history(my_group, limit=5)
    # for h in hist:
    #     print(h)
    #     mylogger.info(h)

    # саммари по чату (в том числе логин канала и количество участников)
    # res =app.get_chat(my_group)
    # print(res)

    # Всего диалогов (у меня) 936
    # res = app.get_dialogs_count()
    #
    # # Всего закрепленных диалогов (у меня) 3
    # res = app.get_dialogs_count(pinned_only=True)
    # print(res)
    #
    # Сколько пользователей в онлайне (работает для супергрупп)
    # online = app.get_chat_online_count(simulative_chl_id)
    # print(online)

    # Информация о нашем аккаунте
    # me = app.get_me()
    # print(me)

    # # Получаем информацию об аккаунте собеседника (Андрон)
    # you = app.get_users('andron233')
    # # print(you)
    # # Пересылаем фото из профиля Андрона в наш канал
    # #   ошибка - опознано как CHAT_PHOTO а не PHOTO
    # # app.send_photo('me', photo=you.photo.small_file_id)
    # # Получаем фото подругому
    # photos = app.get_chat_photos('andron233', limit=10)
    # # for photo in photos:
    # #     print(photo)
    # # print([*photos])  # преобразуем генератор в список
    # # Пробуем еще раз
    # # app.send_photo('me', photo=[*photos][0].file_id)
    # # Или так
    # for photo in photos:
    #     app.send_photo('me', photo=photo.file_id)


# @app.on_message(filters.chat(my_group_id) & ~filters.bot)
# def echo(client, message) :
#     app.send_message('me', f'Новое сообщение в канале: {my_group} >  '
#                            f'{message.text}')
# app.run()

# Создание своих фильтров
# def func_bot_filter(_, __, query: PyroTypes.Message) -> bool:
#     return query.from_user.is_bot
#
# msg_bot_filter = filters.create(func_bot_filter)
#
# @app.on_message(filters.chat(['me',my_group]) & ~msg_bot_filter)
# def echo(client, message: PyroTypes.Message) :
#     app.send_message('me', f'Новое сообщение в канале: {message.chat.title} >  '
#                            f'{message.text}')
# app.run()

# Создание своих фильтров через lambda
# msg_bot_filter = filters.create(lambda _, __, query: not query.from_user.is_bot)
#
# @app.on_message(filters.chat(['me',my_group]) & msg_bot_filter)
# def echo(client, message: PyroTypes.Message) :
#     app.send_message('me', f'Новое сообщение в канале: {message.chat.title} >  '
#                            f'{message.text}')
# app.run()

# Организация обработки обновлений через плагины
# Настройки папок для хендлеров а config.json
# Обработчик в handlers.py, фильтр для него в handler_filters.py
# chats_for_filters = ['me', my_group]
# app.run()

# АВТОМАТИЗАЦИЯ
async def job() :
    # time.sleep(1)
    await app.send_message('me', f'1:{datetime.now()}')

async def job2() :
    # time.sleep(1)
    await app.send_message('me', f'2:{datetime.now()}')

async def main():

    async with app:
        scheduler = AsyncIOScheduler()
        # scheduler = BackgroundScheduler()
        scheduler.add_job(job, 'interval', seconds=3)
        scheduler.add_job(job2, 'interval', seconds=4)
        scheduler.start()
        while True :
            pass
            await asyncio.sleep(1000)


asyncio.run(main())



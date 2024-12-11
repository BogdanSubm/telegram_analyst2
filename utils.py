import asyncio
import betterlogging as logging

from pyrogram import Client, idle, filters, raw, types
from pyrogram.types import Message, Chat
from pyrogram.enums import ParseMode
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from typing import Dict, Union
from pyrogram.errors import FloodWait
from pyrogram import Client, emoji, filters

from datetime import datetime, date

from config import config, API_ID, API_HASH
from pgdb import Database

DB_HOST = config['Database']['HOST']
DB_PORT = int(config['Database']['PORT'])
DB_NAME = config['Database']['NAME']
DB_USER = config['Database']['USER']
DB_PASS = config['Database']['PASS']


def _update_birthdate() -> int :
    '''
    filling in up-to-date birthday data on all channels
    :param: None
    :return: int, True - successfully, False - unsuccessfully
    '''

    db = Database( host=DB_HOST,
                   port=DB_PORT,
                   dbname=DB_NAME,
                   user=DB_USER,
                   password=DB_PASS
                   )

    db.post('select * from channels')

    pass



if __name__ == '__main__':

    if _update_birthdate(db=db):
        print('done... :) !')
    else:
        print('damn... :(')

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

# from config import config, API_ID, API_HASH
from config_py import settings
from pgdb import Database, Rows

from config_py import settings

from faker import Faker


def generate_fake_data(count: int) -> Rows :
    ''' Generating fake data for the demo function <pgdb_examples> '''
    fake = Faker('ru_RU')
    fake_rows = ((str(_), fake.company()[0:25]) for _ in range(1, count+1))
    return fake_rows


def _update_birthdate() -> int :
    '''
    filling in up-to-date birthday data on all channels
    :param: None
    :return: int, True - successfully, False - unsuccessfully
    '''

    db = Database(settings.database_connection)

    # db.post('select * from channels')
    #
    # pass
    result = db.read_rows(table_name='channel',
                          condition_statement='name >= \'Data\'',
                          limit=2)

    if result.is_successful :
        print(result.value)


    result = db.create_table(table_name='new_table',
                             columns_statement='post_id VARCHAR(10) UNIQUE, post_name VARCHAR(25)',
                             overwrite=True)

    print(result.is_successful)


    # if result.is_successful:
    #     print('A new table has been creating successfully.')
    #
    # result = db.search_table('new_table')

    # if result.is_successful:
    #     print('A new table has been creating successfully.')


    data = tuple(generate_fake_data(25))
    res = db.insert_rows(table_name='new_table', values=data)
    res = db.update_data(table_name='new_table',
                         set_statement='post_name = \'TEST2\'',
                         condition_statement='post_id in (\'10\', \'11\', \'12\', \'13\', \'15\')')
    res = db.delete_rows('new_table', 'post_name in (\'TEST2\')')
    print(res.is_successful)
    print(res.value)

    # insert_query = '''
    #     INSERT INTO new_table (post_id, post_name) VALUES (5, %s)
    #     ON CONFLICT (post_id) DO UPDATE
    #     SET post_name = EXCLUDED.post_name;
    #     '''
    res = db.count_rows('new_table')
    print(res.is_successful)
    print(res.value)

    db.close_connection()
    return True



if __name__ == '__main__':

    if _update_birthdate():
        print('done... :) !')
    else:
        print('damn... :(')

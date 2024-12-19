"""
main module
"""
from logger import mylogger
mylogger.debug('Loading <database> module')

from pyrogram import Client
from pyrogram.enums import ParseMode, ChatType

from pgdb import Database
from config_py import settings
from logger import mylogger

from config_py import is_first_run

db: Database | None = None   # global Database object


async def get_channels(client: Client) -> list[int]:
    # Iterate through all dialogs
    i = 0
    res = []
    async for dialog in client.get_dialogs() :
        if i < settings.analyst.numb_channels_process:

                                #     FOR DEBUGGING
            if dialog.chat.id in (-1001373128436, -1001920826299, -1001387835436, -1001490689117) :

            # if dialog.chat.type in (ChatType.SUPERGROUP, ChatType.CHANNEL) :
                mylogger.info(f'channel/group has been added for downloading: {dialog.chat.id} - {dialog.chat.title}')
                res.append(int(dialog.chat.id))
                i += 1
    return res


def fill_all_tables(channels):
    pass


def install_all_tables(channels) -> bool:
    global db

    if not db.create_table(table_name='channel',
                           columns_statement='''
                                id varchar(15) NOT NULL, 
                                username varchar(50) NOT NULL,
                                title varchar(100) NOT NULL, 
                                category varchar(25) NULL, 
                                creation_time timestamp NULL,
                                CONSTRAINT channel_pk PRIMARY KEY(id)
                                ''',
                           overwrite=True) :
        return False

    if not db.create_table(table_name='channel_hist',
                           columns_statement='''
                                channel_id varchar(15) NOT NULL,
	                            update_time timestamp NOT NULL,
	                            subscribers int4 NULL,
	                            CONSTRAINT channel_hist_channel_fk FOREIGN KEY (channel_id) 
	                                REFERENCES public.channel(id) ON UPDATE CASCADE
	                            ''',
                           overwrite=True) :
        return False

    if not db.create_table(table_name='post',
                           columns_statement='''
                                id bigserial NOT NULL,
                                post_id varchar(10) NOT NULL,
                                channel_id varchar(15) NOT NULL,
                                creation_time timestamp NOT NULL,
                                drop_time timestamp NULL,
                                is_advertising bool DEFAULT false NOT NULL,
                                group_post_id varchar(15) NULL,
                                content_type varchar(15) NOT NULL,
                                "content" varchar(100) NULL,
                                CONSTRAINT post_pk PRIMARY KEY (id),
                                CONSTRAINT post_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
	                            ''',
                           overwrite=True) :
        return False

    if not db.create_table(table_name='post_hist',
                           columns_statement='''                            
                                post_raw_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                "comments" int4 DEFAULT 0 NOT NULL,
                                "views" int4 DEFAULT 0 NOT NULL,
                                positives int4 DEFAULT 0 NOT NULL,
                                negatives int4 DEFAULT 0 NOT NULL,
                                neutrals int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT post_hist_post_fk FOREIGN KEY (post_raw_id) 
                                    REFERENCES public.post(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) :
        return False

    return True


async def first_run(client: Client) -> Database | bool :
    global db
    db = Database(settings.database_connection)
    if not db.is_connected :
        return False

    if is_first_run.get() :
        mylogger.info('The first launch, the beginning of initialization and filling')
        mylogger.info('Resetting of all database\'s tables get started...')
        channels = await get_channels(client)
        if install_all_tables(channels) :
            mylogger.info('Successful installation!')
            is_first_run.set_off()
            return True
        else:
            mylogger.info('Unsuccessful installation...')
            return False

    else :
        mylogger.info('This is not the first launch, the database is connected...')
        return True


async def another_run(client: Client) :
    global db

    if is_first_run.get() :
        mylogger.error('Error: the first launch, initialization and filling is required.')
        return False
    else :
        db = Database(settings.database_connection)
        if not db.is_connected :
            return False

        return True

"""
main module
"""
from logger import mylogger
mylogger.debug('Loading <database> module')

from pgdb import Database
from config_py import settings
from logger import mylogger

from config_py import is_first_run

db: Database | None = None   # global Database object


def Reinstall_all_tables(channels) -> bool:
    global db

    res = db.create_table(table_name='new_table',
            columns_statement='post_id VARCHAR(10) UNIQUE, post_name VARCHAR(30)',
                          overwrite=True
                          )
    if not res.is_successful:
        return False
    return True


def Fill_all_tables(db, channels):
    pass


async def first_run(channels) -> Database | bool :
    global db
    db = Database(settings.database_connection)
    if not db.is_connected :
        return False

    if is_first_run.get() :
        mylogger.info('The first launch, the beginning of initialization and filling')
        mylogger.info('Resetting of all database\'s tables get started...')
        if Reinstall_all_tables(channels) :
            mylogger.info('Successful reinstallation!')
            is_first_run.set_off()
        else:
            mylogger.info('Unsuccessful reinstallation...')
            return False


    else :
        mylogger.info('This is not the first launch, the database is connected...')
        return True




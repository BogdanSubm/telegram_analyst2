import pathlib
from email.policy import default
from datetime import datetime
from typing import List, Union, Annotated
from pydantic import BaseModel, Field, PositiveInt, computed_field
import argparse


class TelegramSettings(BaseModel) :
    api_id: PositiveInt = Field(exclude=True, description='my telegram api_id')
    api_hash: str = Field(exclude=True,  description='my telegram api_hash')
    bot_auth_token: str = Field(description='<reserved>')
    summary_receivers: List[str]

class DBConnectionSettings(BaseModel) :
    host: str = Field(default='localhost', description='connection host')
    port: PositiveInt = Field(default=5432, description='connection port')
    dbname: str = Field(default='tg_analyst2', description='connection data base name')
    user: str = Field(default='postgres', description='connection user')
    password: str = Field(default='123456', exclude=True, description='connection password')

class LogSettings(BaseModel) :
    path: str = Field(default='.log', description='path to save log files')
    file_name_prefix: str = Field(default='tg_an2_', description='prefix of the log file name')
    max_num_log_files: PositiveInt = Field(default=10, description='Maximum enabled number of log files')

class PyrogramPlugins(BaseModel) :
    root: str = Field(default='plugins', description='app plugins folder')
    include: list[str] = Field(default='handlers', description='included [<subfolders>] <handlers file>')
    exclude: list[str] = Field(default='', description='excluded [<subfolders>] <handlers file>')
class PyrogramSettings(BaseModel) :
    plugins: PyrogramPlugins = Field(description='plugins storage')

class AnalystSettings(BaseModel) :
    analyzing_from: datetime = Field(default=datetime.fromisoformat( "2024-10-01 00:00:00.000"),
                                     description='start time of the analysis period')
    numb_channels_process : PositiveInt = Field(default=10, description='limiting the number of channels '
                                                                        'for the first download')

class AppSettings(BaseModel):
    telegram: TelegramSettings = Field(description='telegram settings')
    database_connection: DBConnectionSettings = Field(description='data base connection settings')
    logging: LogSettings = Field(description='logging settings')
    pyrogram: PyrogramSettings = Field(description='pyrogram settings')
    analyst: AnalystSettings = Field(description='other app settings')


_settings_json_string = pathlib.Path('config.json').read_text()
settings = AppSettings.model_validate_json(_settings_json_string)


# a class for working with the flag - the first launch of the application
# (we use singleton pattern)
class FirstRunFlag() :
    __is_first_run_flag_instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__is_first_run_flag_instance is None :
            cls.__is_first_run_flag_instance = super().__new__(cls)
        return cls.__is_first_run_flag_instance

    def __init__(self):
        self.__flag = False
        try :
            with open('.first_run', 'r') as f :
                # if the flag file exists, this is not the first launch of the application
                # we are checking its integrity
                if 'succeed' in f.read() :
                    need_restore = False
                else :
                    need_restore = True

            # we restore the flag file if necessary
            if need_restore :
                with open('.first_run', 'w') as f :
                    f.write('succeed')

        except FileNotFoundError as e:
            # the flag-file is missing - this is the first launch of the application
            self.__flag = True

    def is_first(self) -> bool:
        return self.__flag

    def set_not_first(self) :
        with open('.first_run', 'w') as f :
            f.write('succeed')
        self.__flag = False



if __name__ == "__main__":
    print(settings.model_dump())
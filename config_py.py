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
    api_calls_per_minute: PositiveInt = Field(default=60,
                                              description='the number of api function calls per minute')
    api_idle_reset_time: PositiveInt = Field(default=300,
                                              description='a pause between api calls after which '
                                                          'changes by normalizer to the <api_calls_per_minute>'
                                                          ' parameter will be reset')

class DBConnectionSettings(BaseModel) :
    host: str = Field(default='localhost', description='connection host')
    port: PositiveInt = Field(default=5432, description='connection port')
    dbname: str = Field(default='tg_analyst2', description='connection data base name')
    user: str = Field(default='postgres', description='connection user')
    password: str = Field(default='123456', description='connection password')

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
    analyzing_from: datetime = Field(default=datetime.fromisoformat("2024-10-01 00:00:00.000"),
                                     description='start time of the analysis period')
    numb_channels_process: PositiveInt = Field(default=10, description='limiting the number of channels '
                                                                       'for the first download')
    size_text_fragment_for_save: PositiveInt = Field(default=256,
                                    description='the size of the text fragment from <text> (or <caption>)'
                                                ' field of the <Message> object to be saved')
    chunk_size_for_db_ops: PositiveInt = Field(default=100, description='the chunk size for a one-time'
                                                                        ' group database operation')

# class TelegramNormalizerSettings(BaseModel) :
#     api_call_before_pause: PositiveInt = Field(default=10,
#                                                description='the number of api function calls before the pause')
#     api_call_pause_duration : float = Field(default=5.0, description='the duration of the pause in seconds')
#     flood_idle_period : PositiveInt = Field(default=60, description='the duration of the period when api '
#                                                                     'functions are not accessed to reset '
#                                                                     'the normalizer counters')

class AppSettings(BaseModel):
    telegram: TelegramSettings = Field(description='telegram settings')
    database_connection: DBConnectionSettings = Field(description='data base connection settings')
    logging: LogSettings = Field(description='logging settings')
    pyrogram: PyrogramSettings = Field(description='pyrogram settings')
    analyst: AnalystSettings = Field(description='other app settings')
    # telegram_normalizer: TelegramNormalizerSettings = Field(description='settings to prevent a ban for a flood in Telegram')


_settings_json_string = pathlib.Path('config.json').read_text()
settings = AppSettings.model_validate_json(_settings_json_string)


if __name__ == "__main__":
    print(settings.model_dump())
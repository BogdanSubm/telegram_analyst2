import pathlib
from email.policy import default
from typing import List, Union, Annotated
from pydantic import BaseModel, Field, PositiveInt, computed_field
import argparse

class TelegramSettings(BaseModel):
    api_id: PositiveInt = Field(exclude=True, description='my telegram api_id')
    api_hash: str = Field(exclude=True,  description='my telegram api_hash')
    bot_auth_token: str = Field(description='<reserved>')
    summary_receivers: List[str]

class DBConnectionSettings(BaseModel):
    host: str = Field(default='localhost', description='connection host')
    port: PositiveInt = Field(default=5432, description='connection port')
    dbname: str = Field(default='tg_analyst2', description='connection data base name')
    user: str = Field(default='postgres', description='connection user')
    password: str = Field(default='123456', exclude=True, description='connection password')

class LogSettings(BaseModel):
    path: str = Field(default='.log', description='path to save log files')
    file_name_prefix: str = Field(default='tg_an2_', description='prefix of the log file name')
    max_num_log_files: PositiveInt = Field(default=10, description='Maximum enabled number of log files')

class AppSettings(BaseModel):
    telegram: TelegramSettings = Field(description='telegram setting')
    database_connection: DBConnectionSettings = Field(description='data base connection setting')
    logging: LogSettings = Field(description='logging setting')



_settings_json_string = pathlib.Path('config.json').read_text()
settings = AppSettings.model_validate_json(_settings_json_string)

if __name__ == "__main__":
    print(settings.model_dump())
import pathlib
from email.policy import default
from typing import List, Union, Annotated
from pydantic import BaseModel, Field, PositiveInt, computed_field
import argparse

class DBConnectionSettings(BaseModel):
    host: str = Field(default='localhost', description='connection host')
    port: PositiveInt = Field(default=5432, description='connection port')
    dbname: str = Field(default='tg_analyst2', description='connection data base name')
    user: str = Field(default='postgres', description='connection user')
    password: str = Field(default='123456', exclude=True, description='connection password')

class AppSettings(BaseModel):
    telegram_api_id: int = Field(exclude=True, description='my telegram api_id')
    telegram_api_hash: str = Field(exclude=True,  description='my telegram api_hash')
    telegram_bot_auth_token: str = Field(description='<reserved>')
    openai_api_key: str = Field(description='<reserved>')
    telegram_summary_receivers: List[str]
    database_connection: DBConnectionSettings = Field(description='data base connection setting')

_settings_json_string = pathlib.Path('config.json').read_text()
settings = AppSettings.model_validate_json(_settings_json_string)

if __name__ == "__main__":
    print(settings.model_dump())
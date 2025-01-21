from datetime import datetime
from pathlib import Path, PurePath
from pydantic import BaseModel, Field, PositiveInt, computed_field
import logging

logger_level = dict(NOTSET=logging.NOTSET,
                    DEBUG=logging.DEBUG,
                    INFO=logging.INFO,
                    WARNING=logging.WARNING,
                    ERROR=logging.ERROR,
                    CRITICAL=logging.CRITICAL)

class TelegramSettings(BaseModel) :
    api_id: PositiveInt = Field(exclude=True, description='my telegram api_id')
    api_hash: str = Field(exclude=True,  description='my telegram api_hash')
    # bot_auth_token: str = Field(description='<reserved>')
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
    level: str = Field(default='INFO', description='level of logging')
    @computed_field
    def level_logging(self) -> PositiveInt:
        return logger_level[self.level]
    to_file: bool = Field(default=False, description='file or console mode of the registrar')
    logs_folder_path: str = Field(default='.log', description='path to save log files')
    file_name_prefix: str = Field(default='tg_an2_', description='prefix of the log file name')
    max_num_log_files: PositiveInt = Field(default=10, description='Maximum enabled number of log files')



class PyrogramPlugins(BaseModel) :
    root: str = Field(default='plugins', description='app plugins folder')
    include: list[str] = Field(description='included [<subfolders>] <handlers file>')
    exclude: list[str] = Field(description='excluded [<subfolders>] <handlers file>')
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
    chunk_size_for_tg_ops: PositiveInt = Field(default=100, description='the chunk size for a read operation in '
                                                                          'group api-functions')
    media_group_post_ordering_base: int = Field(default=1, ge=0, le=1, description='the base for numbering '
                                                                                   'posts in a media group')
    channel_selection_filter: list[int] = Field(default='', description='channel selection filter')

class ScheduleUpdateLogFile(BaseModel) :
    hour: int = Field(default=0, ge=0, le=23, description='hour of the start time for log file update')
    minute: int = Field(default=0, ge=0, le=59, description='minutes of the start time for log file update')
    second: int = Field(default=0, ge=0, le=59, description='seconds of the start time for log file update')
class ScheduleUpdateChannels(BaseModel) :
    hour: int = Field(default=0, ge=0, le=23, description='hour of the start time for the channel update task')
    minute: int = Field(default=0, ge=0, le=59, description='minutes of the start time for the channel update task')
    second: int = Field(default=0, ge=0, le=59, description='seconds of the start time for the channel update task')
class ScheduleUpdatePosts(BaseModel) :
    hours: list[int] = Field(description='hours of the start time for the posts update task')
    minutes: list[int] = Field(description='minutes of the start time for the posts update task')
    seconds: list[int] = Field(description='seconds of the start time for the posts update task')
class ScheduleSettings(BaseModel) :
    update_log_file: ScheduleUpdateLogFile = Field(description='the start time of the task for change the log file')
    update_channels: ScheduleUpdateChannels = Field(description='task start time for channels')
    update_posts: ScheduleUpdatePosts = Field(description='task start time for channels')
    post_observation_days: list[PositiveInt] = Field(description='list of all observation day numbers')
    min_duration_observation_task: PositiveInt = Field(default=1, description='minimum duration of the observation '
                                                                              'task in seconds')

class AppSettings(BaseModel):
    telegram: TelegramSettings = Field(description='telegram settings')
    database_connection: DBConnectionSettings = Field(description='data base connection settings')
    logging: LogSettings = Field(description='logging settings')
    pyrogram: PyrogramSettings = Field(description='pyrogram settings')
    analyst: AnalystSettings = Field(description='main app settings')
    schedules: ScheduleSettings = Field(description='schedules settings')


dir_name = PurePath(__file__).parent


_settings_json_string = Path(PurePath.joinpath(dir_name, 'config.json')).read_text()
settings = AppSettings.model_validate_json(_settings_json_string)


if __name__ == "__main__":
    print(settings.model_dump())
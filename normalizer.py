# api call flow normalizer
from logger import logger
logger.debug('Loading <normalizer> module')

import asyncio
from pyrogram.errors import FloodWait
from typing import Any, Callable
from datetime import datetime, timedelta

from config_py import settings

API_CALL_BEFORE_PAUSE = settings.telegram_normalizer.api_call_before_pause   # 1 time
API_CALL_PAUSE_DURATION = settings.telegram_normalizer.api_call_pause_duration   # 0.8 sec
FLOOD_IDLE_PERIOD = settings.telegram_normalizer.flood_idle_period   # 60 sec

# a class for prevent a ban for a flood in Telegram (we use singleton pattern)
class Normalizer() :
    __normalizer_instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__normalizer_instance is None :
            cls.__normalizer_instance = super().__new__(cls)
        return cls.__normalizer_instance

    def __init__(self):
        self.__time_start = 0   # start time (reserved)
        self.__last_call = 0    # time of last <func> call
        self.__count_calls = 0  # number of calls
        self.__pause_duration = API_CALL_PAUSE_DURATION     # the duration of the pause between the call blocks

    async def run(self, func, *args, **kwargs) -> Any :
        while True:

            try:
                if self.__count_calls == 0 :
                    self.__time_start = self.__last_call = datetime.now()
                else:
                    if (datetime.now() - self.__last_call).total_seconds() > FLOOD_IDLE_PERIOD :
                        self.__count_calls = 0
                        self.__pause_duration = API_CALL_BEFORE_PAUSE
                        continue

                if self.__count_calls == API_CALL_BEFORE_PAUSE:
                    await asyncio.sleep(self.__pause_duration)  # wait
                    self.__count_calls = 0
                    continue

                res = await func(*args, **kwargs)

                self.__last_call = datetime.now()
                self.__count_calls += 1
                logger.debug(f'calls before pause: {self.__count_calls}')

            except FloodWait as e :
                logger.error(f'Telegram warning:{e}')
                await asyncio.sleep(e.value+1)  # Wait "value" seconds before continuing
                self.__count_calls = 0
                self.__pause_duration += 1  # added 1 second
                logger.debug(f'Set pause duration to: {self.__pause_duration}')
                continue

            except Exception as e:
                logger.error(f'Telegram error: {e}')
                return None

            return res
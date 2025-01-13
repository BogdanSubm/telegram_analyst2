# api call flow normalizer
# from database import normalizer
from logger import logger
logger.debug('Loading <normalizer> module')

import asyncio
from pyrogram.errors import FloodWait
from typing import Any
from datetime import datetime
from pyrogram.errors import BadRequest

from config_py import settings
# global normalizer


# a class for prevent a ban for a flood in Telegram (we use singleton pattern)
class Normalizer :
    __normalizer_instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__normalizer_instance is None :
            cls.__normalizer_instance = super().__new__(cls)
        return cls.__normalizer_instance

    def __init__(self):
        self.__last_call = datetime.now()    # time of last <func> call
        self.__calls_per_minute = settings.telegram.api_calls_per_minute
        self.__delta = 60 / self.__calls_per_minute

    async def run(self, func = None, *args, **kwargs) -> Any | None :
        while True:
            try:
                delta = (datetime.now() - self.__last_call).total_seconds()
                if delta < self.__delta :
                    await asyncio.sleep(self.__delta - delta)  # wait

                elif delta > settings.telegram.api_idle_reset_time :
                    self.__calls_per_minute = settings.telegram.api_calls_per_minute
                    self.__delta = 60 / self.__calls_per_minute

                self.__last_call = datetime.now()
                if func is not None :
                    res = await func(*args, **kwargs)
                else:
                    res = None

            except FloodWait as e :
                logger.error(f'Telegram warning:{e}')
                await asyncio.sleep(e.value)  # Wait "value" seconds before continuing

                self.__last_call = datetime.now()
                self.__calls_per_minute *= 0.8   # reducing the number of calls per minute by 20%
                self.__delta =  60 / self.__calls_per_minute
                logger.debug(f'Set acceptable number of calls per minute to: {self.__delta}')
                continue

            except BadRequest as e:
                raise BadRequest()

            except Exception as e:
                logger.error(f'Telegram error: {e}')
                return None

            return res


normalizer = Normalizer()


# API_CALL_BEFORE_PAUSE = settings.telegram_normalizer.api_call_before_pause   # 1 time
# API_CALL_PAUSE_DURATION = settings.telegram_normalizer.api_call_pause_duration   # 0.8 sec
# FLOOD_IDLE_PERIOD = settings.telegram_normalizer.flood_idle_period   # 60 sec
#
# # a class for prevent a ban for a flood in Telegram (we use singleton pattern)
# class Normalizer() :
#     __normalizer_instance = None
#
#     def __new__(cls, *args, **kwargs):
#         if cls.__normalizer_instance is None :
#             cls.__normalizer_instance = super().__new__(cls)
#         return cls.__normalizer_instance
#
#     def __init__(self):
#         self.__time_start = 0   # start time (reserved)
#         self.__last_call = 0    # time of last <func> call
#         self.__count_calls = 0  # number of calls
#         self.__pause_duration = API_CALL_PAUSE_DURATION     # the duration of the pause between the call blocks
#
#     async def run(self, func, *args, **kwargs) -> Any :
#         while True:
#
#             try:
#                 if self.__count_calls == 0 :
#                     self.__time_start = self.__last_call = datetime.now()
#                 else:
#                     if (datetime.now() - self.__last_call).total_seconds() > FLOOD_IDLE_PERIOD :
#                         self.__count_calls = 0
#                         self.__pause_duration = API_CALL_BEFORE_PAUSE
#                         continue
#
#                 if self.__count_calls == API_CALL_BEFORE_PAUSE:
#                     await asyncio.sleep(self.__pause_duration)  # wait
#                     self.__count_calls = 0
#                     continue
#
#                 res = await func(*args, **kwargs)
#
#                 self.__last_call = datetime.now()
#                 self.__count_calls += 1
#                 logger.debug(f'calls before pause: {self.__count_calls}')
#
#             except FloodWait as e :
#                 logger.error(f'Telegram warning:{e}')
#                 await asyncio.sleep(e.value+1)  # Wait "value" seconds before continuing
#                 self.__count_calls = 0
#                 self.__pause_duration *= 1.5  # added 50% duration
#                 logger.debug(f'Set pause duration to: {self.__pause_duration}')
#                 continue
#
#             except Exception as e:
#                 logger.error(f'Telegram error: {e}')
#                 return None
#
#             return res
#


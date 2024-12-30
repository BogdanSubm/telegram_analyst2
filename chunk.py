# api call flow normalizer
from logger import logger
logger.debug('Loading <chunk> module')

import asyncio
from normalizer import Normalizer
from config_py import settings

# a simple class for reading data with the necessary anti-flood pause
class Chunk :

    def __init__(self, normalizer: Normalizer, chunk_size: int = settings.analyst.chunk_size_for_read_ops):
        self.__chunk_size = chunk_size
        self.__chunk_filled = self.__chunk_size
        self.__normalizer = normalizer

    async def one_reading(self) -> None :
        if self.__chunk_filled == 0 :
            await self.__normalizer.run()
            self.__chunk_filled =  self.__chunk_size
        else :
            self.__chunk_filled -= 1


async def chunks(lst, chunk_size) :
    ''' Auxiliary splitting function '''
    for i in range(0, len(lst), chunk_size) :
        yield lst[i:i + chunk_size]

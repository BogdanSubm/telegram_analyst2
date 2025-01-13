# Scheduler module

from logger import logger
logger.debug('Loading <scheduler> module')

from apscheduler.schedulers.asyncio import AsyncIOScheduler


# main_schedule = AsyncIOScheduler()


class AppScheduler() :
    def __init__(self) :
        self.__not_started = True
        self.__scheduler = AsyncIOScheduler()

    def add_job(self, *args, **kwargs) :
        self.__scheduler.add_job(*args, **kwargs)

    def start(self) :
        if self.__not_started:
            self.__scheduler.start()
            self.__not_started = False

    def stop(self, *args, **kwargs) :
        self.__scheduler.shutdown(*args, **kwargs)

    def pause(self) :
        self.__scheduler.pause()

    def resume(self) :
        self.__scheduler.resume()

    def restart(self) :
        self.stop()
        self.__scheduler = AsyncIOScheduler()
        self.__not_started = True
        self.start()

    def print_stat(self) -> str :
        report = f'Total tasks in progress: {len(self.__scheduler.get_jobs())}'
        logger.info(report)
        return report

    def print_tasks(self, *args, **kwargs) :
        logger.info(self.__scheduler.print_jobs(*args, **kwargs))



main_schedule = AppScheduler()
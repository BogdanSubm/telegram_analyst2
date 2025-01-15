# Scheduler module

from logger import logger
logger.debug('Loading <scheduler> module')

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import psutil

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

    # def restart(self) :
    #     self.stop()
    #     self.__scheduler = AsyncIOScheduler()
    #     self.__not_started = True
    #     self.start()

    def reset(self) :
        self.pause()
        for job in self.__scheduler.get_jobs() :
            self.__scheduler.remove_job(job_id=job.id)
        self.resume()


    def print_stat(self) -> str :
        report = f'Total tasks in progress: {len(self.__scheduler.get_jobs())}'
        logger.info(report)
        return report

    @staticmethod
    def print_memory() -> str :
        report = f'Used memory: {psutil.Process().memory_info().rss / 1024 ** 2:.2f} Mb'
        logger.info(report)
        return report

    def print_tasks(self, *args, **kwargs) :
        self.__scheduler.print_jobs(*args, **kwargs)



main_schedule = AppScheduler()
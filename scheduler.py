# Scheduler module
from logger import logger
logger.debug('Loading <scheduler> module')

from apscheduler.schedulers.asyncio import AsyncIOScheduler

main_schedule = AsyncIOScheduler()


# class AppScheduler() :
#     def __init__(self) :
#         self.__not_started = True
#         self.scheduler = AsyncIOScheduler()
#
#     def add_task(self, *args, **kwargs) :
#         self.scheduler.add_job(*args, **kwargs)
#
#     def start(self) :
#         if self.__not_started:
#             self.scheduler.start()
#             self.__not_started = False
#
#     def stop(self, *args, **kwargs) :
#         self.scheduler.shutdown(*args, **kwargs)
#
#     def print_tasks(self, *args, **kwargs) :
#         self.scheduler.print_jobs(*args, **kwargs)


# main_schedule = AppScheduler()
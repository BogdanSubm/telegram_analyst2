# Scheduler module
from app_types import DBTaskPlan
from logger import logger
logger.debug('Loading <scheduler> module')

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pgdb import Database
from config_py import settings




# main_schedule = AsyncIOScheduler()


class AppScheduler() :
    def __init__(self) :
        self.__not_started = True
        self.scheduler = AsyncIOScheduler()

    def add_job(self, *args, **kwargs) :
        self.scheduler.add_job(*args, **kwargs)

    def start(self) :
        if self.__not_started:
            # self.load_tasks()
            self.scheduler.start()
            self.__not_started = False

    def stop(self, *args, **kwargs) :
        self.scheduler.shutdown(*args, **kwargs)

    #
    # def add_post_tasks(self, db:Database, chat_id=int, post_id=int)
    #
    #     task_records: list[DBTaskPlan] = []
    #     for day in settings.schedules.post_observation_days :
    #         if ((base_time + timedelta(days=day) >= current_time)
    #                 or (day == settings.schedules.post_observation_days[-1])) :
    #             # adding a task to the schedule if the scheduled time is greater than or equal to the current time
    #             # or it is the last day of all observation days.
    #             if main_schedule.add_task(
    #                     DBTaskPlan(
    #                         channel_id=chat_id,
    #                         post_id=post_id,
    #                         observation_day=day,
    #                         planned_at=base_time + timedelta(days=day),
    #                         started_at=None,
    #                         completed_at=None
    #                     ),
    #             ) :
    #
    #     res = db.insert_rows(table_name='task_plan', values=tuple(task_records))
    #     if not res.is_successful :
    #         logger.info(f'sorry, we couldn\'t scheduled task for post: id [{post_id}] in <task_plan> table. ')
    #         return False
    #
    #
    #
    #
    #     res = db.insert_rows(table_name='task_plan', values=tuple(task,))
    #     if not res.is_successful :
    #         logger.error(f'Error when saving a task {task} to the schedule.')
    #         return False
    #
    #     self.add_job(
    #         func=posts_update,
    #         kwargs={'client': client},
    #         trigger='cron',
    #         hour=h,
    #         minute=minutes[i],
    #         second=seconds[i]
    #     )
    #     self.scheduler.add_job(*args, **kwargs)
    #
    # DBTaskPlan(
    #     channel_id=chat_id,
    #     post_id=post_id,
    #     observation_day=day,
    #     planned_at=base_time + timedelta(days=day),
    #     started_at=None,
    #     completed_at=None
    #
    # def get_tasks(self) :
    #
    #
    # def load_tasks(self) :
    #
    #     for
    #     ...


    def print_tasks(self, *args, **kwargs) :
        self.scheduler.print_jobs(*args, **kwargs)




main_schedule = AppScheduler()
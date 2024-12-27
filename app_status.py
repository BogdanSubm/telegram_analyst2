
if __name__ != '__main__' :
    from logger import logger
    logger.debug('Loading <app_status> module')


import enum
class AppStatusType(enum.StrEnum) :
    NOT_RUNNING = 'not running'
    FIRST_RUN = 'first run'
    PROCESS_RUN = 'processing'
    UPDATE_RUN = 'update'
    APP_STOPPED = 'stopped'


# the class for working with the flag that is about the current status of the application
# (we use singleton pattern)
class AppStatus() :
    __is_app_status_instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__is_app_status_instance is None :
            cls.__is_app_status_instance = super().__new__(cls)
        return cls.__is_app_status_instance

    def __init__(self):
        self.__status = ''
        try :
            with open('.app_status', 'r') as f :
                # if the status-file exists, this is not the first launch of the application
                # we are checking its integrity
                self.__status = f.read()

        except FileNotFoundError as e :
            # the flag-file is missing - this is the first launch of the application
            try:
                with open('.app_status', 'w') as f :
                    self.__status = AppStatusType.NOT_RUNNING
                    f.write(self.__status)
            except Exception as e :
                logger.error(f'Error: the status file cannot be saved: {e}')

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, new_status: AppStatusType):
        try :
            with open('.app_status', 'w') as f :
                self.__status = new_status
                f.write(self.__status)
        except Exception as e :
            logger.error(f'Error: the status file cannot be saved: {e}')

app_status = AppStatus()


if __name__ == '__main__' :
    import logging
    from logger import get_logger, logger
    logger = get_logger(logging.DEBUG, to_file=False)

    flag =  AppStatus()
    print(flag.status)
    flag.status = AppStatusType.FIRST_RUN
    print(flag.status)
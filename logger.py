"""
The module of functions for logging
"""
from datetime import datetime
import os
import re
import logging

from config_py import settings


logger: logging.Logger | None = None    # Global variable for save only one instance of the logger
                                        # the command for use the logger in another module:
                                        #   <from logger import logger>

format_line = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class ColoredFormatter(logging.Formatter):
    COLORS = {'DEBUG': '\033[94m', 'INFO': '\033[92m', 'WARNING': '\033[93m',
              'ERROR': '\033[91m', 'CRITICAL': '\033[95m'}

    def format(self, record):
        log_fmt = f"{self.COLORS.get(record.levelname, '')}{format_line}\033[0m"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def _init_logging() -> str :
    prefix_name= settings.logging.file_name_prefix
    path = settings.logging.path
    max_num_files = settings.logging.max_num_log_files

    new_log_name = (prefix_name + datetime.now().strftime('%Y-%m-%d_%H-%M') + '.log')

    if not os.path.isdir(path) :
        # Creating a log folder if it doesn't exist yet
        os.mkdir(path)

    # Reading a log folder
    list_dir = os.listdir(path)
    # Compiling "re"-pattern for the name of log
    regexp = re.compile(rf'{prefix_name}'+r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log')
    # Finding all of logs files
    list_logs = []
    for el in list_dir :
        if regexp.match(el, 0) :
            list_logs.append(el)
    # Sorting the log list by file creation time in reverse order
    list_logs.sort(reverse=True)
    if new_log_name in list_logs[:max_num_files] :
        start_pos = max_num_files
    else :
        start_pos = max_num_files - 1
    if list_logs[start_pos :] :
        for f in list_logs[start_pos :] :
            os.remove(os.path.join(path, f))

    return str(os.path.join(path, new_log_name))


def get_logger(level: int = logging.DEBUG, to_file: bool = True) -> logging.Logger:
    global logger
    if not logger:  # only one copy of the registrar at a time
        logger = logging.getLogger('tgan2_logger')
        logger.setLevel(level)

        if to_file :
            handler = logging.FileHandler(_init_logging())
            formatter = logging.Formatter(format_line)
        else :
            handler = logging.StreamHandler()
            formatter = ColoredFormatter()

        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

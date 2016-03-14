from __future__ import absolute_import, print_function

import os
import fourpisky.env_vars as fps_env_vars
from celery import Celery

from celery.signals import after_setup_task_logger
import logging



fps_app = Celery('fourpisky',
                 broker='amqp://guest@localhost//',
                 include=['fourpisky.tasks'])

if fps_env_vars.celery_config_module in os.environ:
    try:
        fps_app.config_from_envvar(fps_env_vars.celery_config_module, force=True)
    except ImportError:
        print("Could not import celery config, check {} "
              "environment variable.".format(fps_env_vars.celery_config_module))
        raise
else:
    fps_app.config_from_object('fourpisky.taskqueue.default_config')


@after_setup_task_logger.connect
def setup_task_logfiles(**kwargs):
    logfile_path = fps_app.conf.CELERY_TASK_LOGFILE
    debug_logfile_path = fps_app.conf.CELERY_TASK_DEBUG_LOGFILE

    log_chunk_bytesize = 5e6
    full_date_fmt = "%y-%m-%d (%a) %H:%M:%S"
    named_formatter = logging.Formatter(
                            '%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                            # '%(asctime)s:%(levelname)s:%(message)s',
                            full_date_fmt)

    info_logger = logging.handlers.RotatingFileHandler(logfile_path,
                            maxBytes=log_chunk_bytesize, backupCount=10)
    info_logger.setFormatter(named_formatter)
    info_logger.setLevel(logging.INFO)
    info_logger.propagate = False

    debug_logger = logging.handlers.RotatingFileHandler(debug_logfile_path,
                            maxBytes=log_chunk_bytesize, backupCount=10)
    debug_logger.setFormatter(named_formatter)
    debug_logger.setLevel(logging.DEBUG)
    debug_logger.propagate = False

    logger = logging.getLogger('fourpisky')
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.handlers.append(info_logger)
    logger.handlers.append(debug_logger)
    from logging_tree import printout
    printout()


if __name__ == '__main__':
    fps_app.start()
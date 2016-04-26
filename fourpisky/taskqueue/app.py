from __future__ import absolute_import, print_function

import os
import fourpisky.env_vars as fps_env_vars
import fourpisky.log_config as log_config
from celery import Celery

from celery.signals import after_setup_task_logger
import logging

fps_app = Celery('fourpisky',
                 broker='amqp://guest@localhost//',
                 include=['fourpisky.taskqueue.tasks'])

if fps_env_vars.celery_config_module in os.environ:
    try:
        fps_app.config_from_envvar(fps_env_vars.celery_config_module,
                                   force=True)
    except ImportError:
        print("Could not import celery config, check {} "
              "environment variable.".format(fps_env_vars.celery_config_module))
        raise
else:
    fps_app.config_from_object('fourpisky.taskqueue.default_config')


class NoTaskQueueFilter(logging.Filter):
    def filter(self, record):
        return not record.name.startswith('fourpisky.taskqueue')

class NoFpsFilter(logging.Filter):
    def filter(self, record):
        return not (record.name.startswith('fourpisky')
            or record.name.startswith('voeventdb'))


@after_setup_task_logger.connect
def setup_task_logfiles(**kwargs):
    root_logfile_path = fps_app.conf.CELERY_LOG_PATHSTEM
    task_logfile_path = fps_app.conf.CELERY_TASK_LOG_PATHSTEM

    rootlogger=logging.getLogger()
    rootlogger.handlers[0].addFilter(NoFpsFilter())
    log_config.setup_email_errorhandler(rootlogger)
    log_config.setup_logfile_handlers(rootlogger,
                                      logfile_pathstem=root_logfile_path)

    for pkg_name in ('voeventdb', 'fourpisky'):
        pkglogger = logging.getLogger(pkg_name)
        # # Don't intermix package output with celery output:
        # pkglogger.propagate = False
        pkglogger.setLevel(logging.DEBUG)
        log_config.setup_logfile_handlers(pkglogger,
                                          logfile_pathstem=task_logfile_path)


    from logging_tree import printout
    printout()


if __name__ == '__main__':
    fps_app.start()

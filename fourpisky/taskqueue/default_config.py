
CELERYD_CONCURRENCY = 2
CELERYD_TASK_TIME_LIMIT = 120
CELERY_TASK_LOGFILE = './fps_celery_tasks.log'
CELERY_TASK_DEBUG_LOGFILE = './fps_celery_tasks.debug.log'
FPS_ACTIONS_LOGFILE = './fps_actions.debug.log'

CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'msgpack'
CELERY_ACCEPT_CONTENT = ['msgpack',]
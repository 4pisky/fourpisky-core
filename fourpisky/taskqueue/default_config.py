
CELERYD_CONCURRENCY = 2
CELERYD_TASK_TIME_LIMIT = 120


CELERY_LOG_PATHSTEM = './fps_celery_root'
# Logs everything from the tasks run,
# but filters out the celery 'task received' / 'task successful' msgs.
CELERY_TASK_LOG_PATHSTEM = './fps_celery_tasks'

CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'msgpack'
CELERY_ACCEPT_CONTENT = ['msgpack',]
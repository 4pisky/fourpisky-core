#!/usr/bin/env bash

PYTHONPATH=./${PYTHONPATH:+:${PYTHONPATH}} \
FPS_CELERY_CONFIG="celery_test_config" \
FPS_USE_DUMMY_EMAIL=1 \
celery -A fourpisky.taskqueue.tasks worker --loglevel=info 

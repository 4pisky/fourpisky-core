#!/usr/bin/env bash


FPS_CELERY_CONFIG="celery_test_config" \
FPS_DUMMY_MODE=1 \
FPS_VOEVENTDB_DBNAME="voeventcache" \
celery -A fourpisky.taskqueue.tasks worker \
    --loglevel=info \
    --concurrency=4 \

#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
COMET_PLUGIN_DIR="$( dirname $SCRIPT_DIR)/comet_plugin"

LOCALIVORN=ivo://fpstoolstest/test_host


PYTHONPATH=${COMET_PLUGIN_DIR}${PYTHONPATH:+:${PYTHONPATH}} \
/usr/bin/env twistd -n comet \
    --receive \
    --broadcast \
    --local-ivo=$LOCALIVORN \
    --verbose \
    --verbose \
    --celery-queue \

#    --print-event \


#    --remote=$REMOTE \
#    --cmd=$HANDLER




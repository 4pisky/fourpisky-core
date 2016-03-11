#!/usr/bin/env bash



LOCALIVORN=ivo://fpstoolstest/test_host

# This is the script that comet will pass every VOEvent to, for processing:
#HANDLER=./process_voevent_from_stdin_1.py

# The remote broker that we will subscribe to. The '--remote' flag can be
# repeated with different addresses if you want to  listen to multiple remotes.
#REMOTE=voevent.4pisky.org


# Put it all together:
/usr/bin/env twistd -n comet \
    --receive \
    --broadcast \
    --local-ivo=$LOCALIVORN \
#    --verbose \
#    --remote=$REMOTE \
#    --cmd=$HANDLER




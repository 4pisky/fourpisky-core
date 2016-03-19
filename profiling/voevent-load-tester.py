#!/usr/bin/env python
"""
Written to pull in my own voevent-generation code with the minimum of thought.

To get higher throughput, see:
    https://github.com/jdswinbank/Comet/blob/paper/scripts/vtp-bench.py
(Which actually looks quite easy to modify).

However, this is *marginally* useful to test the performance of using
comet-sendvo via a subprocess call; cf
https://github.com/jdswinbank/Comet/issues/36

"""

import multiprocessing
import fourpisky
import fourpisky.comms.comet
import fourpisky.voevent
import logging
import datetime

import time
import threading
from functools import wraps

import signal
import sys

logger = logging.getLogger('load-test')


def rate_limited(max_per_second):
    """
    Decorator that make functions not be called faster than
    """
    lock = threading.Lock()
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_time_called = [0.0]

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            elapsed = time.clock() - last_time_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            lock.release()

            ret = func(*args, **kwargs)
            last_time_called[0] = time.clock()
            return ret

        return rate_limited_function

    return decorate


def init_worker_to_ignore_sigint():
    #Use the readymade 'SIG_IGN' (ignore signal) handler to handle SIGINT
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def generate_and_send_packet():
    now = datetime.datetime.utcnow()
    # uuid =fourpisky.voevent.generate_stream_id(now)
    # return "UUID:"+uuid
    try:
        test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
        dummy_packet = fourpisky.voevent.create_skeleton_4pisky_voevent(
            substream="DUMMYPACKET",
            stream_id=fourpisky.voevent.generate_stream_id(now),
            date=now
        )
        sendpacket = dummy_packet
        # sendpacket = test_packet
        ivorn = sendpacket.attrib['ivorn']
        fourpisky.comms.comet.send_voevent(sendpacket)
    except Exception as e:
        return "Error sending {}:\n {}".format(
            ivorn, e.output)
    return "Sent {}".format(ivorn)


def logger_callback(summary):
    """Used to return the 'job complete' log message in the master thread."""
    if summary.startswith('Error'):
        logger.error('There was an error:')
        logger.error(summary)
    else:
        pass
        # logger.info('*** Job complete: ' + summary)


def main():
    n_threads = 6
    n_events = 200
    n_per_second = 15
    pool = multiprocessing.Pool(n_threads,
                                initializer=init_worker_to_ignore_sigint)
    results = []
    start = datetime.datetime.utcnow()

    @rate_limited(n_per_second)
    def add_job_to_pool():
        results.append(pool.apply_async(generate_and_send_packet,
                                        callback=logger_callback
                                        ))

    logging.info("Beginning run...")
    try:
        for i in range(n_events):
            logger.debug('Sending event #{}'.format(i))
            add_job_to_pool()
    except KeyboardInterrupt:
        logger.warning("Caught KeyboardInterrupt, terminating")
        pool.terminate()
        pool.join()
        return 1

    logging.info("... Done.")

    n_fails = 0
    resultset = set()
    for obj in results:
        # print res.get(), type(res.get())
        summary = obj.get()
        if summary.startswith('Error'):
            n_fails += 1
        resultset.add(summary)
    end = datetime.datetime.utcnow()

    assert len(resultset) == len(results)
    time_taken = (end - start).total_seconds()
    print "Sent {} events in {} seconds".format(
        n_events, time_taken
    )
    print "Rate: {} /second ".format(n_events / time_taken)
    print "Or {} /second/thread".format(n_events / time_taken / n_threads)
    print "{} failed (proportion {})".format(n_fails, float(n_fails) / n_events)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())


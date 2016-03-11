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


logger = logging.getLogger('load-test')

def generate_and_send_packet():
    now = datetime.datetime.utcnow()
    # uuid =fourpisky.voevent.generate_stream_id(now)
    # return "UUID:"+uuid
    try:
        test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
        ivorn = test_packet.attrib['ivorn']
        fourpisky.comms.comet.send_voevent(test_packet)
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
    n_events = 1000
    pool = multiprocessing.Pool(n_threads)
    results=[]
    start = datetime.datetime.utcnow()
    for i in range(n_events):
        # print "Spawning number", i
        # logger_callback(generate_and_send_packet())
        # continue
        results.append(pool.apply_async(generate_and_send_packet,
                                        callback=logger_callback
                                        ))

    n_fails = 0
    resultset = set()
    for obj in results:
        # print res.get(), type(res.get())
        summary = obj.get()
        if summary.startswith('Error'):
            n_fails+=1
        resultset.add(summary)
    end = datetime.datetime.utcnow()

    assert len(resultset)== len(results)
    time_taken = (end - start).total_seconds()
    print "Sent {} events in {} seconds".format(
        n_events, time_taken
    )
    print "Rate: {} /second ".format(n_events/time_taken)
    print "Or {} /second/thread".format(n_events/time_taken/n_threads)
    print "{} failed (proportion {})".format(n_fails, float(n_fails)/n_events)




if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info("Beginning run...")
    main()
    logging.info("... Done.")
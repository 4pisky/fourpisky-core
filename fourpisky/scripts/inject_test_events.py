import click
from fourpisky.comms import comet
import logging
import logging.handlers
from fourpisky.voevent import create_alarrm_obs_test_event
import voeventparse as vp



def main(logfile, process_function=comet.send_voevent):
    setup_logging(logfile)
    logger = logging.getLogger('inject-test-event')

    v = create_alarrm_obs_test_event()
    process_function(v)
    logger.info(
        "Processed test Voevent: {}".format(v.attrib['ivorn']))


def save_to_tmpfile(voevent):
    testpacket_tmpfile_path = "/tmp/fps_alarrm_testpacket.xml"
    with open(testpacket_tmpfile_path, 'w') as f:
        logger = logging.getLogger()
        vp.dump(voevent, f)
        logger.debug("Saved packet to "+testpacket_tmpfile_path)

@click.command()
@click.option('--logfile', type=click.Path(),
              default='inject_test_events.log')
@click.option('--testrun', is_flag=True)
def cli(logfile, testrun):
    """
     Trivial wrapper about main to create a command line interface entry-point.
    """
    if testrun:
        main(logfile, process_function=save_to_tmpfile)
    else:
        main(logfile)

def setup_logging(logfile_path):
    """
    Set up INFO- and DEBUG-level logfiles
    """
    full_date_fmt = "%y-%m-%d (%a) %H:%M:%S"
    short_date_fmt = "%H:%M:%S"


    std_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s',
                                      short_date_fmt)

    named_formatter = logging.Formatter(
                            '%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                            # '%(asctime)s:%(levelname)s:%(message)s',
                            full_date_fmt)

    #Get to the following size before splitting log into multiple files:
    log_chunk_bytesize = 5e6

    info_logfile_path = logfile_path
    debug_logfile_path = logfile_path+".debug"

    info_logger = logging.handlers.RotatingFileHandler(info_logfile_path,
                            maxBytes=log_chunk_bytesize, backupCount=10)
    info_logger.setFormatter(named_formatter)
    info_logger.setLevel(logging.INFO)

    debug_logger = logging.handlers.RotatingFileHandler(debug_logfile_path,
                            maxBytes=log_chunk_bytesize, backupCount=10)
    debug_logger.setFormatter(named_formatter)
    debug_logger.setLevel(logging.DEBUG)

    stdout_logger = logging.StreamHandler()
    stdout_logger.setFormatter(std_formatter)
    # stdout_logger.setLevel(logging.INFO)
    stdout_logger.setLevel(logging.DEBUG)

    #Set up root logger
    logger = logging.getLogger()
    logger.handlers=[]
    logger.setLevel(logging.DEBUG)
    logger.addHandler(info_logger)
    logger.addHandler(debug_logger)
    logger.addHandler(stdout_logger)
    # logging.getLogger('iso8601').setLevel(logging.INFO) #Suppress iso8601 logging

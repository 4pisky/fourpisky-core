import click
import os
from fourpisky.feeds import (AsassnFeed, )
from fourpisky.comms import comet
import sqlalchemy
from voeventdb.server.database import session_registry
import voeventdb.server.database.config as dbconfig
import logging
import logging.handlers



def main(hashdb_path, logfile):
    """
    Checks feeds against their 'last-seen' hash, processes if changed.

    Identifies any 'new' events (not found in local db), generates VOEvents
    and sends them to the local broker.

    Args:
        hashdb_path: path to use for the 'last-seen' hash-database
        logfile: path to use for logfile.

    Returns:

    """
    setup_logging(logfile)
    logger = logging.getLogger('scraper')
    feed_list = [AsassnFeed(hashdb_path)]

    for feed in feed_list:
        if ((feed.new_hash != feed.old_hash)
            or feed.old_hash is None):
            new_ids = feed.determine_new_ids_from_localdb()
            for id in sorted(new_ids,
                             key=lambda id:feed.feed_id_to_stream_id(id)):
                try:
                    v = feed.generate_voevent(id)
                    comet.send_voevent(v)
                    logger.info(
                        "Sent new Voevent: {}".format(v.attrib['ivorn']))
                except:
                    logger.exception(
                        "Error processing id {} in feed".format(id, feed.url))
            feed.save_new_hash()
            if not new_ids:
                logger.debug("Feed {} changed but found no new VOEvents".format(
                    feed.name
                ))
        else:
            logger.debug(
                    "Hash in {} matches for feed: '{}'; moving on.".format(
                        hashdb_path,
                        feed.name,
            ))


default_dbname = os.environ.get('VOEVENTDB_DBNAME',
                                dbconfig.testdb_corpus_url.database)

@click.command()
@click.option('--dbname',
                default = default_dbname,
                help="Database to check for duplicates, default='{}'".format(
                  default_dbname
              ))
@click.option('--hashdb_path', type=click.Path(),
              default='/tmp/fps_feeds_hashdb')
@click.option('--logfile', type=click.Path(),
              default='scrape_feeds.log')
def cli(dbname, hashdb_path, logfile):
    """
     Trivial wrapper about main to create a command line interface entry-point.

     (This preserves main for use as a regular function for use elsewhere
     e.g. testing, and also provide a sensible location to initialise logging.)
    """
    dburl = dbconfig.make_db_url(dbconfig.default_admin_db_params, dbname)
    session_registry.configure(
        bind=sqlalchemy.engine.create_engine(dburl, echo=False)
    )
    main(hashdb_path, logfile)

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

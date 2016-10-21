import click
import logging
import logging.handlers
import os
import sqlalchemy
import sqlalchemy.exc
import subprocess
import time
from voeventdb.server.database import session_registry
from voeventdb.server.database.models import Voevent
import voeventdb.server.database.config as dbconfig
from fourpisky.comms import comet
from fourpisky.feeds import (AsassnFeed, GaiaFeed, create_swift_feeds)
from fourpisky.log_config import setup_logging
logger = logging.getLogger('scraper')


def process_feed_content(feed, process_function, voevent_pause_secs):
    new_ids = feed.determine_new_entries()
    for feed_id in sorted(new_ids,
                          key=lambda id: feed.feed_id_to_stream_id(id)):
        try:
            v = feed.generate_voevent(feed_id)
            process_function(v)
            logger.info(
                "Processed new Voevent: {}".format(v.attrib['ivorn']))
            # Momentary pause to avoid spamming the VOEvent network
            time.sleep(voevent_pause_secs)
        except KeyboardInterrupt:
            raise
        except subprocess.CalledProcessError:
            logger.warning(
                "VOEvent insertion failed for {}".format(feed_id))
        except:
            logger.exception(
                "Error processing id {} in feed".format(feed_id,
                                                        feed.url))
    feed.save_new_hash()
    if not new_ids:
        logger.debug("Feed {} changed but found no new VOEvents".format(
            feed.name
        ))

def main(hashdb_path, logfile, voevent_pause_secs,
         process_function=comet.send_voevent):
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
    # feed_list = []
    feed_list = [AsassnFeed(hashdb_path),
                 GaiaFeed(hashdb_path),
                 ]
    feed_list.extend(create_swift_feeds(hashdb_path, look_back_ndays=7))

    for feed in feed_list:
        if ((feed.old_hash is None) or (feed.new_hash != feed.old_hash)):
            try:
                process_feed_content(feed, process_function, voevent_pause_secs)
            except Exception as e:
                logger.exception("Error processing feed '{}'".format(feed.name))
        else:
            logger.debug(
                "Hash in {} matches for feed: '{}'; moving on.".format(
                    hashdb_path,
                    feed.name,
                ))


default_dbname = os.environ.get('VOEVENTDB_DBNAME',
                                dbconfig.testdb_corpus_url.database)
default_sleeptime = os.environ.get('FPS_FEED_SLEEPTIME',
                                   '0.5')


def direct_store_voevent(voevent):
    s = session_registry()
    try:
        s.add(Voevent.from_etree(voevent))
        s.commit()
    except sqlalchemy.exc.SQLAlchemyError:
        s.rollback()
        raise


@click.command()
@click.option('--dbname',
              default=default_dbname,
              help="Database to check for duplicates, default='{}'".format(
                  default_dbname
              ))
@click.option('--direct-store', is_flag=True,
              help='Store the VOEvents directly in the local database'
                   '(Default is to send/insert via the local broker.)')
@click.option('--hashdb_path', type=click.Path(),
              default='/tmp/fps_feeds_hashdb')
@click.option('--logfile', type=click.Path(),
              default='scrape_feeds')
@click.option('--sleeptime', type=click.FLOAT,
              default=default_sleeptime,
              help="Delay between VOEvent Comet-sends, default='{}'".format(
                  default_sleeptime
              ))
def cli(dbname, direct_store, hashdb_path, logfile, sleeptime):
    """
     Trivial wrapper about main to create a command line interface entry-point.

     (This preserves main for use as a regular function for use elsewhere
     e.g. testing, and also provide a sensible location to initialise logging.)
    """
    dburl = dbconfig.make_db_url(dbconfig.default_admin_db_params, dbname)
    session_registry.configure(
        bind=sqlalchemy.engine.create_engine(dburl, echo=False)
    )
    if direct_store:
        main(hashdb_path, logfile, voevent_pause_secs=0.0,
             process_function=direct_store_voevent)
    else:
        main(hashdb_path, logfile, sleeptime)



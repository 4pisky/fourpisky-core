import click
from fourpisky.feeds import (AssasnFeed, )
from fourpisky.comms import comet
import logging



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
    logger = logging.getLogger(__name__)
    feed_list = [AssasnFeed(hashdb_path)]

    for feed in feed_list:
        if ((feed.new_hash != feed.old_hash)
            or feed.old_hash is None):
            new_ids = feed.determine_new_ids_from_localdb()
            for id in sorted(new_ids,
                             key=lambda id:feed.feed_id_to_stream_id(id)):
                try:
                    v = feed.generate_voevent(id)
                    comet.send_voevent(v)
                    logger.debug(
                        "Sent new Voevent: {}".format(v.attrib['ivorn']))
                except:
                    logger.exception(
                        "Error processing id {} in feed".format(id, feed.url))
            feed.save_new_hash()


@click.command()
@click.option('--hashdb_path', type=click.Path(),
              default='/tmp/fps_feeds_hashdb')
@click.option('--logfile', type=click.Path(),
              default='scrape_feeds.log')
def cli(hashdb_path, logfile):
    """
     Trivial wrapper about main to create a command line interface entry-point.

     (This preserves main for use as a regular function for use elsewhere
     e.g. testing, and also provide a sensible location to initialise logging.)
    """
    logging.basicConfig()
    main(hashdb_path, logfile)

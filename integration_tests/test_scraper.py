from voeventdb.server.database import session_registry
from voeventdb.server.database.config import testdb_corpus_url
from voeventdb.server.database.models import Voevent
import sqlalchemy
import fourpisky.scripts.scrape_feeds as scrape_script
import os
import logging
logging.basicConfig(level=logging.DEBUG)

# Use the testdb
session_registry.configure(
        bind=sqlalchemy.engine.create_engine(testdb_corpus_url, echo=False)
    )


def direct_store_voevent(voevent, host=None, port=None):
    s = session_registry()
    s.add(Voevent.from_etree(voevent))
    s.commit()

# Replace 'send voevent' function with simple 'insert into database'
scrape_script.comet.send_voevent = direct_store_voevent

hashdb_path = '/tmp/fps_feed_hash_testdb'
if os.path.exists(hashdb_path):
    os.unlink(hashdb_path)
    pass

scrape_script.main(
    hashdb_path=hashdb_path,
     logfile='feed_scrape_test.log'
     )


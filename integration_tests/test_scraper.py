from voeventdb.server.database import session_registry
from voeventdb.server.database.config import testdb_corpus_url
import sqlalchemy
import os
import logging

import fourpisky.scripts.scrape_feeds as scrape_script
import fourpisky as fps
fps.comms.email.send_email = fps.comms.email.dummy_email_send_function


logging.basicConfig(level=logging.DEBUG)

# Use the testdb
session_registry.configure(
        bind=sqlalchemy.engine.create_engine(testdb_corpus_url, echo=False)
)

hashdb_path = '/tmp/fps_feed_hash_testdb'
if os.path.exists(hashdb_path):
    # Delete hash-cache every time if desired for testing:
    os.unlink(hashdb_path)
    pass

scrape_script.main(
        hashdb_path=hashdb_path,
        logfile='feed_scrape_test',
        voevent_pause_secs=0.0,
        process_function=scrape_script.direct_store_voevent
)

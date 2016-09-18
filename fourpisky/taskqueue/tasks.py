from __future__ import absolute_import
from fourpisky.taskqueue.app import fps_app
import voeventparse
from celery.utils.log import get_task_logger
import os
from fourpisky.scripts.process_voevent import voevent_logic
import fourpisky.env_vars as fps_env_vars

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import voeventdb.server.database.config as dbconfig
from voeventdb.server.database import db_utils
import voeventdb.server.database.convenience as dbconv
import fourpisky as fps

# logger = logging.getLogger(__name__)
logger = get_task_logger(__name__)

dummy_email_mode = os.environ.get(fps_env_vars.use_dummy_mode, None)
if dummy_email_mode is not None:
    fps.comms.email.send_email = fps.comms.email.dummy_email_send_function
    fps.comms.comet.send_voevent = fps.comms.comet.dummy_send_to_comet_stub
    logger.warning("Dummy stub-functions engaged!")

voeventdb_dbname = os.environ.get(fps_env_vars.voeventdb_dbname,
                                  dbconfig.testdb_corpus_url.database)

dburl = dbconfig.make_db_url(dbconfig.default_admin_db_params, voeventdb_dbname)
if not db_utils.check_database_exists(dburl):
    raise RuntimeError("voeventdb database not found: {}".format(
        voeventdb_dbname))
dbengine = create_engine(dburl)


@fps_app.task()
def process_voevent_celerytask(bytestring):
    """
    Process the voevent using the 'voevent_logic'

    i.e. the function defined in
    `fourpisky.scripts.process_voevent`.
    """
    v = voeventparse.loads(bytestring)
    logger.debug("Load for processing: " + v.attrib['ivorn'])
    voevent_logic(v)
    logger.info("Processed:" + v.attrib['ivorn'])


@fps_app.task()
def ingest_voevent_celerytask(bytestring):
    """
    Ingest the voevent into a local instance of voeventdb.
    """
    v = voeventparse.loads(bytestring)
    logger.debug("Load for ingest: " + v.attrib['ivorn'])
    session = Session(bind=dbengine)
    try:
        dbconv.safe_insert_voevent(session, v)
        session.commit()
    except:
        if (v.attrib['role'] == voeventparse.definitions.roles.test and
                v.attrib['ivorn'].startswith('ivo://nasa.gsfc.gcn/INTEGRAL')):
            logger.warning(
                "Ignoring mismatched duplicate-ivorn test events from "
                "NASA-INTEGRAL stream")
        else:
            logger.exception(
                "Could not insert packet with ivorn {} into {}".format(
                    v.attrib['ivorn'], voeventdb_dbname))

    logger.info("Ingested:" + v.attrib['ivorn'])

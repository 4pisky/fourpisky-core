from __future__ import absolute_import
from fourpisky.taskqueue.app import fps_app
import voeventparse


from celery.utils.log import get_task_logger
import os
from fourpisky.scripts import process_voevent as pv_mod
import fourpisky.env_vars as fps_env_vars

# logger = logging.getLogger(__name__)
logger = get_task_logger(__name__)

dummy_email_mode = os.environ.get(fps_env_vars.use_dummy_email_stub, None)
if dummy_email_mode is not None:
    pv_mod.fps.comms.email.send_email = pv_mod.fps.comms.email.dummy_email_send_function
    logger.warning("Dummy emailer stub-function engaged!")

@fps_app.task()
def process_voevent_celerytask(bytestring):
    v = voeventparse.loads(bytestring)
    logger.debug("Loading: " +v.attrib['ivorn'])
    pv_mod.voevent_logic(v)
    logger.info("Processed:" + v.attrib['ivorn'])




from __future__ import absolute_import
import logging
import subprocess
import voeventparse
import tempfile
import textwrap

logger = logging.getLogger(__name__)


def send_voevent(voevent, host='localhost', port=8098):
    logger.debug("comet-sendvo voevent: {}".format(voevent.attrib['ivorn']))
    tf = tempfile.TemporaryFile()
    voeventparse.dump(voevent, tf)
    tf.seek(0)
    # tf.close()
    try:
        cmd = ['comet-sendvo']
        cmd.append('--host=' + host)
        cmd.append('--port=' + str(port))
        output = subprocess.check_output(cmd, stdin=tf, )
    except subprocess.CalledProcessError as e:
        logger.error(f"send_voevent failed, output was: {e.output}")
        raise e
    return output


def dummy_send_to_comet_stub(voevent, host='localhost', port=8098):
    tf = tempfile.NamedTemporaryFile(delete=False)
    logmsg=textwrap.dedent("""\
    *************
    Would have sent a VOEvent to node: {host}:{port};
    IVORN: {ivorn}
    Copy of XML dumped to: {fname}
    *************
    """.format(host=host, port=port, ivorn=voevent.attrib['ivorn'],
               fname=tf.name))
    logger.debug(logmsg)
    voeventparse.dump(voevent, tf)
    tf.close()
    # raise subprocess.CalledProcessError(1, 'dummyvosend')

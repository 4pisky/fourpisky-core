import os
import datetime, pytz
import voeventparse
import logging
import subprocess
import click
from fourpisky.formatting import fps_template_env
from fourpisky.local import contacts
from fourpisky.visibility import get_ephem
from fourpisky.triggers import swift, asassn
from fourpisky.triggers import is_test_trigger
from fourpisky.voevent import ivorn_base
from fourpisky.sites import AmiLA, Pt5m
import fourpisky as fps
import amicomms

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# Definitions
grb_contacts = contacts.grb_contacts

amicomms.email_address = contacts.test_contacts[0].email

notification_email_prefix = "[4 Pi Sky] "

default_archive_root = os.path.join(os.environ["HOME"],
                                    "voevent-deploy","voe_archive")

active_sites = [AmiLA, Pt5m]
#-------------------------------------------------------------------------------

@click.command()
def cli():
    stdin_binary = click.get_binary_stream('stdin')
    v = voeventparse.loads(stdin_binary.read())
    voevent_logic(v)
    return 0

def voevent_logic(v):
    #SWIFT BAT GRB alert:
    if swift.filters.is_bat_grb_pkt(v):
        swift_bat_grb_logic(v)
    if asassn.filters.is_fps_asassn_packet(v):
        asassn_alert_logic(v)
    if is_test_trigger(v):
        test_logic(v)
    archive_voevent(v, rootdir=default_archive_root)


def swift_bat_grb_logic(v):
    actions_taken=[]
    alert = swift.BatGrb(v)
    alert_rejection = alert.reject()
    if alert_rejection is None:
        ami_reject = fps.filters.ami.reject(alert.position)
        if ami_reject is None:
            try:
                trigger_ami_swift_grb_alert(alert)
                actions_taken.append('Observation requested from AMI.')
                try:
                    send_initial_ami_alert_vo_notification(alert)
                    actions_taken.append('AMI request notified to VOEvent network.')
                except subprocess.CalledProcessError as e:
                    emsg = '***Notification to VOEvent network failed.***'
                    logger.warn(emsg)
                    actions_taken.append(emsg)
            except Exception as e:
                emsg = 'Observation request failed.'
                actions_taken.append(emsg)
                logger.error(emsg)
                raise
        else:
            actions_taken.append('Target unsuitable for ami: ' + ami_reject)
    else:
        actions_taken.append('Alert ignored: ' + alert_rejection)

    send_alert_report(alert, actions_taken, grb_contacts)


def asassn_alert_logic(v):
    actions_taken=[]
    alert = asassn.AsassnAlert(v)
    if asassn.filters.is_recent(alert):
        send_alert_report(alert, actions_taken, grb_contacts)


#=============================================================================
# Subroutines


def trigger_ami_swift_grb_alert(alert):
    assert isinstance(alert, swift.BatGrb)
    target_name = alert.id
    comment = alert.id + " / " + alert.inferred_name
    duration = datetime.timedelta(hours=2.)

    ami_request = amicomms.request_email(
                   target_coords=alert.position,
                   target_name=target_name,
                   duration=duration,
                  timing='ASAP',
                  action='CHECK',
                  requester=amicomms.default_requester,
                  comment=comment)

    fps.comms.email.send_email(recipient_addresses=amicomms.email_address,
                               subject=amicomms.request_email_subject,
                               body_text=ami_request)





def send_initial_ami_alert_vo_notification(alert):
    notification_timestamp = datetime.datetime.utcnow()
    request_status = {'sent_time':notification_timestamp,
                  'acknowledged':False,
                  }
    stream_id = notification_timestamp.strftime(fps.formatting.datetime_format_short)
    v = fps.voevent.create_ami_followup_notification(alert,
                                                     stream_id=stream_id,
                                                     request_status=request_status)
    fps.comms.comet.send_voevent(v, contacts.local_vobroker.ipaddress,
                                 contacts.local_vobroker.port)


def send_alert_report(alert, actions_taken, contacts):
    notify_msg = generate_report_text(
                                alert,
                                active_sites,
                                actions_taken)
    subject = alert.id
    if alert.inferred_name is not None:
              subject+= ' / ' + alert.inferred_name
    fps.comms.email.send_email([p.email for p in contacts],
                               notification_email_prefix + subject,
                               notify_msg)


def test_logic(v):
    now = datetime.datetime.now(pytz.utc)
    stream_id = v.attrib['ivorn'].partition('#')[-1]
    response = fps.voevent.create_4pisky_test_response_voevent(
        stream_id=stream_id,
        date=now)

    fps.comms.comet.send_voevent(response, contacts.local_vobroker.ipaddress,
                                 contacts.local_vobroker.port)
    testresponse_template = fps_template_env.get_template('test_response.j2')
    msg_context = dict(now=now)
    msg_context.update(fps.base_context())
    msg = testresponse_template.render(msg_context)
    fps.comms.email.send_email(
        recipient_addresses=[c.email for c in contacts.test_contacts],
        subject=notification_email_prefix + '[TEST] Test packet received',
        body_text=msg)
    archive_voevent(v, rootdir=default_archive_root)


def archive_voevent(v, rootdir):
    relpath, filename = v.attrib['ivorn'].split('//')[1].split('#')
    filename += ".xml"
    fullpath = os.path.sep.join((rootdir, relpath, filename))
    fps.utils.ensure_dir(fullpath)
    with open(fullpath, 'w') as f:
        voeventparse.dump(v, f)

def generate_report_text(alert, sites, actions_taken,
                         report_timestamp=None):
    if report_timestamp is None:
        report_timestamp = datetime.datetime.now(pytz.utc)
    site_reports = [(site, get_ephem(alert.position, site, report_timestamp))
                            for site in sites]
    notification_template = fps_template_env.get_template('notify.j2')
    msg_context=dict(alert=alert,
                report_timestamp=report_timestamp,
                site_reports=site_reports,
                actions_taken=actions_taken,)
    msg_context.update(fps.base_context())
    msg = notification_template.render(msg_context)
    return msg


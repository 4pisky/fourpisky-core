import os
import datetime, pytz
import voeventparse
import logging
import subprocess
import click

from fourpisky.local import contacts
from fourpisky.reports import (generate_report_text, send_report,
                               generate_testresponse_text)
from fourpisky.sites import AmiLA, Pt5m
from fourpisky.triggers import swift, asassn, gaia
from fourpisky.triggers import is_test_trigger
from fourpisky.voevent import ivorn_base
import fourpisky as fps
import amicomms

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# Definitions
grb_contacts = contacts.grb_contacts

amicomms.email_address = contacts.test_contacts[0].email

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
    if swift.BatGrb.packet_type_matches(v):
        swift_bat_grb_logic(v)
    if asassn.AsassnAlert.packet_type_matches(v):
        asassn_alert_logic(v)
    if gaia.GaiaAlert.packet_type_matches(v):
        gaia_alert_logic(v)
    if is_test_trigger(v):
        test_logic(v)
#    archive_voevent(v, rootdir=default_archive_root)


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
    logger.info("Swift BAT GRB packet received, actions taken:\n{}".format(
        actions_taken
    ))
    report = generate_report_text(alert,active_sites,actions_taken)
    send_report(subject=alert.full_name, text=report, contacts=grb_contacts)


def asassn_alert_logic(v):
    actions_taken=[]
    alert = asassn.AsassnAlert(v)
    if alert.is_recent():
        report = generate_report_text(alert,active_sites,actions_taken)
        send_report(subject=alert.full_name, text=report, contacts=grb_contacts)

def gaia_alert_logic(v):
    actions_taken = []
    alert = gaia.GaiaAlert(v)
    if alert.is_recent():
        report = generate_report_text(alert,active_sites,actions_taken)
        send_report(subject=alert.full_name, text=report,
                    contacts=grb_contacts)


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
    request_status = {
        'sent_time':notification_timestamp,
        'acknowledged':False,
                  }
    stream_id = notification_timestamp.strftime(fps.formatting.datetime_format_short)
    v = fps.voevent.create_ami_followup_notification(alert,
                                                     stream_id=stream_id,
                                                     request_status=request_status)
    fps.comms.comet.send_voevent(v, contacts.local_vobroker.ipaddress,
                                 contacts.local_vobroker.port)


def test_logic(v):
    now = datetime.datetime.now(pytz.utc)
    stream_id = v.attrib['ivorn'].partition('#')[-1]
    response = fps.voevent.create_4pisky_test_response_voevent(
        stream_id=stream_id,
        date=now)
    fps.comms.comet.send_voevent(response, contacts.local_vobroker.ipaddress,
                                 contacts.local_vobroker.port)
    report = generate_testresponse_text(now)
    send_report(subject='Test packet received', text = report,
                contacts=contacts.test_contacts
                )



import datetime, pytz
from fourpisky.visibility import get_ephem
from fourpisky.formatting import fps_template_env, datetime_format_long
from fourpisky.local import notification_email_prefix
import fourpisky as fps
import socket

from fourpisky import __versiondict__

def base_context():
    """
    Get a dictionary of context variables used across multiple templates.
    """
    hostname = socket.gethostname()
    return dict(
        versions=__versiondict__,
        hostname=hostname,
        dt_style=datetime_format_long
    )

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
    msg_context.update(base_context())
    msg = notification_template.render(msg_context)
    return msg

def generate_testresponse_text(timestamp):
    testresponse_template = fps_template_env.get_template('test_response.j2')
    msg_context = dict(now=timestamp)
    msg_context.update(fps.base_context())
    msg = testresponse_template.render(msg_context)
    return msg


def send_report(subject, text, contacts):
    fps.comms.email.send_email([p.email for p in contacts],
                               notification_email_prefix + subject,
                               text)

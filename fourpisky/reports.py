import datetime, pytz
import socket
from fourpisky.visibility import get_ephem
from fourpisky.formatting import fps_template_env, datetime_format_long
from fourpisky.local import notification_email_prefix
import fourpisky as fps
import logging

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
    msg_context = dict(alert=alert,
                       report_timestamp=report_timestamp,
                       site_reports=site_reports,
                       actions_taken=actions_taken, )
    msg_context.update(base_context())
    msg = notification_template.render(msg_context)
    return msg


def generate_testresponse_text(timestamp):
    testresponse_template = fps_template_env.get_template('test_response.j2')
    msg_context = dict(now=timestamp)
    msg_context.update(base_context())
    msg = testresponse_template.render(msg_context)
    return msg


def send_report(subject, text, contacts):
    fps.comms.email.send_email([p.email for p in contacts],
                               notification_email_prefix + subject,
                               text)


class EmailHandler(logging.Handler):
    """
    We use this as a catch-all for reporting errors via email.
    """

    def __init__(self, recipients):
        super(EmailHandler, self).__init__()
        logging.Handler.__init__(self)
        self.recipients = recipients

    def emit(self, record):
        msg_context = dict(error_msg=self.format(record),
                           now=datetime.datetime.now(pytz.utc),
                           )
        msg_context.update(base_context())
        template = fps_template_env.get_template('error_report.j2')
        msg = template.render(msg_context)
        fps.comms.email.send_email(self.recipients,
                                   notification_email_prefix + "Error detected",
                                   body_text=msg)

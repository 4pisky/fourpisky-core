from __future__ import absolute_import
import smtplib
# import sendgrid
from sendgrid import SendGridAPIClient
import fourpisky.utils as utils
import logging

logger = logging.getLogger(__name__)

from fourpisky.local import contacts


class EmailConfigKeys():
    username = 'username'
    password = 'password'
    smtp_server = 'smtp_server'
    smtp_port = 'smtp_port'


keys = EmailConfigKeys()


def send_email_by_smtp(recipient_addresses,
                       subject,
                       body_text,
                       account=contacts.gmail_login
                       ):
    """
    Send email using a Gmail SMTP login.
    """

    logger.debug("Loaded account, starting SMTP session")
    recipient_addresses = utils.listify(recipient_addresses)

    smtpserver = smtplib.SMTP(account.smtp_server,
                              account.smtp_port)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(account.username,
                     account.password)

    sender = account.username

    recipients_str = ",".join(recipient_addresses)

    logger.debug("Logged in, emailing " + recipients_str)
    header = "".join(['To: ', recipients_str, '\n',
                      'From: ', sender, '\n',
                      'Subject: ', subject, '\n'])

    msg = "".join([header, '\n',
                   body_text, '\n\n'])
    smtpserver.sendmail(sender, recipient_addresses, msg)
    logger.debug('Message sent')
    smtpserver.close()


def send_email_by_sendgrid(
        recipient_addresses,
        subject,
        body_text,
        sgapi=SendGridAPIClient(apikey=contacts.sendgrid_api_key)
):
    """
    Send an email using the Sendgrid API.

    Sendgrid has no storage equivalent of a 'sent' folder,
    so we always BCC a copy to the gmail login with the
    "+sent" alias suffix.
    """
    recipient_addresses = utils.listify(recipient_addresses)
    personalization = {}
    personalization['to'] = [{'email': addr for addr in recipient_addresses}]
    personalization['subject'] = subject
    personalization['bcc'] = [{'email': contacts.sendgrid_bcc_address}]

    message_data = {
        "personalizations": [personalization],
        "from": {"email": contacts.gmail_login.username},
        "content": [
            {
                "type": "text/plain",
                "value": body_text
            }
        ]
    }
    if contacts.error_contacts:
        message_data["reply_to"] = {"email": contacts.error_contacts[0].email}

    logger.debug("Sending message data: \n{}".format(message_data))
    response = sgapi.client.mail.send.post(request_body=message_data)
    if response.status_code != 202:
        # Don't raise an exception - what are we gonna do about it?
        # If no emails are going out, we can't email an exception notice.
        # Instead, log the error for later manual investigation:
        logger.error("Could not send mail!")
        logger.error("Response code: {}".format(response.status_code))
        logger.error("Response headers: {}".format(response.headers))
        logger.error("Message data: {}".format(message_data))
    # And return the response so client code can detect errors if desirable:
    return response


def send_email(
        recipient_addresses,
        subject,
        body_text
):
    """
    Defines the default delivery method
    """
    logger.debug("Attempting to send email subject:{} to {}".format(
        subject, recipient_addresses
    ))
    # send_email_by_smtp(recipient_addresses, subject, body_text)
    return send_email_by_sendgrid(recipient_addresses, subject, body_text)


def dummy_email_send_function(recipient_addresses,
                              subject,
                              body_text
                              ):
    logger.debug("*************")
    logger.debug("""\
Would have sent an email to:
{recipients}
Subject: {subject}
--------------
{body_text}
*************""".format(
        recipients=utils.listify(recipient_addresses),
        subject=subject,
        body_text=body_text
    ))

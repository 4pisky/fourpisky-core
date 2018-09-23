import fourpisky.comms.email
import fourpisky.comms.comet

import fourpisky.reports

import amicomms


def dearm_for_tests():
    fourpisky.comms.email.send_email = fourpisky.comms.email.dummy_email_send_function
    fourpisky.comms.comet.send_voevent = fourpisky.comms.comet.dummy_send_to_comet_stub

    test_prefix = "[LOCALTEST] "

    if fourpisky.reports.notification_email_prefix[
       :len(test_prefix)] != test_prefix:
        fourpisky.reports.notification_email_prefix = (
                test_prefix + fourpisky.reports.notification_email_prefix)

    amicomms.email_address = 'blocked!' + amicomms.email_address  # Do NOT email AMI

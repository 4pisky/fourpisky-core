import fourpisky.comms.email
import fourpisky.comms.comet

import fourpisky.reports

from fourpisky.local import amicomms_safe


def dearm_for_tests():
    fourpisky.comms.email.send_email = fourpisky.comms.email.dummy_email_send_function
    fourpisky.comms.comet.send_voevent = fourpisky.comms.comet.dummy_send_to_comet_stub

    test_prefix = "[LOCALTEST] "

    if fourpisky.reports.notification_email_prefix[
       :len(test_prefix)] != test_prefix:
        fourpisky.reports.notification_email_prefix = (
                test_prefix + fourpisky.reports.notification_email_prefix)

    # Do NOT email AMI
    amicomms_safe.email_address = 'blocked!' + amicomms_safe.email_address

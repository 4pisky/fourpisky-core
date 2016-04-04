#!/usr/bin/env python
from __future__ import absolute_import
import logging
import datetime

logging.basicConfig(level=logging.DEBUG)

#Minimal imports here - ensures proper testing of alert_response.
#(If not careful you might temporarily fix a broken import - which then remains broken)
from fourpisky.tests.resources import datapaths
from fourpisky.scripts import process_voevent as pv_mod

##We bind the email sender to a dummy function:
pv_mod.fps.comms.email.send_email = pv_mod.fps.comms.email.dummy_email_send_function
pv_mod.fps.comms.comet.send_voevent = pv_mod.fps.comms.comet.dummy_send_to_comet_stub
test_prefix = "[LOCALTEST] "
if pv_mod.notification_email_prefix[:len(test_prefix)]!=test_prefix:
    pv_mod.notification_email_prefix = test_prefix + pv_mod.notification_email_prefix
pv_mod.grb_contacts = pv_mod.contacts.test_contacts  # Only notify test contacts
pv_mod.amicomms.email_address = 'blocked!' + pv_mod.amicomms.email_address  # Do NOT email AMI
pv_mod.default_archive_root = "./"

def main():
    def test_packet(path):
        with open(path) as f:
            pv_mod.voevent_logic(pv_mod.voeventparse.load(f))

    hr = "********************************************************************"
    print hr
    test_packet(datapaths.gaia_alert_16ajo)
    print hr



if __name__ == "__main__":
    print "Testing with default 'recent' alert notification period:"
    main()
    print "And with modified notification period:"
    pv_mod.asassn.default_alert_notification_period = datetime.timedelta(days=100*365)
    main()
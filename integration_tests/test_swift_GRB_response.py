#!/usr/bin/env python
from __future__ import absolute_import
import logging

logging.basicConfig(level=logging.DEBUG)

#Minimal imports here - ensures proper testing of alert_response.
#(If not careful you might temporarily fix a broken import - which then remains broken)
from fourpisky.tests.resources import datapaths
from fourpisky.scripts import process_voevent as pv_mod

import fourpisky.reports as reports

##We bind the email sender to a dummy function:
pv_mod.fps.comms.email.send_email = pv_mod.fps.comms.email.dummy_email_send_function
pv_mod.fps.comms.comet.send_voevent = pv_mod.fps.comms.comet.dummy_send_to_comet_stub
test_prefix = "[LOCALTEST] "
if reports.notification_email_prefix[:len(test_prefix)]!=test_prefix:
    reports.notification_email_prefix = test_prefix + reports.notification_email_prefix
pv_mod.grb_contacts = pv_mod.contacts.test_contacts  # Only notify test contacts
pv_mod.amicomms.email_address = 'blocked!' + pv_mod.amicomms.email_address  # Do NOT email AMI
pv_mod.default_archive_root = "./"

def main():
    def test_packet(path):
        with open(path) as f:
            pv_mod.voevent_logic(pv_mod.voeventparse.load(f))

    hr = "********************************************************************"
    print hr
    print "Sometimes visible source:"
    test_packet(datapaths.swift_bat_grb_pos_v2)
    ##Now a circumpolar source:
    print hr
    print "Always visible source:"
    test_packet(datapaths.swift_bat_grb_circumpolar)
    ##Now test one with null follow-up:
    print hr
    print "Never visible source:"
    test_packet(datapaths.swift_bat_grb_low_dec)
    ##Now test one with bad star tracking:
    print hr
    print "Bad source:"
    test_packet(datapaths.swift_bat_grb_lost_lock)
    print hr
    print "Known source:"
    test_packet(datapaths.swift_bat_known_source)

if __name__ == "__main__":
    main()

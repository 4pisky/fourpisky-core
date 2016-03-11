#!/usr/bin/env python

import logging
logging.basicConfig(level=logging.DEBUG)

#Minimal imports here - ensures proper testing of alert_response.
#(If not careful you might temporarily fix a broken import - which then remains broken)
import fourpisky.voevent
from fourpisky.scripts import process_voevent as pv_mod

##We bind the email sender to a dummy function:
pv_mod.fps.comms.email.send_email = pv_mod.fps.comms.email.dummy_email_send_function
pv_mod.fps.comms.comet.send_voevent = pv_mod.fps.comms.comet.dummy_send_to_comet_stub

@profile
def main():
    pv_mod.default_archive_root = "./"
    test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
    print "Packet loaded, ivorn", test_packet.attrib['ivorn']
    pv_mod.voevent_logic(test_packet)

if __name__ == "__main__":
    main()

#!/usr/bin/python


#Minimal imports here - ensures proper testing of alert_response.
#(If not careful you might temporarily fix a broken import - which then remains broken)
from pysovo.tests.resources import datapaths
import voeparse
import alert_response as ar

##We bind the email sender to a dummy function:
ar.ps.comms.email.send_email = ar.ps.comms.email.dummy_email_send_function

def main():
    ar.default_archive_root = "./"
    test_packet = voeparse.Voevent(stream='voevent.astro.soton/TEST',
                                   stream_id='42',
                                   role=voeparse.roles.test)
    print "Packet loaded, ivorn", test_packet.attrib['ivorn']
    print "Logic go!"
    ar.voevent_logic(test_packet)

if __name__ == "__main__":
    main()

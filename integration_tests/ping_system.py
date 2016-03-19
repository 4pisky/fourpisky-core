#!/usr/bin/env python
"""
Pings a live broker / alert_response setup with test packet.
This provides a means of testing a live system in a safe and unobtrusive manner.
"""
import datetime
import logging
import voeventparse
import fourpisky
import fourpisky.voevent
from fourpisky.local import contacts
from fourpisky.formatting import datetime_format_short
from fourpisky.triggers import test_trigger_substream


def main():
    now = datetime.datetime.utcnow()
    test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
    dummy_packet = fourpisky.voevent.create_skeleton_4pisky_voevent(
            substream="DUMMYPACKET",
            stream_id=fourpisky.voevent.generate_stream_id(now),
            date=now
        )
    sendpacket = dummy_packet
    # sendpacket = test_packet

    print "Sending packet, ivorn: ", sendpacket.attrib['ivorn']
    broker = contacts.local_vobroker
    before = datetime.datetime.utcnow()
    fourpisky.comms.comet.send_voevent(sendpacket, broker.ipaddress, broker.port)
    after = datetime.datetime.utcnow()
    print "Done. Sending took", (after - before).total_seconds(), "seconds."

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()

#!/usr/bin/env python

import logging
logging.basicConfig(level=logging.DEBUG)

import fourpisky.voevent
from fourpisky.tests.resources import dearm_for_tests
from fourpisky.scripts import process_voevent as pv_mod

dearm_for_tests()

# @profile
def main():
    pv_mod.default_archive_root = "./"
    test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
    print("Packet loaded, ivorn", test_packet.attrib['ivorn'])
    pv_mod.voevent_logic(test_packet)

if __name__ == "__main__":
    main()

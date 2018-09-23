#!/usr/bin/env python

import fourpisky.log_config
from fourpisky.scripts import process_voevent as pv_mod
from fourpisky.tests.resources import datapaths, dearm_for_tests

dearm_for_tests()

pv_mod.grb_contacts = pv_mod.contacts.test_contacts  # Only notify test contacts
pv_mod.default_archive_root = "./"

def main():
    fourpisky.log_config.setup_logging()
    def test_packet(path):
        with open(path, 'rb') as f:
            pv_mod.voevent_logic(pv_mod.voeventparse.load(f))

    hr = "********************************************************************"
    print(hr)
    print("Sometimes visible source:")
    test_packet(datapaths.swift_bat_grb_pos_v2)
    ##Now a circumpolar source:
    print(hr)
    print("Always visible source:")
    test_packet(datapaths.swift_bat_grb_circumpolar)
    ##Now test one with null follow-up:
    print(hr)
    print("Never visible source:")
    test_packet(datapaths.swift_bat_grb_low_dec)
    ##Now test one with bad star tracking:
    print(hr)
    print("Bad source:")
    test_packet(datapaths.swift_bat_grb_lost_lock)
    print(hr)
    print("Known source:")
    test_packet(datapaths.swift_bat_known_source)

if __name__ == "__main__":
    main()

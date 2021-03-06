#!/usr/bin/env python

import datetime

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
    test_packet(datapaths.asassn_alert_16ab)
    print(hr)
    test_packet(datapaths.asassn_alert_AT2016D)


if __name__ == "__main__":
    print("Testing with default 'recent' alert notification period:")
    main()
    print("And with modified notification period:")
    pv_mod.asassn.default_alert_notification_period = datetime.timedelta(
        days=100 * 365)
    main()

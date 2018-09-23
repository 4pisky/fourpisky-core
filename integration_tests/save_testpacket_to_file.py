#!/usr/bin/env python

import logging
logging.basicConfig(level=logging.DEBUG)


import fourpisky.voevent
from fourpisky.utils import archive_voevent_to_file
import voeventparse

def main():
    test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
    archive_voevent_to_file(test_packet, rootdir="./")


if __name__ == "__main__":
    main()

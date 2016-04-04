#!/usr/bin/env python

import logging
logging.basicConfig(level=logging.DEBUG)


import fourpisky.voevent
from fourpisky.scripts.process_voevent import archive_voevent
import voeventparse

def main():
    test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
    archive_voevent(test_packet, rootdir="./")


if __name__ == "__main__":
    main()
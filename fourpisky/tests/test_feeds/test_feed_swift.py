import os
import voeventparse as vp
from fourpisky.feeds import SwiftFeed
from fourpisky.tests.resources import datapaths

import pytest

with open(datapaths.swift_bat_grb_pos_v2, 'rb') as f:
    good_bat_grb_voevent = vp.load(f)

def test_content_fetch():
    feed = SwiftFeed(good_bat_grb_voevent)
    assert len(feed.content)


def parse_from_voevent(voevent):
    feed = SwiftFeed(voevent)
    events = feed.parse_content_to_event_data_list()
    assert len(events) == 1
    feed_id = feed.event_id_data_map.keys()[0]
    voevent = feed.generate_voevent(feed_id)
    vp.assert_valid_as_v2_0(voevent)
    if True:
        # Write to file for desk-checking:
        tmpdir = '/tmp/fps_feed_test/swift'
        if not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)
        outpath = os.path.join(tmpdir, '{}.xml'.format(feed_id))

        with open(outpath, 'w') as f:
            vp.dump(voevent, f)
            print("Example voevent output to " + outpath)
    return voevent


def test_good_swift_grb():
    voevent = parse_from_voevent(good_bat_grb_voevent)
    params = vp.pull_params(voevent)
    assert 'duration' in params

def test_bad_duration_swift_grb():
    with open(datapaths.swift_bat_grb_bad_duration_analysis, 'rb') as f:
        bad_duration_voevent = vp.load(f)
    voevent = parse_from_voevent(bad_duration_voevent)
    params = vp.pull_params(voevent)



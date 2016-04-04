from six import string_types
from fourpisky.tests.resources import datapaths
import fourpisky.feeds.gaia as gaia
import voeventparse as vp
from voeventdb.server.database.models import Voevent
import os
import pytest



with open(datapaths.gaia_feed_csv_2016_04_04) as f:
        gaia_content = f.read()

def test_content_parsing():
    feed = gaia.GaiaFeed()
    feed._content = gaia_content
    events = feed.parse_content_to_event_data_list()
    assert len(events) == 524

def test_streamid_generation():
    feed = gaia.GaiaFeed()
    feed._content = gaia_content
    events = feed.parse_content_to_event_data_list()
    for e in events:
        try:
            id = feed.event_data_to_event_id(e)
            # assert isinstance(id, string_types)
        except Exception as e:
            print e
            raise
        #     pass

def test_voevent_generation():
    tmpdir = '/tmp/fps_feed_test/gaia'
    if not os.path.isdir(tmpdir):
        os.makedirs(tmpdir)
    feed = gaia.GaiaFeed()
    feed._content = gaia_content
    # for feed_id in feed.event_id_data_map.keys()[:10]:
    for feed_id in feed.event_id_data_map.keys():
        v = feed.generate_voevent(feed_id)
        stream_id = feed.feed_id_to_stream_id(feed_id)
        vp.assert_valid_as_v2_0(v)
        outpath = os.path.join(tmpdir,'{}.xml'.format(stream_id))
        with open(outpath, 'w') as f:
            vp.dump(v, f)

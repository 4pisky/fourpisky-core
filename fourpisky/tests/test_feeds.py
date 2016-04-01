from six import string_types
from fourpisky.tests.resources import datapaths
import fourpisky.feeds.asassn as asassn
import voeventparse as vp
from voeventdb.server.database.models import Voevent
import os
import pytest



with open(datapaths.asassn_feed_page_2015_12_21) as f:
        asassn_content_1 = f.read()

with open(datapaths.asassn_feed_page_2016_01_11) as f:
        asassn_content_2 = f.read()

def test_content_parsing():
    feed = asassn.AsassnFeed()
    feed._content = asassn_content_1
    events = feed.parse_content_to_event_data_list()
    assert len(events) == 1357

def test_streamid_generation():
    feed = asassn.AsassnFeed()
    feed._content = asassn_content_1
    events = feed.parse_content_to_event_data_list()
    for e in events:
        try:
            id = asassn.extract_asassn_id(e)
            assert isinstance(id, string_types)
        except ValueError as e:
            print e
            pass

def test_assasn_voevent_generation():
    tmpdir = '/tmp/fps_feed_test/assasn'
    if not os.path.isdir(tmpdir):
        os.makedirs(tmpdir)
    feed2 = asassn.AsassnFeed()
    feed2._content = asassn_content_2
    for feed_id in feed2.event_id_data_map.keys()[:10]:
    # for feed_id in feed2.id_row_map.keys():
        v = feed2.generate_voevent(feed_id)
        stream_id = feed2.feed_id_to_stream_id(feed_id)
        vp.assert_valid_as_v2_0(v)
        outpath = os.path.join(tmpdir,'{}.xml'.format(stream_id))
        with open(outpath, 'w') as f:
            vp.dump(v, f)
    # for id in id_map.keys():
    #     v = feed2.generate_voevent(id)
    #     vp.assert_valid_as_v2_0(v)
    #     with open('/tmp/asassn/{}.xml'.format(id), 'w') as f:
    #         vp.dump(v, f)


def test_feed_hashing(uncreated_temporary_file_path):
    hash_cache_path = uncreated_temporary_file_path
    feed1 = asassn.AsassnFeed(hash_cache_path)
    feed1._content = asassn_content_1
    feed1._new_hash = feed1.mock_new_hash
    assert feed1.new_hash
    feed1.save_new_hash()

    feed2 = asassn.AsassnFeed(hash_cache_path)
    feed2._content = asassn_content_1
    feed2._new_hash = feed2.mock_new_hash
    assert feed2.old_hash == feed2.new_hash

def test_localdb_deduplication(fixture_db_session):
    feed1 = asassn.AsassnFeed()
    feed1._content = asassn_content_1
    feed1_row_ids = feed1.determine_new_ids_from_localdb()
    assert len(feed1_row_ids) == len(feed1.event_id_data_map)

    s = fixture_db_session
    for id in feed1_row_ids:
        v = feed1.generate_voevent(id)
        s.add(Voevent.from_etree(v))
    s.commit()

    feed1_new_ids = feed1.determine_new_ids_from_localdb()
    assert len(feed1_new_ids) == 0


    feed2 = asassn.AsassnFeed()
    feed2._content = asassn_content_2
    feed2_new_ids = feed2.determine_new_ids_from_localdb()
    assert len(feed2_new_ids) == len(feed2.event_id_data_map) - len(feed1.event_id_data_map)
    s = fixture_db_session
    for id in feed2_new_ids:
        v = feed2.generate_voevent(id)
        s.add(Voevent.from_etree(v))
    s.commit()

    modified_content = asassn_content_2.replace('ASASSN-16ad', 'ASASSN-16adfooishbar')
    feed3 = asassn.AsassnFeed()
    feed3._content = modified_content
    assert [] == feed3.determine_new_ids_from_localdb()

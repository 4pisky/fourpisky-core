from __future__ import absolute_import
from unittest import TestCase
import voeventparse as vp
from fourpisky.tests.resources import datapaths
import fourpisky.voevent as vo_subs
from fourpisky.triggers.swift import BatGrb
import datetime
import pytz


class TestFollowupVoevent(TestCase):
    def test_initial_case(self):
        with open(datapaths.swift_bat_grb_pos_v2) as f:
            swift_alert = BatGrb(vp.load(f))
        current_utc_time = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        request_status = {'sent_time': current_utc_time,
                          'acknowledged': False,
                          }

        v = vo_subs.create_ami_followup_notification(swift_alert,
                                                     stream_id=001,
                                                     request_status=request_status)
        vp.assert_valid_as_v2_0(v)
        with open('/tmp/test_voevent.xml', 'w') as f:
            vp.dump(v, f)

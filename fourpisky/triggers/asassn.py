"""
Convenience routines and data structures useful for dealing with Swift packets.
"""

import voeventparse
from fourpisky.utils import convert_voe_coords_to_eqposn
from fourpisky.feeds.asassn import AsassnFeed, AsassnKeys
from collections import OrderedDict
import datetime
import pytz

alert_notification_period = datetime.timedelta(days=4)


class filters:
    @staticmethod
    def is_fps_asassn_packet(voevent):
        ivorn = voevent.attrib['ivorn']
        if ivorn.startswith(AsassnFeed.stream_ivorn_prefix):
            return True
        return False

    @staticmethod
    def is_recent(assasn_alert):
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        if (now - assasn_alert.isotime) < alert_notification_period:
            return True
        return False




class AsassnAlert(object):
    def __init__(self, voevent):
        self.voevent = voevent
        self.ivorn = self.voevent.attrib['ivorn']
        if not filters.is_fps_asassn_packet(voevent):
            raise ValueError("Cannot instantiate AsassnAlert; packet header mismatch.")

        all_params = voeventparse.pull_params(self.voevent)

        text_params_grp = all_params[AsassnFeed.text_params_groupname]
        self.text_params = OrderedDict(
            (k,d['value']) for k,d in text_params_grp.items())

        url_params_grp = all_params[AsassnFeed.url_params_groupname]
        self.url_params = OrderedDict(
                (k,d['value']) for k,d in url_params_grp.items())

        self.description = ("ASASSN alert")
        self.id = self.text_params.get(AsassnKeys.id_asassn)
        if self.id is None:
            self.id = self.text_params.get(AsassnKeys.id_other)
        #Assigned name according to the 'why' section of voevent packet:
        self.inferred_name = None
        self.isotime = voeventparse.pull_isotime(self.voevent)

        self.position = convert_voe_coords_to_eqposn(
                                       voeventparse.pull_astro_coords(self.voevent))

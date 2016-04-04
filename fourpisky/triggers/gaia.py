import voeventparse
from fourpisky.utils import convert_voe_coords_to_eqposn
from fourpisky.feeds.gaia import GaiaFeed, GaiaKeys
from collections import OrderedDict
import datetime
import pytz

default_alert_notification_period = datetime.timedelta(days=7)

class GaiaAlert(object):
    @staticmethod
    def packet_type_matches(voevent):
        ivorn = voevent.attrib['ivorn']
        if ivorn.startswith(GaiaFeed.stream_ivorn_prefix):
            return True
        return False

    def __init__(self, voevent,
                 alert_notification_period=None):
        self.voevent = voevent
        self.ivorn = self.voevent.attrib['ivorn']
        self.alert_notification_period = alert_notification_period
        if self.alert_notification_period is None:
            self.alert_notification_period = default_alert_notification_period

        if not GaiaAlert.packet_type_matches(voevent):
            raise ValueError(
                "Cannot instantiate GaiaAlert; packet header mismatch.")

        self.description = ("GAIA alert")

        all_params = voeventparse.pull_params(self.voevent)
        text_params_grp = all_params[GaiaFeed.text_params_groupname]
        self.text_params = OrderedDict(
            (k, d['value']) for k, d in text_params_grp.items())

        self.id = self.text_params.get('Name')
        self.inferred_name = None

        self.isotime = voeventparse.pull_isotime(self.voevent)
        self.position = convert_voe_coords_to_eqposn(
            voeventparse.pull_astro_coords(self.voevent))

        self.url_params = {
            'GSA':'http://gsaweb.ast.cam.ac.uk/alerts/alert/'+self.id}

    def is_recent(self):
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        if (now - self.isotime) < self.alert_notification_period:
            return True
        return False

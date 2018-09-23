import voeventparse
from collections import OrderedDict
import datetime
import pytz
from fourpisky.utils import convert_voe_coords_to_eqposn
from fourpisky.feeds.asassn import AsassnFeed, AsassnKeys
from fourpisky.triggers.alertbase import AlertBase

default_alert_notification_period = datetime.timedelta(days=4)


class AsassnAlert(AlertBase):
    type_description = "ASASSN alert"

    @staticmethod
    def packet_type_matches(voevent):
        ivorn = voevent.attrib['ivorn']
        if ivorn.startswith(AsassnFeed.stream_ivorn_prefix):
            return True
        return False

    def __init__(self, voevent,
                 alert_notification_period=None):
        self.voevent = voevent
        self.ivorn = self.voevent.attrib['ivorn']
        self.alert_notification_period = alert_notification_period
        if self.alert_notification_period is None:
            self.alert_notification_period = default_alert_notification_period

        if not AsassnAlert.packet_type_matches(voevent):
            raise ValueError(
                "Cannot instantiate AsassnAlert; packet header mismatch.")

        group_params = voeventparse.get_grouped_params(self.voevent)

        text_params_grp = group_params[AsassnFeed.text_params_groupname]
        self.text_params = OrderedDict(
            (k, d['value']) for k, d in text_params_grp.items())

        url_params_grp = group_params[AsassnFeed.url_params_groupname]
        self.url_params = OrderedDict(
            (k, d['value']) for k, d in url_params_grp.items())

        self.id = self.text_params.get(AsassnKeys.id_asassn)
        if self.id is None:
            self.id = self.text_params.get(AsassnKeys.id_other)
        # Assigned name according to the 'why' section of voevent packet:
        self.inferred_name = 'ASASSN @ '+self.text_params.get(AsassnKeys.detection_timestamp)
        self.isotime = voeventparse.get_event_time_as_utc(self.voevent)

        self.position = convert_voe_coords_to_eqposn(
            voeventparse.get_event_position(self.voevent))



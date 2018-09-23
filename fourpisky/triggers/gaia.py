from collections import OrderedDict
import datetime
import voeventparse
from fourpisky.utils import convert_voe_coords_to_eqposn
from fourpisky.feeds.gaia import GaiaFeed
from fourpisky.triggers.alertbase import AlertBase


default_alert_notification_period = datetime.timedelta(days=7)

class GaiaAlert(AlertBase):
    type_description = "GAIA alert"

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

        group_params = voeventparse.get_grouped_params(self.voevent)
        text_params_grp = group_params[GaiaFeed.text_params_groupname]
        self.text_params = OrderedDict(
            (k, d['value']) for k, d in text_params_grp.items())

        self.id = self.text_params.get('Name')
        self.inferred_name = False

        self.isotime = voeventparse.get_event_time_as_utc(self.voevent)
        self.position = convert_voe_coords_to_eqposn(
            voeventparse.get_event_position(self.voevent))

        self.url_params = {
            'GSA':'http://gsaweb.ast.cam.ac.uk/alerts/alert/'+self.id}

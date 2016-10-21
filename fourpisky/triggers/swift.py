import voeventparse
from fourpisky.utils import convert_voe_coords_to_eqposn
from fourpisky.triggers.alertbase import AlertBase

def _swift_bool(bstring):
    """
    Convert a SWIFT-VOevent style boolean string ('true'/'false') to a bool.
    """
    if bstring == 'true':
        return True
    elif bstring == 'false':
        return False
    else:
        raise ValueError("This string does not appear to be a SWIFT VOEvent "
                          "boolean: %s" % bstring)

class BatGrb(AlertBase):
    type_description = "Swift BAT GRB - initial position"
    @staticmethod
    def packet_type_matches(voevent):
        ivorn = voevent.attrib['ivorn']
        if ivorn.startswith("ivo://nasa.gsfc.gcn/SWIFT#BAT_GRB_Pos"):
            return True
        return False


    def __init__(self, voevent):
        self.voevent = voevent
        self.ivorn = self.voevent.attrib['ivorn']
        if not BatGrb.packet_type_matches(voevent):
            raise ValueError("Cannot instantiate AsassnAlert; packet header mismatch.")

        id_long_short = self._pull_swift_bat_id()
        self.id_long = 'SWIFT_' + id_long_short[0]
        self.id = 'SWIFT_' + id_long_short[1]
        #Assigned name according to the 'why' section of voevent packet:
        self.inferred_name = self.voevent.Why.Inference.Name
        self.isotime = voeventparse.pull_isotime(self.voevent)
        self.params = voeventparse.pull_params(self.voevent)
        self.position = convert_voe_coords_to_eqposn(
                                       voeventparse.pull_astro_coords(self.voevent))
        self.alert_notification_period = False

    def reject(self):
        """
        Returns None if all ok, otherwise returns 'reason for rejection' string.
        """
        pars = self.params
        if self.startracker_lost():
            return "Alert occurred while Swift star-tracker had lost lock."

        # if not filters.grb_identified(pars):
        #     if filters.tgt_in_ground_cat(pars) or filters.tgt_in_flight_cat(pars):
        #         return "Not a GRB - target associated with known catalog source"
        #     else:
        #         return """Not identified as GRB, but not a known source.
        #                 See packet for further details."""
        return None

    def startracker_lost(self):
        return _swift_bool(
                       self.params["Misc_Flags"]["ImTrig_during_ST_LoL"]['value'])


    def grb_identified(self):
        return _swift_bool(
            self.params["Solution_Status"]['GRB_Identified']['value'])


    def tgt_in_ground_cat(self):
        return _swift_bool(
            self.params["Solution_Status"]['Target_in_Gnd_Catalog']['value'])


    def tgt_in_flight_cat(self):
        return _swift_bool(
            self.params["Solution_Status"]['Target_in_Flt_Catalog']['value'])


    def _pull_swift_bat_id(self):
        alert_id = self.voevent.attrib['ivorn'][len('ivo://nasa.gsfc.gcn/SWIFT#BAT_GRB_Pos_'):]
        alert_id_short = alert_id.split('-')[0]
        return alert_id, alert_id_short




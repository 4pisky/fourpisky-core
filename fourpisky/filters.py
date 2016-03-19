"""Various bits of logic designed to filter out unwanted VOEvent alerts"""
from fourpisky.visibility import DEG_PER_RADIAN

class ami:
    @staticmethod
    def reject(position):
        dec_limit = 0.0
        if position.dec*DEG_PER_RADIAN < dec_limit:
            return "Target below declination limit of %s degrees" % dec_limit
        return None



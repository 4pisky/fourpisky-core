import voeventparse
from fourpisky.utils import convert_voe_coords_to_eqposn
from collections import OrderedDict
import datetime
import pytz
from fourpisky.requiredatts import RequiredAttributesMetaclass

class AlertBase(object):
    __metaclass__ = RequiredAttributesMetaclass
    _required_attributes = [
        'alert_notification_period',
        'id',
        'inferred_name',
        'isotime',
        'ivorn',
        'position',
        'type_description',
    ]

    @property
    def full_name(self):
        name = self.id
        if self.inferred_name:
            name+= ' / ' + self.inferred_name
        return name


    def is_recent(self):
        if not self.alert_notification_period:
            return True
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        if (now - self.isotime) < self.alert_notification_period:
            return True
        return False
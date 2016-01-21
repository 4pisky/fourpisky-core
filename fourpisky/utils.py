"""
Misc. convenience routines.
"""
from __future__ import absolute_import
import os
import string
from collections import Sequence
from ephem import Equatorial, J2000
from fourpisky.visibility import DEG_PER_RADIAN
import voeventparse


def listify(x):
    """
    Returns [x] if x is not already a list.

    Used to make functions accept either scalar or array inputs -
    simply `listify` a variable to make sure it's in list format.
    """
    if (not isinstance(x, basestring)) and isinstance(x, Sequence):
        return x
    else:
        return [x]


def ensure_dir(filename):
    """Ensure parent directory exists, so you can write to `filename`."""
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        os.makedirs(d)


def convert_voe_coords_to_eqposn(c):
    """Unit-checked conversion from voeventparse.Position2D -> astropysics FK5"""
    acceptable_coord_sys = (
        voeventparse.definitions.sky_coord_system.utc_fk5_geo,
        voeventparse.definitions.sky_coord_system.utc_icrs_geo
    )

    if (c.system not in acceptable_coord_sys
        or c.units != 'deg'):
        raise ValueError(
                "Unrecognised Coords type: %s, %s" % (c.system, c.units))
    return Equatorial(c.ra / DEG_PER_RADIAN, c.dec / DEG_PER_RADIAN,
                      epoch=J2000)


def namedtuple_to_dict(nt):
    return {key: nt[i] for i, key in enumerate(nt._fields)}


def sanitise_string_for_stream_id(unsafe_string):
    """
    Removes any unhelpful characters (e.g. #,/,<space>,%) from a string.

    We pass:
        -Letters ([A-Za-z])
        -digits ([0-9]),
        -hyphens ("-"),underscores ("_"), colons (":"), and periods (".")
        -Plus symbol ('+')

    We replace '\', '/','#', and <space> by underscore.
    """
    s = unsafe_string
    if unsafe_string[0] == ".":
        s = unsafe_string[1:]
    return "".join(c for c in
                   s.replace('/', '_').replace('\\', '_'). \
                   replace('#', '_').replace(' ', '_')
                   if c in string.ascii_letters + string.digits + '_-:.+')

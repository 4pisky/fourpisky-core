from __future__ import absolute_import


import fourpisky.comms
import fourpisky.visibility
import fourpisky.filters
import fourpisky.formatting
import fourpisky.triggers
import fourpisky.utils
import fourpisky.voevent
import socket

from ._version import get_versions
__versiondict__ = get_versions()
__version__ = __versiondict__['version']
del get_versions


def base_context():
    """
    Get a dictionary of context variables used across multiple templates.
    """
    hostname = socket.gethostname()
    return dict(
        versions=__versiondict__,
        hostname=hostname,
        dt_style=fourpisky.formatting.datetime_format_long
    )
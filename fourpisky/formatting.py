"""Various code snippets used for formatting and generating messages"""
from __future__ import absolute_import
import urllib
from fourpisky.visibility import DEG_PER_RADIAN

from jinja2 import Environment, PackageLoader

#----------------------------------------------------
datetime_format_long = "%Y-%m-%d %H:%M:%S (%A)"
datetime_format_short = '%y%m%d-%H%M.%S'
day_time_format_short = "%a%H:%M"
time_format_short = "%H:%M"
#----------------------------------------------------
def format_datetime(dt, format=None):
    if format:
        return dt.strftime(format)
    else:
        return dt #Converts to a reasonable default string anyway.

def rad_to_deg(rad):
    return rad*DEG_PER_RADIAN

def urlquote(url):
    return urllib.quote_plus(url)



fps_template_env = Environment(loader=PackageLoader('fourpisky', 'templates'),
                               trim_blocks=True, lstrip_blocks=True)
fps_template_env.filters['datetime'] = format_datetime
fps_template_env.filters['rad_to_deg'] = rad_to_deg
fps_template_env.filters['urlquote'] = urlquote
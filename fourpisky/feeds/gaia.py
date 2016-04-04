import voeventparse as vp
import datetime
import iso8601
import astropy.time
import contextlib
import StringIO
import csv
from astropy.coordinates import SkyCoord
import astropy.units as u
from fourpisky.voevent import (
    create_skeleton_4pisky_voevent,
    gaia_alert_substream,
    get_stream_ivorn_prefix,
    datetime_format_short,
)

from fourpisky.feeds.feedbase import FeedBase
import logging

logger = logging.getLogger(__name__)


class GaiaKeys():
    """
    Col headers used in CSV

    Full definitions at http://gsaweb.ast.cam.ac.uk/alerts/tableinfo
    """
    # Name, Date, RaDeg, DecDeg, AlertMag, HistoricMag, HistoricStdDev, Class, Published, Comment
    name = '#Name'
    obs_timestamp = ' Date'
    pub_timestamp = ' Published'
    ra = ' RaDeg'
    dec = ' DecDeg'
    mag_alert = ' AlertMag'
    mag_historic = ' HistoricMag'
    mag_historic_std_dev = ' HistoricStdDev'
    alert_class = ' Class'
    comment = ' Comment'


class GaiaFeed(FeedBase):
    name = "GAIA science alerts"
    url = "http://gsaweb.ast.cam.ac.uk/alerts/alerts.csv"
    substream = gaia_alert_substream
    stream_ivorn_prefix = get_stream_ivorn_prefix(substream)
    hash_byte_range = (0, 10000)
    hash_cache_path = None

    # VOEvent details:
    text_params_groupname = 'gaia_params'

    def __init__(self, hash_cache_path=None):
        super(GaiaFeed, self).__init__(hash_cache_path)

    def parse_content_to_event_data_list(self):
        with contextlib.closing(StringIO.StringIO(self.content)) as f:
            rdr = csv.DictReader(f)
            events = [row for row in rdr]
        return events

    def event_data_to_event_id(self, event_data):
        """
        Derive a feed-specific identifier for a given event.

        Args:
            event_data: Feed specific datastructure, typically just a dictionary.
        """
        return event_data[GaiaKeys.name]

    def get_ivorn_prefix_for_duplicate(self, feed_id):
        """
        Determines what a possible duplicate ivorn might be prefixed by.

        For GAIA - events are already uniquely identified by their GAIA ID
        rather than being renamed to match other event streams. So we expect
        only exact IVORN matches:
        """
        return self.feed_id_to_ivorn(feed_id)

    def generate_voevent(self, feed_id):
        event_data = self.event_id_data_map[feed_id]

        stream_id = self.feed_id_to_stream_id(feed_id)
        v = create_skeleton_4pisky_voevent(substream=self.substream,
                                           stream_id=stream_id,
                                           role=vp.definitions.roles.observation,
                                           date=datetime.datetime.utcnow()
                                           )

        vp.add_how(v, references=vp.Reference(uri=self.url))
        v.How.Description = "Parsed from GAIA Science Alerts listings by 4PiSky-Bot."

        posn_sc = SkyCoord(event_data[GaiaKeys.ra],
                           event_data[GaiaKeys.dec],
                           unit=(u.deg, u.deg))

        # Astrometric accuracy is a guesstimate,
        # http://gsaweb.ast.cam.ac.uk/alerts/tableinfo states that:
        # "The sky position may either refer to a source in Gaia's own
        # catalogue, or to a source in an external catalogue (e.g. SDSS) used as
        # a reference for combining Gaia observations. Where the position comes
        # from Gaia's catalogue, it is derived from a single, Gaia observation
        # at the triggering point of the alert; this is not an astrometric
        # measurement to the full precision of the Gaia main mission."
        #
        # We assume a 'worst-case' scenario of 100mas from SDSS at mag r=22, cf
        # http://classic.sdss.org/dr7/products/general/astrometry.html
        err_radius_estimate = 0.1 * u.arcsec

        posn_simple = vp.Position2D(ra=posn_sc.ra.deg,
                                    dec=posn_sc.dec.deg,
                                    err=err_radius_estimate.to(u.deg).value,
                                    units=vp.definitions.units.degrees,
                                    system=vp.definitions.sky_coord_system.utc_icrs_geo,
                                    )

        # NB GAIA values are in Barycentric co-ordinate time
        # (http://en.wikipedia.org/wiki/Barycentric_Coordinate_Time)
        observation_time_tcb = astropy.time.Time(
            event_data[GaiaKeys.obs_timestamp],
            scale='tcb')
        # We convert to UTC, in keeping with other feeds:
        observation_time_utc_dt = observation_time_tcb.utc.datetime

        vp.add_where_when(
            v,
            coords=posn_simple,
            obs_time=observation_time_utc_dt,
            observatory_location=vp.definitions.observatory_location.geosurface)

        gaia_params = [vp.Param('Name', event_data[GaiaKeys.name])]
        gaia_params.extend([vp.Param(key.strip(), event_data[key]) for key in
                            (GaiaKeys.alert_class,
                             GaiaKeys.obs_timestamp,
                             GaiaKeys.pub_timestamp,
                             GaiaKeys.ra,
                             GaiaKeys.dec,
                             GaiaKeys.comment,
                             )
                            ])
        gaia_params.extend([vp.Param(key.strip(), event_data[key],
                                     unit='mag', ucd='phot.mag') for key in (
                                GaiaKeys.mag_alert,
                                GaiaKeys.mag_historic,
                                GaiaKeys.mag_historic_std_dev,
                            )
                            ])
        v.What.append(vp.Group(params=gaia_params,
                               name=self.text_params_groupname))

        return v

# ==========================================================================

import lxml
import lxml.html
import shelve
from collections import defaultdict
from contextlib import closing
import urllib2
import requests
import hashlib
import voeventparse as vp
import datetime
import iso8601
from astropy.coordinates import SkyCoord
import astropy.units as u
from voeventdb.server.database import session_registry
import voeventdb.server.database.convenience as dbconvenience
from fourpisky.voevent import (
    ivorn_base,
    create_skeleton_4pisky_voevent,
    asassn_alert_substream,
    get_stream_ivorn_prefix,
)
from fourpisky.utils import sanitise_string_for_stream_id
import logging

logger = logging.getLogger(__name__)


class AsassnFeed(object):
    name = "ASASSN webpage"
    url = "http://www.astronomy.ohio-state.edu/~assassin/transients.html"
    substream = asassn_alert_substream
    stream_ivorn_prefix = get_stream_ivorn_prefix(substream)
    hash_byte_range = (0, 10000)
    hash_cache_path = None

    #VOEvent details:
    text_params_groupname = 'asassn_params'
    url_params_groupname = 'asassn_urls'

    def __init__(self, hash_cache_path=None):
        self.hash_cache_path = hash_cache_path
        self._content = None
        self._old_hash = None
        self._new_hash = None
        self._id_row_map = None

    @property
    def content(self):
        if self._content is None:
            r = requests.get(self.url)
            self._content = r.content
        return self._content

    @property
    def old_hash(self):
        if not self.hash_cache_path:
            logger.debug("No hash-cache path set")
            return None
        with closing(shelve.open(self.hash_cache_path)) as hash_cache:
            if self.url in hash_cache:
                return hash_cache[self.url]
            else:
                logger.debug("Feed {} not found in hash-cache at {}".format(
                        self.url, self.hash_cache_path
                ))
        return None

    @property
    def new_hash(self):
        if not self._new_hash:
            if self.hash_byte_range:
                logger.debug(
                        "Fetching bytes {start}-{end} from {url} for hash-check".format(
                                start=self.hash_byte_range[0],
                                end=self.hash_byte_range[1],
                                url=self.url,
                        ))
                req = urllib2.Request(self.url)
                req.headers['Range'] = 'bytes={}-{}'.format(
                        *self.hash_byte_range)
                data = urllib2.urlopen(req).read()
            else:
                data = self.content
            self._new_hash = hashlib.md5(data).hexdigest()
        return self._new_hash

    @property
    def mock_new_hash(self):
        """
        Compute the hash of byte-range from pre-assigned content.

        (Used for testing.)
        """
        return hashlib.md5(
                self._content[self.hash_byte_range[0]:self.hash_byte_range[1]]
        ).hexdigest()

    @property
    def id_row_map(self):
        if self._id_row_map is None:
            row_list = parse_content_to_dict_list(self.content)
            self._id_row_map = {rowdict_to_feed_id(rd): rd for rd in row_list}
        return self._id_row_map

    def save_new_hash(self):
        with closing(shelve.open(self.hash_cache_path)) as hash_cache:
            hash_cache[self.url] = self.new_hash
        logger.debug("Inserted hash for feed {} in cache {}; md5={}".format(
                self.url, self.hash_cache_path, self.new_hash
        ))

    def feed_id_to_stream_id(self, feed_id):
        # Currently just a wrapper, bound to class for convenience.
        # Could be customised in future though.
        return sanitise_string_for_stream_id(feed_id)

    def feed_id_to_ivorn(self, feed_id):
        safe_id = self.feed_id_to_stream_id(feed_id)
        return self.stream_ivorn_prefix + safe_id

    def generate_voevent(self, feed_id):
        rowdict = self.id_row_map[feed_id]
        params = rowdict['param']
        urls = rowdict['url']
        stream_id = self.feed_id_to_stream_id(feed_id)
        v = create_skeleton_4pisky_voevent(substream=self.substream,
                                           stream_id=stream_id,
                                           role=vp.definitions.roles.observation,
                                           date=datetime.datetime.utcnow()
                                           )

        vp.add_how(v, references=vp.Reference(uri=self.url))
        v.How.Description = "Parsed from ASASSN listings page by 4PiSky-Bot."

        timestamp_dt = asassn_timestamp_str_to_datetime(
                params[AsassnKeys.detection_timestamp])

        posn_sc = SkyCoord(params['ra'], params['dec'],
                           unit=(u.hourangle, u.deg))

        # Couldn't find a formal analysis of positional accuracy, but
        # http://dx.doi.org/10.1088/0004-637X/788/1/48
        # states the angular resolution as 16 arcseconds, so we'll go with that.
        err_radius_estimate = 16 * u.arcsec

        posn_simple = vp.Position2D(ra=posn_sc.ra.deg,
                                    dec=posn_sc.dec.deg,
                                    err=err_radius_estimate.to(u.deg).value,
                                    units=vp.definitions.units.degrees,
                                    system=vp.definitions.sky_coord_system.utc_icrs_geo,
                                    )

        vp.add_where_when(
                v,
                coords=posn_simple,
                obs_time=timestamp_dt,
                observatory_location=vp.definitions.observatory_location.geosurface)
        asassn_params = [vp.Param(key, params[key]) for key in
                         (AsassnKeys.id_asassn,
                          AsassnKeys.id_other,
                          AsassnKeys.detection_timestamp,
                          AsassnKeys.ra,
                          AsassnKeys.dec,
                          AsassnKeys.spec_class,
                          AsassnKeys.comment,
                          )
                         if key in params
                         ]

        if AsassnKeys.mag_v in params:
            asassn_params.append(
                    vp.Param(AsassnKeys.mag_v, params[AsassnKeys.mag_v],
                             unit='mag', ucd="phot.mag",
                             )
            )
        if AsassnKeys.id_other in urls:
            asassn_params.append(
                    vp.Param(AsassnKeys.id_other,
                             urls[AsassnKeys.id_other][0][0])
            )
        asassn_urls = [vp.Param(key, urls[key][0][1]) for key in urls]

        v.What.append(vp.Group(params=asassn_params,
                               name=self.text_params_groupname))
        v.What.append(vp.Group(params=asassn_urls,
                               name=self.url_params_groupname))

        return v

    def determine_new_ids_from_localdb(self):
        s = session_registry()
        new_ids = []
        for feed_id in self.id_row_map:
            ivo = self.feed_id_to_ivorn(feed_id)
            if not dbconvenience.ivorn_present(s, ivo):
                dupes_prefix = self.get_ivorn_prefix_for_matched_timestamp(ivo)
                if dbconvenience.ivorn_prefix_present(s, dupes_prefix):
                    logger.warning(
                            "Possible duplicate - timestamp prefixes match but "
                            "full ivorn has changed (will not insert): {}".format(
                                    ivo
                            ))
                else:
                    new_ids.append(feed_id)
        return new_ids

    def get_ivorn_prefix_for_matched_timestamp(self, ivorn):
        """
        Determines what a possible duplicate ivorn might be prefixed by.

        Used for duplicate checking - assumes timestamp unchanging even if the
        event gets renamed. We extract the timestamp portion from the given
        IVORN, then re-append it to the stream-ivorn prefix.
        """
        stream_id = ivorn[len(self.stream_ivorn_prefix):]
        return self.stream_ivorn_prefix + stream_id.split('_', 1)[0]


# ==========================================================================
def parse_content_to_dict_list(content):
    tree = lxml.html.fromstring(content)
    events = parse_pagetree(tree)
    return events


timestamp_id_map = {
    '2013-09-14.53': 'iPTF13dge',  # Malformed href in other id col.
}


def extract_asassn_id(rowdict):
    params = rowdict['param']
    urls = rowdict['url']
    # print params
    # print urls

    # Check for known-bad rows, manually resolved:
    timestamp = params[AsassnKeys.detection_timestamp]
    if timestamp in timestamp_id_map:
        return timestamp_id_map[timestamp]

    # Now try to parse any vaguely reasonable data
    asassn_id = params.get(AsassnKeys.id_asassn)
    if asassn_id is not None:
        if asassn_id.startswith('ASASSN') or asassn_id.startswith('ASASN'):
            external_id = asassn_id
        else:
            raise ValueError('Could not extract Id for this row, '
                             'unrecognised ASASSN id format')
    else:
        # Ensure ASASSN ID is not something weird
        assert asassn_id is None
        # Then, look for alt-id
        alt_id_text = params.get(AsassnKeys.id_other)
        alt_id_url = urls.get(AsassnKeys.id_other)
        # Otherwise, check for alt_id text:
        if alt_id_text:
            external_id = alt_id_text.strip()
        elif alt_id_url:
            first_url_text_href_pair = alt_id_url[0]
            external_id = first_url_text_href_pair[0]
        else:
            cell = rowdict['raw'][asassn_headers.index('ATEL')]
            # print cell.text
            # print [c.text for c in cell.getchildren()]
            # print '-------------------'
            # print '-------------------'
            raise ValueError('Could not extract Id for this row, '
                             'no id found')
    return external_id

def asassn_timestamp_str_to_datetime(timestamp_str):
        if '.' in timestamp_str:
            date_str, day_fraction_str = timestamp_str.split('.')
            day_fraction_str = '0.' + day_fraction_str
        else:
            date_str = timestamp_str
            day_fraction_str = 0.

        timestamp_dt = (iso8601.parse_date(date_str) +
                        datetime.timedelta(days=float(day_fraction_str)))
        return timestamp_dt

def rowdict_to_feed_id(rowdict):
    """
    NB timestamp goes first in the feed id, we rely on this for deduplication.
    """
    external_id = extract_asassn_id(rowdict)
    #We reformat the date-string to zero-pad the day digit as needed.
    timestamp_dt = asassn_timestamp_str_to_datetime(
            rowdict['param'][AsassnKeys.detection_timestamp]).replace(tzinfo=None)
    uniform_date_str = timestamp_dt.strftime('%Y-%m-%d')
    start_of_day = datetime.datetime(timestamp_dt.year,
                                     timestamp_dt.month,
                                     timestamp_dt.day
                                     )
    #Friday afternoon kludge:
    day_fraction_str = str((timestamp_dt - start_of_day).total_seconds()/3600./24.)[1:]
    feed_id = ''.join((uniform_date_str,day_fraction_str,
                      '_',external_id))
    return feed_id


# =======================================================================

asassn_headers = (
    'ASAS-SN',
    'Other',
    'ATEL',
    'RA',
    'Dec',
    'Discovery',
    'V',
    'SDSS',
    'DSS',
    'Vizier',
    'Spectroscopic Class',
    'Comments'
)

asassn_ncols = len(asassn_headers)


class AsassnKeys():
    id_asassn = 'id_assasn'
    id_other = 'id_other'
    atel_url = 'atel_url'
    ra = 'ra'
    dec = 'dec'
    detection_timestamp = 'detection_timestamp'
    mag_v = 'mag_v'
    sdss_url = 'sdss_url'
    dss_url = 'dss_url'
    vizier_url = 'vizier_url'
    spec_class = 'spec_class'
    comment = 'comment'


asassn_key_hdr_map = {
    'ASAS-SN': AsassnKeys.id_asassn,
    'Other': AsassnKeys.id_other,
    'ATEL': AsassnKeys.atel_url,
    'RA': AsassnKeys.ra,
    'Dec': AsassnKeys.dec,
    'Discovery': AsassnKeys.detection_timestamp,
    'V': AsassnKeys.mag_v,
    'SDSS': AsassnKeys.sdss_url,
    'DSS': AsassnKeys.dss_url,
    'Vizier': AsassnKeys.vizier_url,
    'Spectroscopic Class': AsassnKeys.spec_class,
    'Comments': AsassnKeys.comment,
}

asassn_url_only_keys = (
    AsassnKeys.atel_url,
    AsassnKeys.sdss_url,
    AsassnKeys.dss_url,
    AsassnKeys.vizier_url,
)


def extract_etree_cells(tree):
    tbl = tree.xpath('//table')[0]
    children = tbl.getchildren()

    # expect two header rows, then a malformed data row. Joy.
    assert children[0].tag == 'tr'
    assert children[1].tag == 'tr'
    assert children[2].tag != 'tr'

    cells = children[2:]
    headers = tuple([c.text for c in children[0].getchildren()])
    # We expect a multiple of assasn_ncols:
    assert (len(cells) % asassn_ncols) == 0
    # Check headers unchanged
    assert headers == asassn_headers
    return cells


def asassn_htmlrow_to_dict(cellrow):
    param_dict = {}
    url_dict = defaultdict(list)
    for idx, col_hdr in enumerate(asassn_headers):
        param_key = asassn_key_hdr_map[col_hdr]
        elt = cellrow[idx]
        if elt.text and not col_hdr in asassn_url_only_keys:
            text = elt.text.strip()
            param_dict[param_key] = text
        children = elt.getchildren()
        if children:
            for child in children:
                if 'href' in child.attrib:
                    url_dict[param_key].append(
                            (child.text, child.attrib['href'])
                    )
    # Delete any entries which are merely placeholders, e.g. '-----'.
    for k in param_dict.keys():
        v = param_dict[k]
        if not len(v.strip().replace('-', '')):
            param_dict.pop(k)

    return {'param': param_dict,
            'url': url_dict,
            'raw': cellrow
            }


def parse_pagetree(tree):
    cells = extract_etree_cells(tree)
    cellrows = []
    # Stride through cells at rowlength inferred by ncols
    for row_idx, _ in enumerate(cells[::asassn_ncols]):
        # Select all cells in current stride, create list representing row
        row = [c for c in cells[
                          asassn_ncols * row_idx:asassn_ncols * row_idx + asassn_ncols]]
        cellrows.append(row)
    events = [asassn_htmlrow_to_dict(cr) for cr in cellrows]
    return events

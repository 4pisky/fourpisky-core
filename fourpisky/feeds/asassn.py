import lxml
import lxml.html
from collections import defaultdict
import voeventparse as vp
import datetime
import iso8601
from astropy.coordinates import SkyCoord
import astropy.units as u
from fourpisky.voevent import (
    create_skeleton_4pisky_voevent,
    asassn_alert_substream,
    get_stream_ivorn_prefix,
)

from fourpisky.feeds.feedbase import FeedBase
import logging

logger = logging.getLogger(__name__)

ASSASN_BAD_IDS = [
    'ASASSN-15uh',  # Datestamp has been replaced with junk
    'ASASSN-15co',  # Datestamp has been replaced with junk
    'Comet ASASSN1',  # Moving object
]

ASASSN_TIMESTAMP_ID_MAP = {
    '2013-09-14.53': 'iPTF13dge',  # Malformed href in other id col.
}

ASASSN_EARLIEST_REPARSE_DATE=iso8601.parse_date("2017-10-18")

class AsassnFeed(FeedBase):
    name = "ASASSN webpage"
    url = "http://www.astronomy.ohio-state.edu/asassn/transients.html"
    substream = asassn_alert_substream
    stream_ivorn_prefix = get_stream_ivorn_prefix(substream)
    hash_byte_range = (0, 10000)
    hash_cache_path = None

    # VOEvent details:
    text_params_groupname = 'asassn_params'
    url_params_groupname = 'asassn_urls'

    def __init__(self, hash_cache_path=None):
        super(AsassnFeed, self).__init__(hash_cache_path)

    def generate_voevent(self, feed_id):
        rowdict = self.event_id_data_map[feed_id]
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

    def event_data_to_event_id(self, event_data):
        """
        Derive a feed-specific identifier for a given event.

        Args:
            event_data: Feed specific datastructure, typically just a dictionary.

        NB feed id should contain timestamp prefix followed by underscore,
        we use this for deduplication.
        (Even if the event details are updated the timestamp should remain the
        same.)
        """
        # OK. Fiddly date-string formatting. Aim here is to get a uniform
        # date-time format so that anything ordered by IVORN will also
        # be date-time ordered. Users can always check the XML content
        # for the original ASSASSN timestamp-string.
        # We parse-and-reformat the date-string to zero-pad the day digit as
        # needed.
        # Finally, we regenerate the 'decimal-days' suffix,
        # fixed at 2 decimal places.
        # (since some earlier events don't have this suffix at all we can't
        # just tokenize it).

        external_id = extract_asassn_id(event_data)
        timestamp_input_string = event_data['param'][
            AsassnKeys.detection_timestamp]
        timestamp_dt = asassn_timestamp_str_to_datetime(
            timestamp_input_string).replace(tzinfo=None)

        uniform_date_str = timestamp_dt.strftime('%Y-%m-%d')
        start_of_day = datetime.datetime(timestamp_dt.year,
                                         timestamp_dt.month,
                                         timestamp_dt.day
                                         )
        # Friday afternoon kludge:
        day_fraction_float = (
                (timestamp_dt - start_of_day).total_seconds() / 3600. / 24.
        )
        day_fraction_str = f"{day_fraction_float:.2f}"[1:]
        feed_id = ''.join((uniform_date_str, day_fraction_str,
                           '_', external_id))
        return feed_id

    def get_ivorn_prefixes_for_duplicate(self, feed_id):
        """
        Determines what a possible duplicate ivorn might be prefixed by.

        For ASASSN - assumes timestamp unchanging even if the
        event gets renamed. We match on the substream + timestamp
        (i.e. everything up to the first underscore in the stream_id).
        """
        stream_id = self.feed_id_to_stream_id(feed_id)
        return [
            self.stream_ivorn_prefix + stream_id.split('_', 1)[0],
        ]

    def parse_content_to_event_data_list(self):
        tree = lxml.html.fromstring(self.content)
        events = transform_pagetree(tree)
        return events


# ==========================================================================


def extract_asassn_id(rowdict):
    params = rowdict['param']
    urls = rowdict['url']
    # print group_params
    # print urls

    # Check for known-bad rows, manually resolved:
    timestamp = params[AsassnKeys.detection_timestamp]
    if timestamp in ASASSN_TIMESTAMP_ID_MAP:
        return ASASSN_TIMESTAMP_ID_MAP[timestamp]

    # Now try to parse any vaguely reasonable data
    asassn_id = params.get(AsassnKeys.id_asassn)
    if asassn_id is not None:
        if asassn_id.startswith('ASASSN') or asassn_id.startswith('ASASN'):
            external_id = asassn_id
        else:
            raise ValueError(
                f'Could not extract Id for row- unrecognised id format: {asassn_id}')
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
            cell = rowdict['raw'][asassn_headers_2018.index('ATEL')]
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


# =======================================================================

asassn_headers_2018 = (
    'ASAS-SN',
    'Other',
    'ATEL',
    'RA',
    'Dec',
    'Discovery',
    'V/g',
    'SDSS',
    'DSS',
    'Vizier',
    'Spectroscopic Class',
    'Comments'
)

asassn_ncols = len(asassn_headers_2018)


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


asassn_hdr_to_internal_key_map = {
    'ASAS-SN': AsassnKeys.id_asassn,
    'Other': AsassnKeys.id_other,
    'ATEL': AsassnKeys.atel_url,
    'RA': AsassnKeys.ra,
    'Dec': AsassnKeys.dec,
    'Discovery': AsassnKeys.detection_timestamp,
    'V/g': AsassnKeys.mag_v,
    'SDSS': AsassnKeys.sdss_url,
    'DSS': AsassnKeys.dss_url,
    'Vizier': AsassnKeys.vizier_url,
    'Spectroscopic Class': AsassnKeys.spec_class,
    'Comments': AsassnKeys.comment,
}

assert tuple(asassn_hdr_to_internal_key_map.keys()) == asassn_headers_2018

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
    assert headers == asassn_headers_2018
    return cells


def asassn_htmlrow_to_dict(cellrow):
    param_dict = {}
    url_dict = defaultdict(list)
    for idx, col_hdr in enumerate(asassn_headers_2018):
        param_key = asassn_hdr_to_internal_key_map[col_hdr]
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
    trimmed_params = {}
    for k, v in param_dict.items():
        if not len(v.strip().replace('-', '')):
            continue  # Skip this one if it's a  '------' style placeholder
        trimmed_params[k] = v

    return {'param': trimmed_params,
            'url': url_dict,
            'raw': cellrow
            }


def transform_pagetree(tree):
    """
    Restructure an array of cells into a list of dictionaries

    Since parsing to this stage is robust, we also perform bad-row excision here.
    """
    cells = extract_etree_cells(tree)
    cellrows = []
    # Stride through cells at rowlength inferred by ncols
    for row_idx, _ in enumerate(cells[::asassn_ncols]):
        # Select all cells in current stride, create list representing row
        row = [c for c in cells[
                          asassn_ncols * row_idx:asassn_ncols * row_idx + asassn_ncols]]
        cellrows.append(row)
    events = []
    for cr in cellrows:
        event_dict = asassn_htmlrow_to_dict(cr)
        row_id = event_dict['param'].get(AsassnKeys.id_asassn)
        if row_id in ASSASN_BAD_IDS:
            logger.warning('Removed bad ASASSN row with ID {}'.format(row_id))
            continue
        try:
            row_timestamp = asassn_timestamp_str_to_datetime(
                event_dict['param'].get(AsassnKeys.detection_timestamp)
            )
            if not row_timestamp > ASASSN_EARLIEST_REPARSE_DATE:
                continue
            events.append(event_dict)
        except:
            logger.exception('Error parsing rowdict:' + str(event_dict))
            raise
    return events

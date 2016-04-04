from __future__ import absolute_import

import voeventparse as vp
import datetime
import uuid
from copy import copy
from fourpisky._version import get_versions

fpsversion = get_versions()['version']

ivo_prefix = "ivo://"
ivorn_base = 'voevent.4pisky.org'
test_trigger_substream = 'TEST-TRIGGER'
test_response_substream = 'TEST-RESPONSE'
alarrm_request_substream = 'ALARRM-REQUEST'
alarrm_obs_test_substream = 'ALARRM-OBSTEST'
asassn_alert_substream = 'ASASSN'
gaia_alert_substream = 'GAIA'


def get_stream_ivorn_prefix(substream):
    return ''.join((ivo_prefix, ivorn_base, '/', substream, '#'))


datetime_format_short = '%y%m%d-%H%M.%S'

def generate_stream_id(dtime):
    """
    Get a string for use as a stream ID.

    The idea is to create a stream ID that is largely human-readable
    (hence the timestamp), and compact, but will not repeat if multiple packets
    are generated within a small timespan (within reason).
    To do this, we assume that only a single machine
    is generating alerts in a given stream. This means we can generate
    a uuid1() hexstring and throw away the static bytes which are derived from the
    machine's MAC address. This way we reduce the UUID hex length from
    32 chars to 12.

    """
    datetime_format_short = '%y%m%d-%H%M.%S'
    timestamp = dtime.strftime(datetime_format_short)
    uuid_hex = uuid.uuid1().hex
    uuid_substr = uuid_hex[:8] + uuid_hex[16:20]
    stream_id = timestamp+'_'+uuid_substr
    return stream_id


def create_skeleton_4pisky_voevent(substream, stream_id,
                                   role=vp.definitions.roles.test,
                                   date=None):
    """
    Create a basic empty VOEvent with valid author details

    Args:
        substream (str): Comes after the domain, before the #
            E.g. 'ALARRM-REQUEST' or 'TEST-TRIGGER'
        stream_id (str):  ID within this stream, may be some combination
            of timestamp and / or unique ID.
        role (str): Voevent role
        date (datetime): 'Author date' to assign, typically current time
            at VOEvent generation.

    """
    author_ivorn = ivorn_base + '/robots'
    if date is None:
        date = datetime.datetime.utcnow()

    v = vp.Voevent(stream=ivorn_base + '/' + substream,
                   stream_id=stream_id, role=role)
    v.Who.Description = (
        "VOEvent created by 4PiSky bot, version {}. "
        "See https://github.com/4pisky/fourpisky-core for details.".format(
                fpsversion))
    vp.set_who(v, date=date,
               author_ivorn=author_ivorn)

    vp.set_author(v,
                  shortName="4PiSkyBot",
                  contactName="Tim Staley",
                  contactEmail="tim.staley@physics.ox.ac.uk",
                  contributor=fpsversion
                  )
    return v


def create_4pisky_test_trigger_voevent():
    now = datetime.datetime.utcnow()
    stream_id = generate_stream_id(now)
    test_packet = create_skeleton_4pisky_voevent(
            substream=test_trigger_substream,
            stream_id=stream_id,
            role=vp.definitions.roles.test,
            date=now,
    )
    return test_packet


def create_4pisky_test_response_voevent(stream_id, date):
    response = create_skeleton_4pisky_voevent(
            substream=test_response_substream,
            stream_id=stream_id,
            role=vp.definitions.roles.test,
            date=date
    )
    return response


def create_ami_followup_notification(alert, stream_id,
                                     request_status,
                                     superseded_ivorns=None):
    orig_pkt = alert.voevent
    voevent = create_skeleton_4pisky_voevent(
            substream=alarrm_request_substream,
            stream_id=stream_id,
            role=vp.definitions.roles.utility)
    vp.add_how(voevent, descriptions="AMI Large Array, Cambridge",
               references=vp.Reference(
                       "http://www.mrao.cam.ac.uk/facilities/ami/ami-technical-information/"),
               )
    voevent.Why = copy(orig_pkt.Why)
    vp.add_citations(voevent,
                     citations=vp.Citation(ivorn=orig_pkt.attrib['ivorn'],
                                           cite_type=vp.definitions.cite_types.followup))
    voevent.What.Description = "A request for AMI-LA follow-up has been made."

    request_params = [vp.Param(key, val)
                      for key, val in request_status.iteritems()]
    g = vp.Group(request_params, name='request_status')
    voevent.What.append(g)

    # Also copy target location into WhereWhen
    voevent.WhereWhen = copy(orig_pkt.WhereWhen)
    # But the time marker should refer to the AMI observation:
    # (We are already citing the original Swift alert)
    ac = voevent.WhereWhen.ObsDataLocation.ObservationLocation.AstroCoords
    del ac.Time
    voevent.WhereWhen.Description = "Target co-ords from original Swift BAT alert"

    return voevent


def create_alarrm_obs_test_event():
    now = datetime.datetime.utcnow()
    test_packet = create_skeleton_4pisky_voevent(
            substream=alarrm_obs_test_substream,
            stream_id=now.strftime(datetime_format_short),
            role=vp.definitions.roles.test,
            date=now,
    )

    fake_position = vp.Position2D(
            ra=45, dec=45, err=0.1,
            units=vp.definitions.units.degrees,
            system=vp.definitions.sky_coord_system.utc_icrs_geo)
    vp.add_where_when(
            test_packet,
            fake_position,
            obs_time=now,
            observatory_location=vp.definitions.observatory_location.geosurface)

    test_packet.What.append(
            vp.Param(name='flux_density', value=0.1,
                     unit=vp.definitions.units.jansky,
                     ucd='phot.flux.density;Em.radio.12-30GHz'))
    test_packet.What.append(
            vp.Param(name='central_frequency', value=15e9,
                     unit=vp.definitions.units.hertz,
                     ucd='Instr.bandpass'))
    return test_packet

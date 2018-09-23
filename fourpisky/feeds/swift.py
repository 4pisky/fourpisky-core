import datetime
import logging

import lxml
import lxml.html
import voeventdb.server.database.models as models
import voeventparse as vp
from fourpisky.feeds.feedbase import FeedBase
from fourpisky.triggers.swift import BatGrb
from fourpisky.voevent import (
    create_skeleton_4pisky_voevent,
)
from fourpisky.voevent import (
    swift_annotate_substream,
    get_stream_ivorn_prefix,
)
from voeventdb.server.database import session_registry

logger = logging.getLogger(__name__)


class SwiftFeedKeys():
    duration = 'duration'
    battblocks_failed = 'battblocks_failed'
    t90 = 't90'
    t90_err = 't90_err'
    t50 = 't50'
    t50_err = 't50_err'


class SwiftFeed(FeedBase):
    name = None
    url = "http://gcn.gsfc.nasa.gov/notices_s/{trigger_id}/BA/"
    substream = swift_annotate_substream
    stream_ivorn_prefix = get_stream_ivorn_prefix(substream)
    hash_byte_range = False
    hash_cache_path = None

    def __init__(self, trigger_event, hash_cache_path=None):
        """
        Burst-analysis data-page relating to a BAT_GRB_Pos VOEvent.

        Args:
            trigger_event (voevent): VOEvent (Swift_BAT_GRB_Pos) packet
            hash_cache_path (str): See :class:`.FeedBase`.
        """

        self.trigger_id = BatGrb(trigger_event)._pull_swift_bat_id()[1]
        self.trigger_event = trigger_event
        self.url = self.url.format(trigger_id=self.trigger_id)
        self.name = "SwiftTrigger_{}_analysis".format(self.trigger_id)
        super(SwiftFeed, self).__init__(hash_cache_path)

    def parse_content_to_event_data_list(self):
        data_snippets = []
        tree = lxml.html.fromstring(self.content)
        pre0 = tree.xpath('//pre')[0]
        pre0_lines = pre0.text.split('\n')
        for idx, _ in enumerate(pre0_lines):
            if 'Duration' in pre0_lines[idx]:
                logger.debug("Extracting duration info")
                duration_info = self._extract_duration_info(pre0_lines, idx)
                if duration_info:
                    data_snippets.append(
                        {SwiftFeedKeys.duration: duration_info})
        return data_snippets

    def _extract_duration_info(self, all_lines, start_idx):
        d_lines = all_lines[start_idx:start_idx + 9]
        d_lines = [l.strip() for l in d_lines]
        #     print lines[1].startswith('T90')
        info = {}
        for l in d_lines:
            if "WARNING: battblocks failed." in l:
                info[SwiftFeedKeys.battblocks_failed] = True
                return info
        info[SwiftFeedKeys.battblocks_failed] = False
        # Check the input data is as expected, be conservative here:
        if not d_lines[1].startswith('T90'):
            return None
        if not d_lines[4].startswith('T50'):
            return None
        t90_tokens = d_lines[1].split()
        info[SwiftFeedKeys.t90] = float(t90_tokens[1])
        info[SwiftFeedKeys.t90_err] = float(t90_tokens[3])
        # info['t90_measured_from'] = float(lines[2].split()[2])
        # info['t90_measured_to'] = float(lines[3].split()[1])

        t50_tokens = d_lines[4].split()
        info[SwiftFeedKeys.t50] = float(t50_tokens[1])
        info[SwiftFeedKeys.t50_err] = float(t50_tokens[3])
        # info['t50_measured_from'] = float(lines[5].split()[2])
        # info['t50_measured_to'] = float(lines[6].split()[1])
        return info

    def event_data_to_event_id(self, event_data):
        """
        Derive a feed-specific identifier for a given event.

        Args:
            event_data: Feed specific datastructure, typically just a dictionary.
        """
        data_snippet_type = list(event_data.keys())[0]
        return "{}_{}".format(self.trigger_id, data_snippet_type)

    def get_ivorn_prefixes_for_duplicate(self, feed_id):
        """
        Determines what a possible duplicate ivorn might be prefixed by.

        For SWIFT - events are already uniquely identified by their trigger ID.
        So we expect only exact IVORN matches:
        """
        return [self.feed_id_to_ivorn(feed_id),]

    def generate_voevent(self, feed_id):
        event_data = self.event_id_data_map[feed_id]
        stream_id = self.feed_id_to_stream_id(feed_id)
        v = create_skeleton_4pisky_voevent(substream=self.substream,
                                           stream_id=stream_id,
                                           role=vp.definitions.roles.observation,
                                           date=datetime.datetime.utcnow()
                                           )

        vp.add_how(v, references=[vp.Reference(uri=self.url)])
        v.How.Description = "Parsed from Swift burst-analysis listings by 4PiSky-Bot."

        # Simply copy the WhereWhen from the trigger event:
        v.WhereWhen = self.trigger_event.WhereWhen
        v.What.append(vp.Param("TrigID", value=self.trigger_id, ucd="meta.id"))
        vp.add_citations(v, event_ivorns=[
            vp.EventIvorn(ivorn=self.trigger_event.attrib['ivorn'],
                        cite_type=vp.definitions.cite_types.followup)
        ])
        if SwiftFeedKeys.duration in feed_id:
            duration_data = event_data[SwiftFeedKeys.duration]
            battblocks_failed = duration_data['battblocks_failed']
            battblocks_param = vp.Param(
                'battblocks_failed', value=battblocks_failed,
                ucd='meta.code.error')
            battblocks_param.Description = """\
            If 'battblocks_failed' is 'True', the source-page contains the 'battblocks failed' warning.
            This means the duration analysis is bad, usually because the source
            is not actually a GRB burst.
            """
            duration_params = []
            if not battblocks_failed:
                duration_params.extend([
                                           vp.Param(k,
                                                    value=duration_data.get(k),
                                                    unit='s',
                                                    ucd='time.duration')
                                           for k in
                                           (
                                               SwiftFeedKeys.t90,
                                               SwiftFeedKeys.t50)
                                           ])
                duration_params.extend(
                    [
                        vp.Param(k, value=duration_data.get(k),
                                 unit='s',
                                 ucd='meta.code.error;time.duration')
                        for k in (SwiftFeedKeys.t90_err, SwiftFeedKeys.t50_err)

                        ])
            duration_params.append(battblocks_param)
            v.What.append(vp.Group(params=duration_params,
                                   name=SwiftFeedKeys.duration))

        return v


def create_swift_feeds(hash_cache_path, look_back_ndays):
    """
    Create swift feeds for recent BAT_GRB alerts
    """
    s = session_registry()
    logger.debug("Checking database {} for recent Swift BAT GRB alerts".format(
        s.bind.engine.url.database
    ))
    now = datetime.datetime.utcnow()
    q = s.query(models.Voevent).filter(
        models.Voevent.stream == "nasa.gsfc.gcn/SWIFT",
        models.Voevent.ivorn.like('%{}%'.format("BAT_GRB")),
        models.Voevent.role == 'observation'
    )
    if look_back_ndays is not None:
        threshold_tstamp = now - datetime.timedelta(days=look_back_ndays)
        q = q.filter(models.Voevent.author_datetime > threshold_tstamp)

    feeds = []
    for entry in q:
        v = vp.loads(entry.xml.encode())
        alert = BatGrb(v)
        if not (alert.startracker_lost()
                or alert.tgt_in_flight_cat()
                or alert.tgt_in_ground_cat()):
            feeds.append(SwiftFeed(v, hash_cache_path=hash_cache_path))
        logger.debug("Created feed for packet {}".format(v.attrib['ivorn']))
    return feeds

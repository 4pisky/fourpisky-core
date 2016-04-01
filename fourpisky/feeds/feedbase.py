from __future__ import absolute_import
import urllib2
import requests
import hashlib
from contextlib import closing
import shelve
from voeventdb.server.database import session_registry
import voeventdb.server.database.convenience as dbconvenience
from fourpisky.feeds.requiredatts import RequiredAttributesMetaclass
from fourpisky.utils import sanitise_string_for_stream_id
import logging
logger = logging.getLogger(__name__)


class FeedBase(object):
    __metaclass__ = RequiredAttributesMetaclass
    _required_attributes = [
        'name',
        'url',
        'substream',
        'hash_byte_range', #Set to False to fetch all content
    ]

    def __init__(self, hash_cache_path):
        self.hash_cache_path = hash_cache_path
        self._content = None
        self._old_hash = None
        self._new_hash = None
        self._event_id_data_map = None

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

    def save_new_hash(self):
        with closing(shelve.open(self.hash_cache_path)) as hash_cache:
            hash_cache[self.url] = self.new_hash
        logger.debug("Inserted hash for feed {} in cache {}; md5={}".format(
                self.url, self.hash_cache_path, self.new_hash
        ))

    @property
    def event_id_data_map(self):
        """
        Dict mapping feed-specific event-id to relevant data.
        """
        if self._event_id_data_map is None:
            row_list = self.parse_content_to_event_data_list()
            self._event_id_data_map = {self.event_data_to_event_id(rd): rd for rd in row_list}
        return self._event_id_data_map

    def event_data_to_event_id(self, event_data):
        """
        Generate a feed-specific id from an event-datastructure
        """
        raise NotImplementedError

    def parse_content_to_event_data_list(self):
        """
        Use self.content to extract list of event-datastructures.
        """
        raise NotImplementedError


    def feed_id_to_stream_id(self, feed_id):
        # Currently just a wrapper, bound to class for convenience.
        # Could be customised in future though.
        return sanitise_string_for_stream_id(feed_id)

    def feed_id_to_ivorn(self, feed_id):
        safe_id = self.feed_id_to_stream_id(feed_id)
        return self.stream_ivorn_prefix + safe_id

    def generate_voevent(self, feed_id):
        raise NotImplementedError

    def get_ivorn_prefix_for_matched_timestamp(self, ivorn):
        """
        Determines what a possible duplicate ivorn might be prefixed by.

        Used for duplicate checking - assumes timestamp unchanging even if the
        event gets renamed. We extract the timestamp portion from the given
        IVORN, then re-append it to the stream-ivorn prefix.
        """
        stream_id = ivorn[len(self.stream_ivorn_prefix):]
        return self.stream_ivorn_prefix + stream_id.split('_', 1)[0]

    def determine_new_ids_from_localdb(self):
        """
        Uses a local voeventdb to check for previously broadcast events.

        We assume that the currently configured stream_ivorn_prefix is the same
        as any previously broadcast voevents in the database. Therefore we
        can do an efficient lookup by calculating the relevant IVORN-prefix
        for each event in the `event_id_data_map` of this class.
        """
        s = session_registry()
        new_ids = []
        logger.debug("Checking database {} for duplicates from feed {}".format(
            s.bind.engine.url.database, self.name
        ))
        for feed_id in self.event_id_data_map:
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
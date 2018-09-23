from __future__ import absolute_import

from contextlib import closing
import hashlib
import logging
import requests
import shelve
import urllib.request, urllib.error, urllib.parse

from fourpisky.requiredatts import RequiredAttributesMetaclass
from fourpisky.utils import sanitise_string_for_stream_id
from voeventdb.server.database import session_registry
import voeventdb.server.database.convenience as dbconvenience

logger = logging.getLogger(__name__)


class FeedBase(object):
    """
    A base class to facilitate scraping a table of data from a single URL.

    This can take the form of an HTML embedded table, CSV, whatever - the
    parsing functionality should be implemented by derived classes.
    """
    __metaclass__ = RequiredAttributesMetaclass
    _required_attributes = [
        'name',
        'url',
        'substream',
        'hash_byte_range',  # Set to False to fetch all content
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
            r.raise_for_status()
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
                req = urllib.request.Request(self.url)
                req.headers['Range'] = 'bytes={}-{}'.format(
                    *self.hash_byte_range)
                data = urllib.request.urlopen(req).read()
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
            event_data_dicts = self.parse_content_to_event_data_list()
            self._event_id_data_map = {}
            for ed in event_data_dicts:
                try:
                    self._event_id_data_map[
                        self.event_data_to_event_id(ed)] = ed
                except:
                    logger.exception(
                        "Error trying to extract event ID from data dict: {}".format(
                            ed))
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
        """
        Default implementation simply removes non-allowed characters.
        """
        return sanitise_string_for_stream_id(feed_id)

    def feed_id_to_ivorn(self, feed_id):
        return self.stream_ivorn_prefix + self.feed_id_to_stream_id(feed_id)

    def get_ivorn_prefixes_for_duplicate(self, feed_id):
        """
        Determines what a possible duplicate ivorn might be prefixed by
        """
        raise NotImplementedError

    def determine_new_entries(self):
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
        logger.debug("Checking {} feed entries".format(
            len(self.event_id_data_map)
        ))
        for feed_id in self.event_id_data_map:
            ivo = self.feed_id_to_ivorn(feed_id)
            if not dbconvenience.ivorn_present(s, ivo):
                duplicate_prefixes = self.get_ivorn_prefixes_for_duplicate(
                    feed_id)
                duplicate_present = False
                for prefix in duplicate_prefixes:
                    if dbconvenience.ivorn_prefix_present(s, prefix):
                        duplicate_present = True
                        logger.warning(
                            "Possible duplicate prefix detected: '{}', "
                            "will not insert '{}'".format(prefix, ivo))
                if not duplicate_present:
                    new_ids.append(feed_id)
        return new_ids

    def generate_voevent(self, feed_id):
        raise NotImplementedError

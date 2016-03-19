# Defines a plugin for the Comet broker.
# If top-level directory 'comet_plugin' is added to $PYTHONPATH then comet
# will detect this module at import-time.

import os
from zope.interface import implementer
from twisted.plugin import IPlugin
from comet.icomet import IHandler, IHasOptions
import comet.log as log

from fourpisky.taskqueue.tasks import (
    process_voevent_celerytask,
    ingest_voevent_celerytask
)

@implementer(IPlugin, IHandler)
class CeleryQueuer(object):
    name = "celery-queue"

    # When the handler is called, it is passed an instance of
    # comet.utility.xml.xml_document.
    def __call__(self, event):
        """
        Add an event to the celery processing queue
        """
        log.debug("Passing to celery: %s" % (event.attrib['ivorn'],))
        process_voevent_celerytask.delay(event.text)
        ingest_voevent_celerytask.delay(event.text)


# This instance of the handler is what actually constitutes our plugin.
queue_event = CeleryQueuer()

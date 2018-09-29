import logging
logger = logging.getLogger(__name__)

## Check for a private contacts module:
try:
    from . import contacts
except ImportError as e:
    logger.info("No contacts module found! "
                "Will import template for unit-testing purposes.")
    import fourpisky.contacts_template as contacts


notification_email_prefix = "[4 Pi Sky] "
ivorn_base = 'voevent.4pisky.org'

## Drop in a mock amicomms for testing purposes:
try:
    import amicomms as amicomms_safe
except ImportError as e:
    logger.info("amicomms module not installed!"
                "Will import mock for unit-testing purposes.")
    from . import amicomms_mock as amicomms_safe


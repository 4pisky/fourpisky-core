import logging
logger = logging.getLogger(__name__)

## Check for a private contacts module:
try:
    import fourpisky.contacts
except ImportError as e:
    logger.info("No contacts module found! "
                "Will import template for unit-testing purposes.")
    import fourpisky.contacts_template as contacts


notification_email_prefix = "[4 Pi Sky] "
ivorn_base = 'voevent.4pisky.org'
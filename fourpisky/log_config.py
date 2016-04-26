import logging

from fourpisky.reports import EmailHandler
from fourpisky.local import contacts

full_date_fmt = "%y-%m-%d (%a) %H:%M:%S"
short_date_fmt = "%H:%M:%S"

verbose_formatter = logging.Formatter(
        '%(asctime)s:%(name)s:%(levelname)s:%(message)s',
        # '%(asctime)s:%(levelname)s:%(message)s',
        full_date_fmt)

def setup_logfile_handlers(logger, logfile_pathstem, filters=None,
                           log_chunk_bytesize = 5e6):
    info_logfile_path = logfile_pathstem + ".log"
    debug_logfile_path = logfile_pathstem + ".debug.log"

    info_filehandler = logging.handlers.RotatingFileHandler(
        info_logfile_path, maxBytes=log_chunk_bytesize, backupCount=10)
    info_filehandler.setLevel(logging.INFO)

    debug_filehandler = logging.handlers.RotatingFileHandler(
        debug_logfile_path, maxBytes=log_chunk_bytesize, backupCount=10)
    debug_filehandler.setLevel(logging.DEBUG)

    for fh in (info_filehandler, debug_filehandler):
        fh.setFormatter(verbose_formatter)
        if filters:
            for f in filters:
                fh.addFilter(f)
        logger.addHandler(fh)

def setup_email_errorhandler(logger):
    email_handler = EmailHandler(
        recipients=[p.email for p in contacts.error_contacts])
    email_handler.setFormatter(verbose_formatter)
    email_handler.setLevel(logging.ERROR)
    logger.addHandler(email_handler)


def setup_logging(logfile_pathstem=None, email_errors=True):
    """
    Set up default logging setup
    """

    std_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s',
                                      short_date_fmt)
    stdout_logger = logging.StreamHandler()
    stdout_logger.setFormatter(std_formatter)
    stdout_logger.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.addHandler(stdout_logger)
    if logfile_pathstem:
        setup_logfile_handlers(logger,logfile_pathstem)
    if email_errors:
        setup_email_errorhandler(logger)
    return logger

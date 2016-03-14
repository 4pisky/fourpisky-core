#!/usr/bin/env python
import logging
import click
import fourpisky.voevent
import voeventparse
from fourpisky.taskqueue.tasks import process_voevent_celerytask
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@click.command()
def cli():
    click.echo("Attempting celery task")
    test_packet = fourpisky.voevent.create_4pisky_test_trigger_voevent()
    voevent_bytestring=voeventparse.dumps(test_packet)
    process_voevent_celerytask.delay(voevent_bytestring)
    click.echo("Task fired")
    return 0

if __name__ == '__main__':
    cli()
import tempfile
import pytest
import os
from voeventdb.server.tests.fixtures.connection import (
    empty_db_connection,
    fixture_db_session,
    simple_populated_db
)


@pytest.yield_fixture()
def uncreated_temporary_file_path():
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()
    os.unlink(tf.name)
    yield tf.name
    if os.path.exists(tf.name):
        os.unlink(tf.name)

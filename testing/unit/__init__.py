import os
import tempfile

import pytest
from carpooling.commands import init_db_command

from carpooling import create_app

@pytest.fixture
def client():
    app = create_app()
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            init_db_command()
        yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])
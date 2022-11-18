import os
import tempfile

import pytest
from carpooling.commands import init_db_command_for_code

from carpooling import create_app, db
from carpooling.models import User, Event, Passenger, CarpoolSolution, GeneratedCarpool, GeneratedCarpoolPart
import quickpiggy

import logging

logger = logging.getLogger(__name__)

def init_test_db(uri: str, app):
    # making sure that the db is the piggy and not the real one
    assert uri == app.config['SQLALCHEMY_DATABASE_URI']

    # running through the alembic migrations
    db.create_all()
    init_db_command_for_code(is_testing=True)
    logger.info('successfully ran init_db_command_for_code')

@pytest.fixture
def client():
    # piggy = quickpiggy.Piggy(volatile=True)
    #piggy.params['dbname'] = 'testing_db'
    
    app = create_app(extra_config_settings={'TESTING': True})
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE']
    with app.test_client() as client:
        with app.app_context():
            init_test_db(app.config['DATABASE'], app)
        yield client

    os.unlink(app.config['DATABASE'])

@pytest.fixture
def app():
    # piggy = quickpiggy.Pigly(volatile=True)
    # piggy.params['dbname'] = 'testing_db'
    app = create_app(extra_config_settings={'TESTING': True})
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE']
    with app.app_context():
        init_test_db(app.config['DATABASE'], app)
    yield app

    os.unlink(app.config['DATABASE'])
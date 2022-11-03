from carpooling import create_app
import carpooling.celeryapp as celeryapp
from flask import current_app
import logging
import time

logger = logging.getLogger(__name__)

from .routes import register_task_blueprints

celery = celeryapp.celery
if celery is None:
    app = create_app()
    celery = celeryapp.create_celery_app(app)
    celeryapp.celery = celery
    logger.debug('registered task blueprints in celery tasks module')
else:
    logger.debug('celery already exists')


@celery.task()
def test_task():
    print('test task started')
    time.sleep(5)
    print('test task finished')
    return 'test task'

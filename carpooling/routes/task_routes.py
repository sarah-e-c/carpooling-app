from carpooling import tasks
from flask import Blueprint
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

task_blueprint = Blueprint('task', __name__, template_folder='templates')

logger.debug('making the task routes')
@task_blueprint.route('/test-task')
def test_task():
    logger.debug('test task recieved from routse')
    tasks.test_task.delay()
    return 'test task'



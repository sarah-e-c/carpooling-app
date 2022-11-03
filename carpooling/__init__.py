import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session
import os
from flask_login import LoginManager
from flask_mail import Mail
import logging
from celery import Celery
from carpooling import celeryapp
database_url = os.environ.get('DATABASE_URL')

if database_url is None:
    database_url = 'sqlite:///site.db'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)



#database_url = 'sqlite:///test.db' # for testing

celery = Celery(__name__)
mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login_page'




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



celery = Celery(__name__)

def create_app():
    app = Flask(__name__)

    # Load common settings
    app.config.from_object('carpooling.settings')
    # Load environment specific settings
    app.config.from_object('carpooling.local_settings')
    # Load extra settings from extra_config_settings parameter
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    celery = celeryapp.create_celery_app(app)

    celeryapp.celery = celery
    logger.info('celery app updated')
    celery.conf.update(app.config)
    from .routes import register_blueprints
    register_blueprints(app)
    from .routes import register_task_blueprints
    register_task_blueprints(app)
    return app
    



import carpooling.routes
from carpooling.models import User
import carpooling.tasks



import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session
import os
from flask_login import LoginManager
from flask_mail import Mail
import logging
from celery import Celery
from carpooling import celeryapp
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_migrate import Migrate

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)



#database_url = 'sqlite:///test.db' # for testing

celery = Celery(__name__)
mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login_page'
migrate = Migrate()


# global tasks_
# tasks_ = []

@login_manager.user_loader # yes this is awful, im sorry i couldn't gt the takss to work any other way :(
def load_user(user_id):
    global user_
    try:
        if user_ is None:
            from carpooling.models import User as user_
            logger.info('imported User')
    except NameError as e:
        from carpooling.models import User as user_ 
        logger.info('imported User with nameerror')

    return user_.query.get(int(user_id))



celery = Celery(__name__)

def create_app(extra_config_settings=None):
    app = Flask(__name__)

    # Load common settings
    app.config.from_object('carpooling.settings')
    # Load environment specific settings
    app.config.from_object('carpooling.local_settings')
    # Load extra settings from extra_config_settings parameter
    if extra_config_settings is not None:
        app.config.update(extra_config_settings)


    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    celery = celeryapp.create_celery_app(app)

    celeryapp.celery = celery
    logger.info('celery app updated')
    celery.conf.update(app.config)
    global tasks_
    from carpooling import tasks as tasks_ # this is really weird im sorry
    logger.debug(tasks_)
    migrate.init_app(app, db)
    from .routes import register_blueprints
    register_blueprints(app)
    from .routes import register_task_blueprints
    register_task_blueprints(app)
    # adding commands
    from .commands import register_commands
    register_commands(app)

    return app
    
app = create_app()



#import carpooling.routes
#from carpooling.models import User



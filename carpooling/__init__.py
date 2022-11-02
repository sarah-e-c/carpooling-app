import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session
import os
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session
from flask import Blueprint
import logging
from celery import Celery
from carpooling import celeryapp
database_url = os.environ.get('DATABASE_URL')
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
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.__setattr__('admin_access_flag', False)
    app.__setattr__('driver_access_flag', False)

    app.config['MAIL_SERVER'] = 'smtp.zoho.com' 
    app.config['MAIL_PORT'] = 465 
    app.config['MAIL_USE_SSL'] = True 
    app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
    app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
    app.config['CELERY_CONFIG'] = {
        'broker_url': 'redis://localhost:6379',
        'result_backend':'redis://localhost:6379'
    }
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    celery = celeryapp.create_celery_app(app)
    celeryapp.celery = celery
    celery.conf.update(app.config)
    from .routes import register_blueprints
    register_blueprints(app)


    return app


import carpooling.routes
from carpooling.models import User
import carpooling.tasks



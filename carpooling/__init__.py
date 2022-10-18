import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session
import os
from flask_login import LoginManager
from flask_mail import Mail
from flask_session import Session
from flask import Blueprint


app = Flask(__name__)
#database_url = os.environ.get('DATABASE_URL')

database_url = 'sqlite:///test.db'
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


mail = Mail(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login_page'
login_manager.init_app(app)


import carpooling.routes
from carpooling.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




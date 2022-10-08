import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os
from flask_login import LoginManager

app = Flask(__name__)

#database_url = os.environ.get('DATABASE_URL')
database_url = 'sqlite:///test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.__setattr__('admin_access_flag', False)
app.__setattr__('driver_access_flag', False)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

import carpooling.routes
from carpooling.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


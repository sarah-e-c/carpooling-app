import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

app = Flask(__name__)

#database_url = os.environ.get('DATABASE_URL')
database_url = 'sqlite:///test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.__setattr__('admin_access_flag', False)
app.__setattr__('driver_access_flag', False)

db = SQLAlchemy(app)

import carpooling.routes


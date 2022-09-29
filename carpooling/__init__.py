import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

import carpooling.routes


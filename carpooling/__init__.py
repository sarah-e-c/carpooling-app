import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///driver_data.db'

db = SQLAlchemy(app)

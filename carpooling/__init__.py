import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://pbhbpribpxamgo:d7eb88d69d1f16ac2f1da19071c8e4c898c2fb48619d94be047f590003c4a847@ec2-18-209-78-11.compute-1.amazonaws.com:5432/d6dl85srl08ilp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
import carpooling.routes


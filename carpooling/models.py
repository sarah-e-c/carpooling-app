from carpooling import db
from sqlalchemy.sql import func

class Driver(db.Model):
    __tablename__ = 'drivers'
    index = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    num_seats = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    student_or_parent = db.Column(db.String, nullable=False)
    num_years_with_license = db.Column(db.String)
    car_type_1 = db.Column(db.String, nullable=False)
    car_color_1 = db.Column(db.String, nullable=False)
    car_type_2 = db.Column(db.String)
    car_color_2 = db.Column(db.String)
    emergency_contact_number = db.Column(db.String, nullable=False)
    emergency_contact_relation = db.Column(db.String, nullable=False)
    # carpools = db.relationship('Carpool', backref='driver_index', lazy=True)
    extra_information = db.Column(db.String)

    def __repr__(self):
        return f'Driver: {self.first_name.capitalize()} {self.last_name.capitalize()}'

class AuthKey(db.Model):
    __tablename__ = 'auth_keys'
    index = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f'AuthKey created at: {self.time_created}'

# class Carpool(db.Model):
#     __tablename__ = 'carpools'
#     index = db.Column(db.Integer, primary_key=True)
#     driver_index = db.Column(db.Integer, db.ForeignKey('drivers.index'), nullable=False)
#     driver = db.relationship('Driver', backref=db.backref('carpools', lazy=True))
#     num_passengers = db.Column(db.Integer, nullable=False)
#     event = db.Column()
#     destination = db.Column(db.String, nullable=False)
#     extra_information = db.Column(db.String)

#     def __repr__(self):
#         return f'Carpool: {self.driver.first_name.capitalize()} {self.driver.last_name.capitalize()}'

# class CarpoolEvent(db.Model):
#     __tablename__ = 'carpool_events'
#     event_index = db.Column(db.Integer, primary_key=True)
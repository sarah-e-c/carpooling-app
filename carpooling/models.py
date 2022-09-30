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

<<<<<<< HEAD
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
=======
class Carpool(db.Model):
    """
    A carpool is a collection of a driver and a list of passengers. It is within an event.
    """
    __tablename__ = 'carpools'
    index = db.Column(db.Integer, primary_key=True)
    driver_index = db.Column(db.Integer, db.ForeignKey('drivers.index'), nullable=False)
    driver = db.relationship('Driver', backref=db.backref('carpools', lazy=True))
    num_passengers = db.Column(db.Integer, nullable=False)
    event_index = db.Column(db.String, foreignkey='events.index', nullable=False)
    event = db.relationship('Event', backref=db.backref('carpools', lazy=True))
    destination = db.Column(db.String, nullable=False)
    extra_information = db.Column(db.String)
    region = db.relationship('Region', backref=db.backref('carpools'))
    region_name = db.Column(db.String, nullable=False, foreignkey='regions.name')

    def __repr__(self):
        return f'Carpool: {self.driver.first_name.capitalize()} {self.driver.last_name.capitalize()}'

class Region(db.Model):
    """
    A region is a group of students that are close to each other.
    """
    __tablename__ = 'regions'
    name = db.Column(db.String, primary_key=True)
    dropoff_location = db.Column(db.String, nullable=False)
    carpools = db.relationship('Carpool', backref=db.backref('region'))
    passengers = db.relationship('Passenger', backref=db.backref('region'))


class Event(db.Model):
    """
    Event model. Events can have multiple carpools for each region.
    """
    __tablename__ = 'carpool_events'
    event_index = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    event_start_time = db.Column(db.DateTime, nullable=False)
    event_end_time = db.Column(db.DateTime, nullable=False)
    event_location = db.Column(db.String, nullable=False, default='Maggie Walker Governor\'s School')
    carpools = db.relationship('Carpool', backref='event', lazy=True)

    def __repr__(self):
        return f'Event: {self.event_name}'


class Passenger(db.Model):
    """
    Passenger model. More limited than Driver model. Passengers will not require sign in but might be offered for convenience.
    """
    __tablename__ = 'passengers'
    index = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    email_address = db.Column(db.String, nullable=False)
    emergency_contact_number = db.Column(db.String, nullable=False)
    emergency_contact_relation = db.Column(db.String, nullable=False)
    extra_information = db.Column(db.String)
    region_name = db.Column(db.String, nullable=False, foreignkey='regions.name')
    region = db.relationship('Region', backref=db.backref('passengers'))


    def __repr__(self):
        return f'Passenger: {self.first_name.capitalize()} {self.last_name.capitalize()}'
>>>>>>> de34915 (database models)

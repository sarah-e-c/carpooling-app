from carpooling import db
from sqlalchemy.sql import func
from flask_login import UserMixin



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
    
    @staticmethod
    def get_by_name(full_name):
        first_name, last_name = full_name.split(' ')
        return Driver.query.filter_by(first_name=first_name, last_name=last_name).first()
        


class AuthKey(db.Model):
    __tablename__ = 'auth_keys'
    index = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, default=func.now())

    def __repr__(self):
        return f'AuthKey created at: {self.time_created}'

class Carpool(db.Model):
    """
    A carpool is a collection of a driver and a list of passengers. It is within an event.
    """
    __tablename__ = 'carpools'
    index = db.Column(db.Integer, primary_key=True)
    driver_index = db.Column(db.Integer, db.ForeignKey('drivers.index'), nullable=True)
    driver = db.relationship('Driver', backref=db.backref('carpools', lazy=True))
    num_passengers = db.Column(db.Integer, nullable=False)
    event_index = db.Column(db.String, db.ForeignKey('events.index'), nullable=False)
    event = db.relationship('Event', backref=db.backref('carpools', lazy=True))
    destination = db.Column(db.String, nullable=False)
    extra_information = db.Column(db.String)
    region = db.relationship('Region', backref=db.backref('carpools'), lazy=True)
    region_name = db.Column(db.String, db.ForeignKey('regions.name'), nullable=False)
    passengers = db.relationship('Passenger', secondary='passenger_carpool_links', overlaps='carpools')


    def has_driver(self):
        return self.driver is not None

    def get_passenger_number_name(self, number: int) -> str:
        """
        Returns the name of the passenger in that position
        """
        try:
            if self.passengers[number] is None:
                return 'Open'
        except IndexError:
            return 'Open'

        return self.passengers[number].first_name.capitalize() + ' ' + self.passengers[number].last_name[0].capitalize() + '.'

    def get_dropoff_location(self):
        """
        Use this method to get the dropoff location of the carpool if specified
        or the default drop off of the region.
        """

        if self.destination is not None:
            return self.destination
        else:
            return self.region.dropoff_location
    
    def __repr__(self):
        try:
            return f'Carpool with driver: {self.driver.first_name.capitalize()} {self.driver.last_name.capitalize()}'
        except:
            return 'empty carpool'

    



class Event(db.Model):
    """
    Event model. Events can have multiple carpools for each region.
    """
    __tablename__ = 'events'
    index = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    event_start_time = db.Column(db.DateTime, nullable=False)
    event_end_time = db.Column(db.DateTime, nullable=False)
    event_location = db.Column(db.String, nullable=False, default='Maggie Walker Governor\'s School')
    event_description = db.Column(db.String, nullable=True)
    #carpools = db.relationship('Carpool', backref='event', lazy=True)

    def get_description(self):
        if self.event_description is None:
            return ''
        return self.event_description

    def get_date(self):
        return self.event_date.strftime('%A, %B %d, %Y')
    
    def get_times(self):
        return f'{self.event_start_time.strftime("%I:%M %p")} - {self.event_end_time.strftime("%I:%M %p")}'


    def __repr__(self):
        return f'Event: {self.event_name}'

class Region(db.Model):
    """
    A region is a group of students that are close to each other.
    """
    __tablename__ = 'regions'
    name = db.Column(db.String, primary_key=True)
    dropoff_location = db.Column(db.String, nullable=False)
    color = db.Column(db.String, nullable=False, default='#fff')
    #carpools = db.relationship('Carpool', backref=db.backref('region'))
    #passengers = db.relationship('Passenger', backref=db.backref('region'))

    def get_carpools_in_event(self, event: Event):
        return [carpool for carpool in self.carpools if carpool.event == event]
        

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
    emergency_contact_number = db.Column(db.String, nullable=True)
    emergency_contact_relation = db.Column(db.String, nullable=True)
    extra_information = db.Column(db.String)
    region_name = db.Column(db.String, db.ForeignKey('regions.name'), nullable=True)
    region = db.relationship('Region', backref=db.backref('passengers'))
    carpools = db.relationship('Carpool', secondary='passenger_carpool_links', overlaps='passengers')


    def __repr__(self):
        return f'Passenger: {self.first_name.capitalize()} {self.last_name.capitalize()}'

class PassengerCarpoolLink(db.Model):
    """
    Table to link passengers to carpools.
    """
    __tablename__ = 'passenger_carpool_links'
    index = db.Column(db.Integer, primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('passengers.index'))
    carpool_id = db.Column(db.Integer, db.ForeignKey('carpools.index'))

    def __repr__(self):
        return f'PassengerCarpoolLink: {self.passenger_id} {self.carpool_id}'


class StudentAndRegion(db.Model):
    """
    Table to link students to regions. Is really only going to be used for the initial phase.
    """
    __tablename__ = 'student_and_region'
    index = db.Column(db.Integer, primary_key=True)
    student_first_name = db.Column(db.String, nullable=False)
    student_last_name = db.Column(db.String, nullable=False)
    region_name = db.Column(db.String, db.ForeignKey('regions.name'))
    region = db.relationship('Region', backref=db.backref('students'))

    def __repr__(self):
        return f'StudentAndRegion: {self.student_id} {self.region_name}'


class User(UserMixin, db.Model):
    """
    Class for a user. Users have some special accesses.
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String, nullable=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.index'), nullable=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('passengers.index'), nullable=True)
    driver_profile = db.relationship('Driver', backref=db.backref('user'), lazy=True)
    passenger_profile = db.relationship('Passenger', backref=db.backref('user'), lazy=True)
    is_admin = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'User: {self.first_name.capitalize()} {self.last_name.capitalize()}'

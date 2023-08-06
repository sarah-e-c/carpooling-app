from carpooling import db
from flask import current_app, session
from sqlalchemy.sql import func
from flask_login import UserMixin
from itsdangerous import URLSafeSerializer
import logging
import datetime
from sqlalchemy import event, Sequence

logger = logging.getLogger(__name__)


class EventCheckIn(db.Model):
    __tablename__ = 'event_sign_ups'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.index'))
    event = db.relationship('Event', backref='events.event_sign_ups', uselist=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='users.event_sign_ups', uselist=False)
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    re_check_in_time = db.Column(db.DateTime, nullable=True)

    def get_start_time(self):
        return self.check_in_time.strftime('%I:%M %p')

    def get_end_time(self):
        return self.check_out_time.strftime('%I:%M %p')
    
class Carpool(db.Model):
    """
    A carpool is a collection of a driver and a list of passengers. It is within an event.
    """
    __tablename__ = 'carpools'
    index = db.Column(db.Integer, primary_key=True)
    driver_index = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    driver = db.relationship('User', back_populates='driver_carpools')
    num_passengers = db.Column(db.SmallInteger, nullable=False)
    event_index = db.Column(db.Integer, db.ForeignKey('events.index'), nullable=False)
    event = db.relationship('Event', backref=db.backref('carpools', lazy=True))
    destination = db.Column(db.String, nullable=False)
    extra_information = db.Column(db.String(200), nullable=True)
    passengers = db.relationship('User', back_populates='passenger_carpools', secondary='passenger_carpool_links')

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

        return self.passengers[number].first_name.capitalize() + ' ' + self.passengers[number].last_name[
            0].capitalize() + '.'

    def __repr__(self):
        try:
            return f'Carpool with driver: {self.driver.first_name.capitalize()} {self.driver.last_name.capitalize()}'
        except Exception as e:
            return 'empty carpool'


class Event(db.Model):
    """
    Event model. Events can have multiple carpools for each region.
    """

    __tablename__ = 'events'
    index = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String, nullable=False, default='Maggie Walker Governor\'s School')
    description = db.Column(db.String, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('events', lazy=True))
    passengers_needing_ride = db.relationship('User', secondary='passenger_event_links', lazy=True)
    destination = db.relationship('Destination', backref=db.backref('events', lazy=True))
    destination_id = db.Column(db.Integer, db.ForeignKey('destinations.id'), nullable=True)
    event_carpool_signups = db.relationship('EventCarpoolSignup', back_populates='event', lazy=True)
    needs_matching_build_to = db.Column(db.Boolean, default=False)
    needs_matching_build_from = db.Column(db.Boolean, default=False)
    matching_build_type = db.Column(db.Integer, default=0,)  # 0=none, 1=to, 2=from, 3=to and from
    # carpools = db.relationship('Carpool', backref='event', lazy=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    organization = db.relationship("Organization", back_populates="events", foreign_keys=[organization_id])

    def get_description(self):
        if self.description is None:
            return ''
        return self.description

    def get_date(self):
        return self.date.strftime('%A, %B %d, %Y')

    def get_times(self):
        return f'{self.start_time.strftime("%I:%M %p")} - {self.end_time.strftime("%I:%M %p")}'

    def get_checkins(self):
        return EventCheckIn.query.filter_by(event_id=self.index).all()

    def get_carpool_type_string(self):
        match self.matching_build_type:
            case 0:
                return 'not'
            case 1:
                return 'to'
            case 2:
                return 'from'
            case 3:
                return 'to and from'
        return 'null value'
    def __repr__(self):
        return f'Event: {self.name}'
    

class User(UserMixin, db.Model):
    """
    Class for a user. Users have some special accesses.
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    student_or_parent = db.Column(db.String, nullable=True)
    pool_points = db.Column(db.Float, default=0.0, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    emergency_contact_number = db.Column(db.String, nullable=False)
    emergency_contact_relation = db.Column(db.String, nullable=False)
    extra_information = db.Column(db.String(200), nullable=True)
    num_seats = db.Column(db.Integer, nullable=True)
    num_years_with_license = db.Column(db.String, nullable=True)
    car_type_1 = db.Column(db.String, nullable=True)
    car_color_1 = db.Column(db.String, nullable=True)
    car_type_2 = db.Column(db.String, nullable=True)
    car_color_2 = db.Column(db.String, nullable=True)
    driver_carpools = db.relationship('Carpool', back_populates='driver', lazy=True)
    passenger_carpools = db.relationship('Carpool', secondary='passenger_carpool_links')
    passenger_generated_carpool_parts = db.relationship('GeneratedCarpoolPart', back_populates='passengers',
                                                        secondary='generated_carpool_part_passenger_links', lazy=True)
    driver_generated_carpool_parts = db.relationship('GeneratedCarpoolPart', back_populates='driver', lazy=True)
    passenger_generated_carpools = db.relationship('GeneratedCarpool', back_populates='passengers',
                                                   secondary='generated_carpool_passenger_links', lazy=True)
    driver_generated_carpools = db.relationship('GeneratedCarpool', back_populates='driver', lazy=True)
    event_carpool_signups = db.relationship('EventCarpoolSignup', back_populates='user')
    addresses = db.relationship('Address', secondary='address_user_links', back_populates='users')
    organizations=db.relationship("Organization", secondary="organization_user_links", back_populates="users")
    organization_user_links = db.relationship("OrganizationUserLink", back_populates="user", lazy=True)

    def is_admin(self) -> int:
        """
        Returns the admin level for the current organization section.
        """
        organization = int(session['organization'])
        admin_level = OrganizationUserLink.query.filter_by(user_id=self.id, organization_id=organization).first().admin_level
        return admin_level
    
    def set_admin_level(self, level: int):
        """
        Sets the admin level
        """
        organization_user_link = OrganizationUserLink.query.filter_by(user_id=self.id, organization_id=int(session['organization'])).first()
        organization_user_link.admin_level = level
        db.session.commit()


    def is_signed_up_for_event(self, event_index):
        """
        Checks if the user is signed up for an event
        """
        logger.debug(f'Checking if user {self.id} is signed up for event {event_index}')
        for signup in self.event_carpool_signups:
            if signup.event_id == event_index:
                logger.debug(f'User {self.id} is signed up for event {event_index}')
                return True
        logger.debug(f'User {self.id} is not signed up for event {event_index}')
        return False

    def get_reset_password_token(self, expires_in=600):
        """
        Method to get the reset password token from the user
        """
        s = URLSafeSerializer(current_app.config['SECRET_KEY'])
        return s.dumps([self.id, self.password])

    def verify_reset_password_token(self, token):
        """
        Method to verify the reset password token
        """
        try:
            s = URLSafeSerializer(current_app.config['SECRET_KEY'])
            data = s.loads(token)
            if data[0] != self.id:
                return False
            return True

        except Exception as e:
            logger.critical(f'Error verifying reset password token: {e}')
            return False

    def __repr__(self):
        return f'User: {self.first_name.capitalize()} {self.last_name.capitalize()}'

    def is_checked_in_for_event(self, event: Event):
        """
        Returns true if the passenger is signed up for the event.
        """
        if EventCheckIn.query.filter_by(user_id=self.id, event_id=event.index).first() is not None:
            if EventCheckIn.query.filter_by(user_id=self.id, event_id=event.index).one().check_out_time is None:
                return True
            if EventCheckIn.query.filter_by(user_id=self.id, event_id=event.index).one().re_check_in_time is not None:
                return True
            else:
                return False  # there is a check in, but it is checked out
        else:  # if there is not a check in for the event
            return False

    def is_done_with_event(self, event: Event):
        """
        Returns true if the passenger is done with the event.
        """
        return True if EventCheckIn.query.filter_by(user_id=self.id,
                                                    event_id=event.index).first().check_out_time is not None else False

    def get_event_check_in(self, event: Event):
        """
        Returns the check in for the event.
        """
        return EventCheckIn.query.filter_by(user_id=self.id, event_id=event.index).first()

    # inherited passenger methods
    def get_address(self, address_number=1):
        """
        Gives a pretty version of the address
        """
        try:
            if not self.addresses[address_number - 1].address_line_2:
                return f'{self.addresses[address_number - 1].address_line_1}, {self.addresses[address_number - 1].city}, {self.addresses[address_number -1].state} {self.addresses[address_number - 1].zip_code}'
            else:
                return f'{self.addresses[address_number - 1].address_line_1}, {self.addresses[address_number - 1].address_line_2}, {self.addresses[address_number - 1].city}, {self.addresses[address_number-1].state} {self.addresses[address_number - 1].zip_code}'
        except IndexError:
            return 'No address'

    def get_address_line_1(self, address_number=1):
        """
        Gives the first line of the address
        """
        try:
            return self.addresses[address_number - 1].address_line_1
        except IndexError:
            return None

    def get_address_line_2(self, address_number=1):
        """
        Gives the second line of the address
        """
        try:
            return self.addresses[address_number - 1].address_line_2
        except IndexError:
            return None

    def get_zip_code(self, address_number=1):
        """
        Gives the zip code of the address
        """
        try:
            return self.addresses[address_number - 1].zip_code
        except IndexError:
            return None

    def get_city(self, address_number=1):
        """
        Gives the city of the address
        """
        try:
            return self.addresses[address_number - 1].city
        except IndexError:
            return None

    def get_state(self, address_number=1):
        """
        Gives the state of the address
        """
        try:
            return self.addresses[address_number - 1].state
        except IndexError:
            return None

    def get_address_code(self, address_number=1):
        """
        Gives the address code of the address
        """
        try:
            return self.addresses[address_number - 1].address_code
        except IndexError:
            return None

    def get_latitude(self, address_number=1):
        """
        Gives the latitude of the address
        """
        try:
            return self.addresses[address_number - 1].latitude
        except IndexError:
            return None

    def get_longitude(self, address_number=1):
        """
        Gives the longitude of the address
        """
        try:
            return self.addresses[address_number - 1].longitude
        except IndexError:
            return None

    def is_driver(self):
        """
        Returns true if the user is a driver
        """
        if self.num_seats is not None:
            return True
        return False

    def is_confirmed_for_carpool(self, carpool_id):
        for response in self.generated_carpool_responses:
            if response.generated_carpool_id == carpool_id:
                logger.debug(f'{self} is has response {response.is_accepted} to the carpool {carpool_id}')
                return response.is_accepted
        logger.debug(f'{self} has not responded to carpool {carpool_id}')
        return False

    @staticmethod
    def get_by_name(full_name):
        first_name, last_name = full_name.split(' ')
        return User.query.filter_by(first_name=first_name, last_name=last_name).first()


class DistanceMatrix(db.Model):
    """
    Table to store the distance matrix
    """
    __tablename__ = 'distance_matrix'
    index = db.Column(db.Integer, primary_key=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)  # represents one location
    origin = db.relationship('Address', backref='address.origin_distances', foreign_keys=[origin_id])
    destination_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)  # represents another location
    destination = db.relationship('Address', backref='address.destination_distances', foreign_keys=[destination_id])
    seconds = db.Column(db.Float, nullable=False)  # time in minutes
    kilos = db.Column(db.Float, nullable=False)  # distance in kilometers

    def __repr__(self):
        return f'DistanceMatrix: {self.origin} {self.destination}'


class Address(db.Model):
    """
    Table to store addresses and geocodes
    """
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    address_line_1 = db.Column(db.String, nullable=False)
    address_line_2 = db.Column(db.String, nullable=True)
    city = db.Column(db.String, nullable=False)
    state = db.Column(db.String, nullable=False)
    zip_code = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    code = db.Column(db.String, nullable=True,
                     unique=True)  # change these once all of the addresses are loaded in properly
    destination = db.relationship('Destination', back_populates='address')
    users = db.relationship('User', back_populates='addresses', secondary='address_user_links')

    def __repr__(self):
        return f'Address: {self.address_line_1}'
    
    def get_address(self):
        if not self.address_line_2:
            return f'{self.address_line_1}, {self.city}, {self.state} {self.zip_code}'
        else: 
            return f'{self.address_line_1}, {self.address_line_2}, {self.city}, {self.state} {self.zip_code}'


class Destination(db.Model):
    """
    Class to represent a location where an event can be held.
    """
    __tablename__ = 'destinations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    address = db.relationship('Address', back_populates='destination', foreign_keys=[address_id], uselist=False)
    organization=db.relationship("Organization", back_populates="destinations")
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    def __repr__(self):
        return f'Destination: {self.name}'


class GeneratedCarpool(db.Model):
    """
    Table with the generated carpools
    """
    __tablename__ = 'generated_carpools'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.index'), nullable=False)
    carpool_solution_id = db.Column(db.Integer, db.ForeignKey('carpool_solutions.id'), nullable=False)
    from_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    to_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    from_address = db.relationship('Address', backref=db.backref('from_generated_carpools'),
                                   foreign_keys=[from_address_id])
    to_address = db.relationship('Address', backref=db.backref('to_generated_carpools'), foreign_keys=[to_address_id])
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver = db.relationship('User', back_populates='driver_generated_carpools', foreign_keys=[driver_id])
    passengers = db.relationship('User', back_populates='passenger_generated_carpools',
                                 secondary='generated_carpool_passenger_links', lazy='subquery')
    carpool_solution = db.relationship('CarpoolSolution', backref=db.backref('generated_carpools'),
                                       foreign_keys=[carpool_solution_id])
    event = db.relationship('Event', backref=db.backref('generated_carpools'), foreign_keys=[event_id], uselist=False)
    is_accepted = db.Column(db.Boolean, nullable=False, default=False)
    from_time = db.Column(db.DateTime, nullable=False)
    to_time = db.Column(db.DateTime, nullable=False)

    def get_carpool_pickup_time_for_user(self, user: User):
        """
        Returns the time the user should be picked up for this carpool in datetime format.
        """
        if user == self.driver or self.carpool_solution.type == 'from':
            return self.from_time
        else:  # carpool is 'to' and user is a passenger
            try:
                user_address_id = user.addresses[0].id
                return \
                    [part.from_time for part in self.generated_carpool_parts if
                     part.from_address_id == user_address_id][0]
            except IndexError:
                try:
                    user_address_id = user.addresses[1].id
                    return [part.from_time for part in self.generated_carpool_parts if
                            part.from_address_id == user_address_id][0]
                finally:
                    logger.error('Could not find a carpool part for user {} in carpool {}'.format(user, self))
                    return None

    def get_carpool_dropoff_time_for_user(self, user: User):
        if user == self.driver or self.carpool_solution.type == 'to':
            logger.debug(f'Carpool End Time: {self.to_time}')
            return self.to_time
        else:  # carpool is 'to' and user is a passenger
            try:
                user_address_id = user.addresses[0].id
                return \
                    [part.to_time for part in self.generated_carpool_parts if part.to_address_id == user_address_id][
                        0]
            except IndexError:
                try:
                    user_address_id = user.addresses[1].id
                    return \
                        [part.to_time for part in self.generated_carpool_parts if
                         part.to_address_id == user_address_id][
                            0]
                finally:
                    logger.error('Could not find a carpool part for user {} in carpool {}'.format(user, self))
                    return None

    def get_carpool_points(self, user: User):
        """
        Returns the points for this carpool
        """
        return int(eval(self.carpool_solution.pool_points)[user.id])
class Organization(db.Model):
    """
    Table to store organizations.
    """
    __tablename__ = "organizations"
    id = db.Column(db.Integer, primary_key=True)
    access_key = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100), nullable=False)
    icon_location = db.Column(db.String(100), default="carpooling/static/icons/default_icon.jpg") # icons for organizations to use
    users = db.relationship("User", secondary="organization_user_links", back_populates="organizations", lazy="subquery")
    destinations = db.relationship("Destination", back_populates="organization", lazy="subquery")
    events = db.relationship("Event", back_populates="organization", lazy=True)
    organization_user_links = db.relationship("OrganizationUserLink", back_populates="organization", lazy=True) # this allows for direct access to admin information

class OrganizationUserLink(db.Model):
    """
    Table to store the relationships between users and their organziations.
    This table allows for users to be a part of organization.
    """
    __tablename__ = "organization_user_links"
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    admin_level = db.Column(db.SmallInteger, default=0)
    user = db.relationship("User", back_populates="organization_user_links", foreign_keys=[user_id])
    organization = db.relationship("Organization", back_populates="organization_user_links", foreign_keys=[organization_id])
    



class GeneratedCarpoolResponse(db.Model):
    """
    Table to store the responses to generated carpools. Whenever one is created, always check to see if they all are.
    """
    __tablename__ = 'generated_carpool_response'  # TODO rename table
    id = db.Column(db.Integer, primary_key=True)
    generated_carpool_id = db.Column(db.Integer, db.ForeignKey('generated_carpools.id'), nullable=False)
    generated_carpool = db.relationship('GeneratedCarpool', backref=db.backref('generated_carpool_responses'),
                                        foreign_keys=[generated_carpool_id])
    is_accepted = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('generated_carpool_responses'), foreign_keys=[user_id])


class GeneratedCarpoolPart(db.Model):
    """
    One part of a generated carpool. Ex. Driving from one house to another
    """
    __tablename__ = 'generated_carpool_parts'
    id = db.Column(db.Integer, primary_key=True)
    idx = db.Column(db.Integer, nullable=False)
    generated_carpool_id = db.Column(db.Integer, db.ForeignKey('generated_carpools.id'), nullable=False)
    generated_carpool = db.relationship('GeneratedCarpool', backref=db.backref('generated_carpool_parts'),
                                        foreign_keys=[generated_carpool_id])
    from_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    from_address = db.relationship('Address', backref=db.backref('from_generated_carpool_parts'),
                                   foreign_keys=[from_address_id])
    from_time = db.Column(db.DateTime, nullable=False)
    to_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    to_address = db.relationship('Address', backref=db.backref('to_generated_carpool_parts'),
                                 foreign_keys=[to_address_id])
    to_time = db.Column(db.DateTime, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver = db.relationship('User', back_populates='driver_generated_carpool_parts', foreign_keys=[driver_id])
    passengers = db.relationship('User', back_populates='passenger_generated_carpool_parts',
                                 secondary='generated_carpool_part_passenger_links', lazy='subquery')


class CarpoolSolution(db.Model):
    """
    Table with possible solutions
    """
    __tablename__ = 'carpool_solutions'
    id = db.Column(db.Integer, primary_key=True)
    utility_value = db.Column(db.Float, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.index'), nullable=False)
    event = db.relationship('Event', backref=db.backref('carpool_solutions'), foreign_keys=[event_id])
    length_objective_value = db.Column(db.Float, nullable=False, default=0)
    needed_passengers_served_objective_value = db.Column(db.Float, nullable=False, default=0)
    favorable_time_objective_value = db.Column(db.Float, nullable=False, default=0)
    favorable_route_objective_value = db.Column(db.Float, nullable=False, default=0)
    is_best = db.Column(db.Boolean, nullable=True)
    type = db.Column(db.String(4), nullable=False)  # to or from or both
    pool_points = db.Column(db.String(1000),nullable=False) # JSON string of pool points earned per user. Format: {user_id: pool_points}
    corresponding_solution_id = db.Column(db.Integer, db.ForeignKey('carpool_solutions.id'), nullable=True)
    corresponding_solution = db.relationship('CarpoolSolution', remote_side=[corresponding_solution_id])



class EventCarpoolSignup(db.Model):
    """
    Table with the signups for carpools and for events. Was the old CSV, but now is in a database.
    """
    __tablename__ = 'event_carpool_signups'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.index'), nullable=False)
    user = db.relationship('User', back_populates='event_carpool_signups', foreign_keys=[user_id])
    event = db.relationship('Event', back_populates='event_carpool_signups', foreign_keys=[event_id])
    willing_to_drive = db.Column(db.Boolean, nullable=False)
    needs_ride = db.Column(db.Boolean, nullable=False)


class GeneratedCarpoolPassengerLink(db.Model):
    """
    Table with the links between generated carpools and passengers
    """
    __tablename__ = 'generated_carpool_passenger_links'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generated_carpool_id = db.Column(db.Integer, db.ForeignKey('generated_carpools.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # person who is a passenger
    # generated_carpool = db.relationship('GeneratedCarpool', foreign_keys=[generated_carpool_id])
    # passenger = db.relationship('Passenger', foreign_keys=[passenger_id])


class GeneratedCarpoolPartPassengerLink(db.Model):
    """
    Table with the links between generated carpools and passengers
    """
    __tablename__ = 'generated_carpool_part_passenger_links'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generated_carpool_id = db.Column(db.Integer, db.ForeignKey('generated_carpool_parts.id'), nullable=False,
                                     primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, primary_key=True)
    # generated_carpool_part = db.relationship('GeneratedCarpoolPart', back_populates='generated_carpool_parts', foreign_keys=[generated_carpool_id])
    # passenger = db.relationship('Passenger', foreign_keys=[passenger_id])


class PassengerCarpoolLink(db.Model):
    """
    Table to link passengers to carpools.
    """
    __tablename__ = 'passenger_carpool_links'
    index = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    carpool_id = db.Column(db.Integer, db.ForeignKey('carpools.index'))

    def __repr__(self):
        return f'UserCarpoolLink: {self.user_id} {self.carpool_id}'


class PassengerEventLink(db.Model):
    """
    Table to link passengers that need carpools to events
    """
    __tablename__ = 'passenger_event_links'
    index = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.index'))

    def __repr__(self):
        return f'UserEventLink: {self.user_id} {self.event_id}'



class AddressUserLink(db.Model):
    """
    Table to link addresses to users
    """
    __tablename__ = 'address_user_links'
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    def __repr__(self):
        return f'AddressUserLink: {self.address_id} {self.user_id}'


class UserUserLink(db.Model):
    """
    Table that links users to users. Used to represent the relationships between users.
    """
    __tablename__ = 'user_user_links'
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    description = db.Column(db.String(100), nullable=False)
    good = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'UserUserLink: {self.user1_id} {self.user2_id}'
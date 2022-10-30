from carpooling import db
from carpooling import app, mail
from carpooling.models import Driver, AuthKey, Event, Passenger, Region, Carpool, StudentAndRegion, User
import logging
import time
from carpooling.utils import PersonAlreadyExistsException, admin_required, driver_required, InvalidNumberOfSeatsException, super_admin_required
from flask import render_template, request, redirect, url_for, make_response, flash, session, send_file
import secrets
import os
import datetime
from sqlalchemy import func
import hashlib
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from carpooling.utils import requires_auth_key
from itsdangerous import URLSafeSerializer
from flask_mail import Message

DEFAULT_NUMBER_OF_CARPOOLS = 4

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# logFormatter = logging.Formatter(fmt=' %(name)s :: %(levelname)-8s :: %(message)s')
# logging.RootLogger(logging.DEBUG)


# h2 = logging.SMTPHandler(mailhost=app.config['MAIL_SERVER'],
#                             fromaddr=app.config['MAIL_USERNAME'],
#                             toaddrs=app.config['MAIL_USERNAME'],
#                             subject='Carpooling Error',
#                             credentials=(app.config['MAIL_USERNAME'],app.config['MAIL_PASSWORD']),
#                             secure=None)
# h2.setLevel(logging.CRITICAL)
# h2.setFormatter(logFormatter)
# logging.getLogger().addHandler(h2)




@app.route('/driver/<lastname>/<firstname>')
@requires_auth_key
def driver_page(lastname, firstname):
    """
    Driver page for passengers and other drivers to see
    last_name: last name of the driver
    first_name: first name of the driver
    """
    logger.info('driver page')
    try:
        driver = Driver.query.filter_by(last_name=lastname, first_name=firstname).one()
    except:
        logger.info('no driver was found')
        return 'No driver was found.'
    
    logger.info('driver found')
    driver_info = {'lastname': driver.last_name.capitalize(),
                    'firstname':  driver.first_name.capitalize(),
                    'car_type_1': driver.car_type_1,
                    'car_color_1': driver.car_color_1,
                    'car_type_2': driver.car_type_2,
                    'car_color_2': driver.car_color_2,
                    'number_seats': driver.num_seats,
                    'phone_number': driver.phone_number,
                    'email': driver.email_address,
                    'student_or_parent': driver.student_or_parent,
                    'emergencycontact': driver.emergency_contact_number,
                    'emergencycontactrelation': driver.emergency_contact_relation,
                    'licenseyears': driver.num_years_with_license,
                    'phone_number_string': f'tel:{driver.phone_number}',
                    'email_string': f'mailto:{driver.email_address}',
                    'extra_information': driver.extra_information}

                
    return render_template('driver_template.html', **driver_info, user=current_user)


@app.route('/verify_auth_key/<next>/<kwargs_keys>/<kwargs_string>', methods=['GET', 'POST'])
def verify_auth_key_page(next, kwargs_keys, kwargs_string):
    """
    Page that users are redirected to if they need to get an auth key
    next: the next page to go to
    kwargs_keys: the keys of the kwargs, encoded by the decorator
    kwargs_string: the values of the kwargs, encoded by the decorator

    This page is called by the decorator requires_auth_key, and is pretty much exclusivelt used for that purpose.

    """
    if request.method == 'GET':
        # this is how the things are encoded
        # kwargs_keys = '--'.join(kwargs)
        # kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
        return render_template('get_driver_access_template.html', next=next, kwargs_keys=kwargs_keys, kwargs_string=kwargs_string, user=current_user)
    if request.method == 'POST':
        try:
            if request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key or request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key:
                if current_user.is_authenticated:
                    current_user.team_auth_key = AuthKey.query.order_by(AuthKey.index.desc()).first().key
                    db.session.commit()
                    logger.info('Driver access granted to user {}'.format(current_user))
                
                # re-encoding the keys
                kwargs = {}
                for kwarg_key, kwarg in zip(kwargs_keys.split('--'), kwargs_string.split('--')):
                    kwargs[kwarg_key] = kwarg
                
                # setting the response
                response = make_response(redirect(url_for(next, **kwargs)))
                s = URLSafeSerializer(app.secret_key)
                logger.info('setting cookie')
                response.set_cookie('driver-access', s.dumps(['access granted']), max_age=datetime.timedelta(seconds=60))
                return response
            else:
                flash('Invalid Auth Key') # theres no flash support but like whatever
                return render_template('get_driver_access_template.html', next=next, kwargs_keys=kwargs_keys, kwargs_string=kwargs_string, user=current_user, message='Invalid Key')
        except IndexError as e:
            # basically the same thing, but there's only one key... yes there is probably a better way to do this but like 
            if request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key:
                if current_user.is_authenticated:
                    current_user.team_auth_key = AuthKey.query.order_by(AuthKey.index.desc()).first().key
                    db.session.commit()
                    logger.info('Driver access granted to user {}'.format(current_user))
                
                logger.info('Access granted')
                # re-encoding the keys
                kwargs = {}
                for kwarg_key, kwarg in zip(kwargs_keys.split('--'), kwargs_string.split('--')):
                    kwargs[kwarg_key] = kwarg
                
                response = make_response(redirect(url_for(next, **kwargs)))
                s = URLSafeSerializer(app.secret_key)
                logger.info('setting cookie')
                response.set_cookie('driver-access', s.dumps(['access granted']), max_age=datetime.timedelta(seconds=60))
                return response

            else:
                # invalid key
                flash('Invalid Auth Key')
                logger.info('access denied')
                return render_template('get_driver_access_template.html', next=next, kwargs_keys=kwargs_keys, kwargs_string=kwargs_string, user=current_user, message='Invalid Key')


@app.route('/')
@app.route('/home')
def home_page(logout=False):
    """
    Home page. Also index page.
    """
    # if the user requested a logout, then they get logged out here
    logout = request.args.get('logout')
    if logout:
        logout_user()
        logger.info(f'User {current_user} logged out')
    
    # finding the information needed for the dashboard... technically doesn't need to be done if not authenticated, but its not too bad
    events = Event.query.all()
    events = [event for event in events if event.event_date >= datetime.datetime.now() - datetime.timedelta(hours=36)]
    if current_user.is_authenticated:
        if current_user.driver_profile is not None:
            driver_carpools = [carpool for carpool in Carpool.query.filter_by(driver_index=current_user.driver_profile.index).all() if carpool.event.event_date >= datetime.datetime.now() - datetime.timedelta(hours=36)]
        else:
            driver_carpools = []
        passenger_carpools = [carpool for carpool in current_user.passenger_profile.carpools if carpool.event.event_date >= datetime.datetime.now() - datetime.timedelta(hours=36)]
    else:
        driver_carpools = []
        passenger_carpools = []
    return render_template('index.html', user=current_user, driver_carpools=driver_carpools, passenger_carpools=passenger_carpools, events=events)


@app.route('/register', methods=['GET','POST'])
def register_new_driver_page():
    """
    Page to register a new driver to the database.
    """
    
    # updating the auth keys... this should probably be done in a utils method or something
    if (datetime.datetime.now() - AuthKey.query.order_by(AuthKey.index.desc()).first().date_created).days > 29:
        new_auth_key = AuthKey(auth_key=secrets.token_hex(16))
        db.session.add(new_auth_key)
        db.session.commit()
    
    # get template
    if request.method == 'GET':
        message = request.args.get('message')
        if message is None:
            message = 'Register to be a driver for team 422!'
        regions = Region.query.all()
        return render_template('driver_signup_template.html', message=message, user=current_user, regions=regions)
    
    if request.method == 'POST':

        # getting the data from the form, i don't care if aaron says this is bad practice
        driver_info = {
            'first_name':request.form['firstname'].lower(),
            'last_name': request.form['lastname'].lower(),
            'student_or_parent': request.form['studentorparent'],
            'num_years_with_license': request.form['licenseyears'],
            'phone_number': request.form['phonenumber'],
            'email_address': request.form['email'],
            'car_type_1': request.form['cartype1'],
            'car_color_1': request.form['carcolor1'],
            'car_type_2': request.form['cartype2'],
            'car_color_2': request.form['carcolor2'],
            'emergency_contact_number': request.form['emergencycontact'],
            'emergency_contact_relation': request.form['emergencycontactrelation'],
            'extra_information': request.form['note'],
            'num_seats': request.form['numberofseats'],
            'region_name': request.form['region'],
            'address_line_1': request.form['addressline1'],
            'address_line_2': request.form['addressline2'],
            'city': request.form['city'],
            'zip_code': request.form['zipcode'],
        }
        try:
            # the person already exists in the database as a driver
            if (Driver.query.filter_by(first_name = driver_info['first_name'], last_name = driver_info['last_name']).count() > 0) or (User.query.filter_by(first_name = driver_info['first_name'], last_name = driver_info['last_name']).count() > 0):
                raise PersonAlreadyExistsException
            
            new_driver = Driver(**driver_info)


            try:
                _ = int(request.form['numberofseats'])
            except ValueError:
                raise InvalidNumberOfSeatsException

            # deleting the unneeded rows so it can also be converted to passenger
            del driver_info['student_or_parent']
            del driver_info['num_years_with_license']
            del driver_info['num_seats']
            del driver_info['car_type_1']
            del driver_info['car_color_1']
            del driver_info['car_type_2']
            del driver_info['car_color_2']

            # making the corresponding passenger and committing to the database
            new_passenger = Passenger(**driver_info)
            db.session.add(new_passenger)
            db.session.add(new_driver)
            db.session.commit()
            logger.info(f'New driver added to database: {new_driver}')\
            
            # creating the corresponding user
            user_info = {
                'first_name': new_driver.first_name,
                'last_name': new_driver.last_name,
                'password': generate_password_hash(request.form['password'], method='sha256'),
                'driver_id': new_driver.index,
                'passenger_id': new_passenger.index
            }

            logger.debug(f'New User info: {user_info}')

            new_user = User(**user_info)
            db.session.add(new_user)
            db.session.commit()
            logger.info('New user registered.')

        # exceptions and their meanings
        except PersonAlreadyExistsException as e:
            logger.info(e)
            return redirect(url_for("register_new_driver_page", message='A person with that name already exists.'))
        except InvalidNumberOfSeatsException as e:
            logger.info(e)
            return redirect(url_for("register_new_driver_page", message='The number of seats must be an integer.'))
        except Exception as e:
            logger.info(e)
            return redirect(url_for("register_new_driver_page", message='Something went wrong. Make sure that all inputs are valid.'))
        
        return render_template('error_template.html', main_message='Success!', sub_message='Thank you for helping team 422!', user=current_user)

@app.route('/valid-auth-keys')
@admin_required
def valid_auth_keys_page():
    """
    This page is only accessible if the admin has logged in.
    Page for admins to see all valid auth keys and when they were created.
    """
    # querying the auth keys and ordering them
    auth_keys = AuthKey.query.order_by(AuthKey.date_created).all()

    # i love naming things
    return_list = [item.key for item in auth_keys]
    return_list_2 = [item.date_created for item in auth_keys]
    return render_template('valid_auth_keys_template.html', return_list=zip(return_list, return_list_2), user=current_user)

@app.route('/events')
def events_page():
    """
    Page to display all upcoming events. Probably should make an events log in the futre
    """
    current_events = Event.query.filter(Event.event_date >= datetime.datetime.now() - datetime.timedelta(hours=36)).all()
    return render_template('events_template.html', events=current_events, user=current_user)

@app.route('/event/<event_index>')
def event_page(event_index):
    """
    Event page
    event_index: the index of the event that is wanted.
    """
    try:
        event = Event.query.get(event_index)
    except: # the event doesn't exist
        redirect(url_for('events_page'))
   
    return render_template('event_template.html', event=event, regions=Region.query.all(), user=current_user)

@app.route('/create-event', methods=['GET', 'POST'])
@login_required
@requires_auth_key
def create_event_page():
    """
    Create event page. Used for verified users to create events.
    """

    if request.method == 'GET':
        message = request.args.get('message')
        if message is None: 
            message = 'Create an Event'
        return render_template('create_event_template.html', message=message, user=current_user)

    if request.method == 'POST':
        # getting the event info from the form
        event_info = {
            'event_name': request.form['eventname'],
            'event_date': datetime.datetime.strptime(request.form['eventdate'], '%Y-%m-%d'),
            'event_start_time': datetime.datetime.strptime(request.form['eventstarttime'], '%H:%M'),
            'event_end_time': datetime.datetime.strptime(request.form['eventendtime'], '%H:%M'),
            'event_location': request.form['eventlocation'],
            'event_description': request.form['eventdescription'],
            'user_id': current_user.id
        }

        try:
            new_event = Event(**event_info)
            db.session.add(new_event)
            for region in Region.query.all(): # i love for loops
                # for each region, create carpools
                for _ in range(DEFAULT_NUMBER_OF_CARPOOLS):
                    carpool = Carpool(event_index=new_event.index, region_name=region.name, num_passengers=0, destination=region.dropoff_location)
                    db.session.add(carpool)
            
            db.session.commit()
            logger.info(f'New event added to database: {new_event} with carpools: {new_event.carpools}')

        except Exception as e: # i don't really know how this happens but its good to have
            logger.debug(e)
            return redirect(url_for("create_event_page", message='Something went wrong. Make sure that all inputs are valid.'))
        
        return redirect(url_for('events_page'))
    else: 
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)


@app.route('/driver-signup/<carpool_index>', methods=['GET', 'POST'])
@driver_required
@requires_auth_key
def driver_carpool_signup_page(carpool_index):
    """
    Page that drivers go to when they are signing up for a carpool. Still needs a check for sign in
    :carpool_index index of the carpool to be signed up for
    """
    if request.method == 'GET':
        if current_user.is_authenticated:
            carpool = Carpool.query.get(carpool_index)
            if carpool.driver is not None:
                return redirect(url_for('event_page', event_index=carpool.event_index))
            carpool.driver = current_user.driver_profile
            carpool.num_passengers = current_user.driver_profile.num_seats
            carpool.driver_index = current_user.driver_profile.index
            db.session.commit()
            logger.info(f'{current_user} signed up for carpool {carpool}')
            # messaging the passengers in region that requested a carpool
            for passenger in [passenger for passenger in carpool.event.passengers_needing_ride if passenger.region_name == carpool.region_name]:
                if passenger.region_name == carpool.region_name:
                    try:
                        message = Message(
                            subject='Carpool Request Fulfilled',
                            recipients=[passenger.email_address],
                            sender = ('Mech Tech Dragons Carpooling', 'Carpooling Dragon'),
                            body=f'Hi {passenger.first_name},\n\nYour request for a carpool has been fulfilled! Check the events page to sign up.\n\nThanks,\nTeam 422'
                        )
                        mail.send(message)
                        logger.info(f'Message sent to {passenger.email_address}')
                    except Exception as e:
                        logger.debug(e)
                        logger.info(f'Failed to send message to {passenger.email_address}, probably due to an invalid email address')
            # removing the passengers needing a ride in the region
            for passenger in [passenger for passenger in carpool.event.passengers_needing_ride if passenger.region_name == carpool.region_name]:
                carpool.event.passengers_needing_ride.remove(passenger)
            db.session.commit()

            return render_template('error_template.html', main_message='Success!', sub_message='You have signed up to drive! Thank you for helping the team!', user=current_user) 

        carpool = Carpool.query.get(carpool_index)
        return render_template('driver_carpool_signup_template.html', carpool=carpool, message='Sign up for a carpool!', user=current_user)
    if request.method == 'POST':
        try:
            carpool = Carpool.query.get(carpool_index)
        except Exception as e:
            logger.critical(e)
            logger.warning('This should never happen : (')
        driver = Driver.query.filter_by(first_name=request.form['firstname'].lower(), last_name=request.form['lastname'].lower()).first()
        logger.debug(driver)
        if driver is None:
            return render_template('driver_carpool_signup_template.html', carpool=carpool, message='That driver does not exist. Please try again.', user=current_user)
        else:
            carpool.driver = driver
            try:
                carpool.num_passengers = int(request.form['numberofpassengers'])
            except Exception as e:
                logger.debug(e)

            db.session.commit()
            logger.info(f'Driver {driver} signed up for carpool {carpool}')
            return render_template('error_template.html', main_message='Success!', sub_message='You have successfully signed up for a carpool!', user=current_user)


@app.route('/passenger-signup/<carpool_index>', methods=['GET', 'POST'])
def passenger_carpool_signup_page(carpool_index):
    """
    Page for the passenger to sign up for a carpool
    """

    if request.method == 'GET':
        if current_user.is_authenticated:
            carpool = Carpool.query.get(carpool_index)
            if carpool.driver is None:
                return redirect(url_for('event_page', event_index=carpool.event_index))
            carpool.passengers.append(current_user.passenger_profile)
            db.session.commit()
            logger.info(f'{current_user} signed up for carpool {carpool}')
            return render_template('error_template.html', main_message='Success!', sub_message='You have signed up for a carpool!', user=current_user)
        else:
            carpool = Carpool.query.get(carpool_index)
            return render_template('passenger_carpool_signup_template.html', carpool=carpool, message='Sign up for a carpool!', user=current_user)


    if request.method == 'POST':
        carpool = Carpool.query.get(carpool_index)
        passenger = Passenger.query.filter_by(first_name=request.form['firstname'].lower(), last_name=request.form['lastname'].lower()).first()
        logger.debug(passenger)
        if passenger is None:
            try:
                new_passenger = Passenger(
                    first_name = request.form['firstname'].lower(),
                    last_name = request.form['lastname'].lower(),
                    email_address = request.form['email'].lower(),
                    phone_number = request.form['phonenumber'],
                    emergency_contact_number = request.form['emergencycontact'],
                    emergency_contact_relation = request.form['emergencycontactrelation'],
                    extra_information = request.form['note']
                )

                carpool.passengers.append(new_passenger)
                db.session.add(new_passenger)
                db.session.commit()
                logger.info('new temp passenger created')

                try:
                    # send email to driver about new passenger
                    message = Message(
                        subject='New Passenger Signup',
                        recipients=[carpool.driver.email_address],
                        body=f'New passenger {new_passenger} signed up for carpool {carpool}!',
                        sender=('Carpooling Manager', 'mechtechscarpooling@zohomail.com'),
                    )
                    mail.send(message)
                    logger.info('email sent to driver')

                except Exception as e:
                    logger.warning(e)
                    logger.warning('email not sent to driver')
                

                return render_template('error_template.html', main_message='Success!', sub_message='A new passenger was registered, and you have successfully signed up for a carpool!', user=current_user)


            except Exception as e:
                logger.debug(e)
                return render_template('passenger_carpool_signup_template.html', carpool=carpool, message='There was an error registering a new passenger. Try again.', user=current_user)

        else:
            passenger.extra_information = request.form['note']
            carpool.passengers.append(passenger)
            db.session.add(passenger)
            db.session.commit()
            logger.info('existing passenger added to carpool without sign in')

            # send email to driver about new passenger
            message = Message(
                subject='New Passenger Signup',
                recipients=[carpool.driver.email_address],
                body=f'New passenger {new_passenger} signed up for carpool {carpool}!',
                sender=('Carpooling Manager', 'mechtechscarpooling@zohomail.com'),
            )
            mail.send(message)
            logger.info('email sent to driver')
            return render_template('error_template.html', main_message='Success!', sub_message='The passenger already existed in the database. Please register to use all features.', user=current_user)


    carpool  = Carpool.query.get(carpool_index)
    return str(carpool.passengers[0].carpools) + str(len(carpool.passengers))

@app.route('/register-passenger', methods=['GET', 'POST'])
def register_passenger_page():
    """
    Page for passengers to register
    """
    if request.method == 'GET':
        regions = Region.query.all()
        return render_template('passenger_sign_up_template.html', regions=regions, user=current_user)

    if request.method == 'POST':
        if request.form['password'] != request.form['confirmpassword']: # the form password is unequal to this password
            regions = Region.query.all()
            return render_template('passenger_sign_up_template.html', message='Passwords do not match. Please try again.', regions=regions, user=current_user)
        
        # doesn't really work
        region_name = request.form.get('region')
        


        if User.query.filter_by(first_name=request.form['firstname'], last_name=request.form['lastname']).first() is not None:
            regions = Region.query.all()
            return render_template('passenger_sign_up_template.html', message='A user with that name already exists. Please try again.', regions=regions, user=current_user)
        
        if Driver.query.filter_by(first_name=request.form['firstname'], last_name=request.form['lastname']).first() is not None:
            regions = Region.query.all()
            return render_template('passenger_sign_up_template.html', message='A user with that name already exists. Please try again.', regions=regions, user=current_user)

        try:
            passenger_information = {
                'first_name': request.form['firstname'].lower(),
                'last_name': request.form['lastname'].lower(),
                'email_address': request.form['email'],
                'phone_number': request.form['phonenumber'],
                'region_name': region_name,
                'extra_information': request.form['note'],
                'emergency_contact_number': request.form['emergencycontact'],
                'emergency_contact_relation': request.form['emergencycontactrelation'],
                'address_line_1': request.form['addressline1'],
                'address_line_2': request.form['addressline2'],
                'city': request.form['city'],
                'zip_code': request.form['zipcode'],
            }

            passenger = Passenger(**passenger_information)
            db.session.add(passenger)
            db.session.commit()
            logger.info('A new passenger has been added to the database!')

            user_information = {
                'first_name': request.form['firstname'].lower(),
                'last_name': request.form['lastname'].lower(),
                'password': generate_password_hash(request.form['password']),
                'passenger_id': passenger.index,
                'driver_id': None,
            }
        
            user = User(**user_information)
            db.session.add(user)
            db.session.commit()


        except Exception as urMom:
            regions = Region.query.all()
            logger.debug(urMom)
            return render_template('passenger_sign_up_template.html', message='There was an error', user=current_user, regions=regions)
        
    
        return render_template('error_template.html', main_message='Success!', sub_message='You have signed up!', user=current_user)


        
        



@app.route('/legacy-driver-to-current', methods=['GET', 'POST'])
def legacy_driver_to_login_page():
    """
    Page that allows for the conversion of a legacy driver to creating an account
    """

    if request.method == 'GET': 
        logger.debug('get request')
        return render_template('legacy_driver_to_login_template.html', message='Enter your information', user=current_user)
    if request.method == 'POST':
        if request.form['password'] != request.form['confirmpassword']:
            return render_template('legacy_driver_to_login_template.html', message='Passwords do not match. Please try again.', user=current_user)
        try:
            existing_driver = Driver.query.filter_by(first_name=request.form['firstname'].lower(), last_name=request.form['lastname'].lower()).first()
            if existing_driver is None:
                return render_template('legacy_driver_to_login_template.html', message='The driver does not exist. Please try again or register.', user=current_user)
            new_passenger = Passenger(
                first_name = request.form['firstname'].lower(),
                last_name = request.form['lastname'].lower(),
                email_address = existing_driver.email_address,
                phone_number = existing_driver.phone_number,
                emergency_contact_number = existing_driver.emergency_contact_number,
                emergency_contact_relation = existing_driver.emergency_contact_relation,
                extra_information = existing_driver.extra_information
            )
            db.session.add(new_passenger)
            db.session.commit()

            new_user = User(
                first_name = request.form['firstname'].lower(),
                last_name = request.form['lastname'].lower(),
                password = generate_password_hash(request.form['password']),
                passenger_id = new_passenger.index,
                driver_id = existing_driver.index
            )
            db.session.add(new_user)
            db.session.commit()
            return render_template('error_template.html', main_message='Success!', sub_message='You have signed up and can now log in!', user=current_user)
        except Exception as e:
            logger.debug(e)
            return render_template('legacy_driver_to_login_template.html', message='There was an error. Please try again.', user=current_user)





@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """
    Login page for drivers and passengers.
    """
    if request.method == 'GET':
        return render_template('login_template.html', message='Login!', user=current_user)
    if request.method == 'POST':
        user = User.query.filter_by(first_name=request.form['firstname'].lower(), last_name=request.form['lastname'].lower()).first()
        if user is None:
            logger.debug('attempted user does not exist')
            return render_template('login_template.html', message='That user does not exist. Please try again.', user=current_user)
        if user.password is None:
            logger.debug('attempted user is probably a legacy driver')
            return render_template('error_template.html', main_message='Not registered', sub_message='The user exists in the database but is not registered to a user. Please use update/register.', user=current_user)

        if check_password_hash(user.password, request.form['password']):
            try:
                remember = request.form.get('remember')
            except ValueError:
                remember = False
            login_user(user, remember=remember)
            return redirect(url_for('home_page'))
        else:
            return render_template('login_template.html', message='Incorrect password. Please try again.', user=current_user)


@app.route('/generic-register', methods=['GET', 'POST'])
def generic_register_page():
    """
    Page that points to driver or passenger registration
    """
    return render_template('generic_register_template.html', user=current_user)



@app.route('/login-help')
def login_help_page():
    """
    Page for people to go to to change their password, see if they exist, or other
    """
    return render_template('login_help_template.html', user=current_user)




@app.route('/user-profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    """
    Page that allows for the management of the user profile
    """
    if current_user.is_driver() == 'Yes':
        return render_template('user_profile_template.html', user=current_user)
    else: 
        return render_template('user_profile_passenger_template.html', user=current_user)



@app.route('/update-user', methods=['GET', 'POST'])
@login_required
def update_user_information_page():
    """
    Page that allows for the updating of user information -- basically just a copy of the sign up page but with default values
    """
    regions = Region.query.all()
    if (request.method == 'GET') and (current_user.driver_profile is not None):
        return render_template('update_user_information_template.html', user=current_user, regions=regions)
    elif request.method == 'GET':
        
        logger.debug(current_user)
        logger.debug(current_user.driver_profile)
        logger.debug(current_user.passenger_profile)
        logger.debug(current_user.driver_id)
        return render_template('update_user_information_template_passenger.html', user=current_user, regions=regions)
    elif request.method == 'POST':
        # if the user is a driver
        if current_user.driver_profile is not None:
            
            region = Region.query.filter_by(name=request.form['region']).first()
            logger.debug(request.form['region'])
            driver_info = {
                'first_name':request.form['firstname'].lower(),
                'last_name': request.form['lastname'].lower(),
                'student_or_parent': request.form['studentorparent'],
                'num_years_with_license': request.form['licenseyears'],
                'phone_number': request.form['phonenumber'],
                'email_address': request.form['email'],
                'car_type_1': request.form['cartype1'],
                'car_color_1': request.form['carcolor1'],
                'car_type_2': request.form['cartype2'],
                'car_color_2': request.form['carcolor2'],
                'emergency_contact_number': request.form['emergencycontact'],
                'emergency_contact_relation': request.form['emergencycontactrelation'],
                'extra_information': request.form['note'],
                'num_seats': request.form['numberofseats'],
                'region_name': region.name,
                'address_line_1': request.form['addressline1'],
                'address_line_2': request.form['addressline2'],
                'city': request.form['city'],
                'zip_code': request.form['zipcode'],
            }
            try:
                existing_driver = current_user.driver_profile
                for key, value in driver_info.items():
                    setattr(existing_driver, key, value)
                db.session.commit()
                logger.info('Driver information updated: {}'.format(existing_driver))

                # deleting the unneeded rows so it can also be converted to passenger -- this is a bit of a hack <- copilot :(
                del driver_info['student_or_parent']
                del driver_info['num_years_with_license']
                del driver_info['num_seats']
                del driver_info['car_type_1']
                del driver_info['car_color_1']
                del driver_info['car_type_2']
                del driver_info['car_color_2']

                # updating the passenger information
                existing_passenger = current_user.passenger_profile
                for key, value in driver_info.items():
                    setattr(existing_passenger, key, value)
                db.session.commit()
                logger.info(f'Passenger Data modified: {existing_passenger}')

                # updating the user information
                current_user.first_name = request.form['firstname'].lower()
                current_user.last_name = request.form['lastname'].lower()
                db.session.commit()
                logger.info(f'User Data modified: {current_user}')

                return redirect(url_for("user_profile_page"))
            except Exception as e:
                logger.debug(e)
                return render_template('update_user_information_template.html', message='There was an error. Please try again.', user=current_user, regions=regions)
        # if the user is a passenger
        else:
            region = Region.query.filter_by(name=request.form['region']).first()
            logger.debug(request.form['region'])

            # defining passenger info
            passenger_info = {
                'first_name':request.form['firstname'].lower(),
                'last_name': request.form['lastname'].lower(),
                'phone_number': request.form['phonenumber'],
                'email_address': request.form['email'],
                'emergency_contact_number': request.form['emergencycontact'],
                'emergency_contact_relation': request.form['emergencycontactrelation'],
                'extra_information': request.form['note'],
                'region_name': region.name,
                'address_line_1': request.form['addressline1'],
                'address_line_2': request.form['addressline2'],
                'city': request.form['city'],
                'zip_code': request.form['zipcode'],
            }
            try:
                for key, value in passenger_info.items():
                    setattr(current_user.passenger_profile, key, value)
                db.session.commit()
                logger.info('Passenger information updated: {}'.format(current_user.passenger_profile))

                # updating the user information
                current_user.first_name = request.form['firstname'].lower()
                current_user.last_name = request.form['lastname'].lower()
                db.session.commit()
                logger.info(f'User Data modified: {current_user}')
                return redirect(url_for("user_profile_page"))
            except Exception as e:
                logger.debug(e)
                return render_template('update_user_information_template_passenger.html', message='There was an error. Please try again.', user=current_user, regions=regions)
            
    else: 
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)




@app.route('/manage-carpools', methods=['GET', 'POST'])
@login_required
def manage_carpools_page():
    """
    Page that allows for the management of carpools
    """

    try:
        driver_carpools = current_user.driver_profile.carpools
        logger.debug(driver_carpools)
        driver_carpools = [carpool for carpool in driver_carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(hours=30)]
        logger.debug(driver_carpools)
    except AttributeError as e:
        logger.debug('user is not a driver')
        logger.debug(e)
        driver_carpools = []
    passenger_carpools = current_user.passenger_profile.carpools
    logger.debug(passenger_carpools)
    passenger_carpools = [carpool for carpool in passenger_carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(hours=30)]
    logger.debug(passenger_carpools)

    return render_template('manage_carpools_template.html', user=current_user, driver_carpools=driver_carpools, passenger_carpools=passenger_carpools)



@app.route('/passenger/<lastname>/<firstname>')
@login_required
@requires_auth_key
def passenger_page(lastname, firstname):
    """
    Page that allows for the viewing of passenger information. Is only accessible if the person is logged in 
    and has an upcoming carpool with the person in it.
    """

    current_user_carpools = Carpool.query.filter_by(driver_index=current_user.driver_profile.index).all() # TODO:filter by current user and upcoming
    current_user_carpools = [carpool for carpool in current_user_carpools if carpool.event.event_end_time > datetime.datetime.now() + datetime.timedelta(hours=5)]

    # checking if the person is able to see
    for carpool in current_user_carpools:
        if (carpool.event.event_start_time) > datetime.datetime.now():
            for passenger in carpool.passengers:
                if (passenger.first_name == firstname) and (passenger.last_name == lastname):
                    return render_template('passenger_template.html', user=current_user, passenger=passenger)

    # if the person is not able to see
    return render_template('error_template.html', main_message='Go Away', sub_message='You do not have access to see the passenger.', user=current_user)

@login_required
@app.route('/cancel-carpool/<carpool_id>')
def cancel_carpool(carpool_id):
    """
    Page that allows for the cancellation of a carpool. Is not really used except for through carpool management page. Emails the passengers.
    """
    
    for carpool in current_user.driver_profile.carpools:
        if str(carpool.index) == carpool_id:
            logger.debug('got here')
            try:
                message = Message(
                    subject='Carpool Cancelled',
                    recipients=[passenger.email_address for passenger in carpool.passengers],
                    sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                    body=f'Hello passengers, \n\n Your carpool for {carpool.event.event_name} has been cancelled. Please contact the driver for more information, or sign up for another carpool.'
                )
                mail.send(message)
            except AssertionError as e:
                logger.debug('No passengers were on the carpool')
            logger.info('Email sent to passengers of carpool {} about cancellation'.format(carpool))

            carpool.driver = None
            carpool.driver_id = None
            carpool.passengers = []  
            carpool.destination = carpool.region.dropoff_location
            db.session.commit()
            return redirect(url_for('manage_carpools_page'))
    
    logger.debug(f'{current_user.driver_profile.carpools}')
    return render_template('error_template.html', main_message='Go Away', sub_message='You do not have access to cancel this carpool.', user=current_user)


@app.route('/leave-carpool/<carpool_id>')
@login_required
def leave_carpool(carpool_id):
    """
    Route that allows a passenger to leave a carpool
    """
    for carpool in current_user.passenger_profile.carpools: # making sure that the current user is in the carpool
        if str(carpool.index) == carpool_id:
            try:
                message = Message('A passenger has left the carpool.', recipients=[carpool.driver.email_address], sender=('Mech Techs Carpooling','mechtechscarpooling@zohomail.com'))
                message.body = f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                {current_user.first_name.capitalize()} {current_user.last_name.capitalize()} has left the carpool. Please check the carpool management page to see if you need to cancel the carpool.
                """
                mail.send(message)
                logger.info('Message sent to a driver.')
            except Exception as e:
                logger.warning(e)
                # maybe send an email to the admin
            
            carpool.passengers.remove(current_user.passenger_profile)
            db.session.commit()
            logger.info(f'User {current_user} left carpool {carpool}')

    return redirect(url_for('manage_carpools_page'))


@app.route('/change-carpool-destination', methods=['GET', 'POST'])
@login_required
def change_carpool_destination():
    """
    Page that allows for the change of the destination of a carpool.
    """
    if request.method == 'GET':
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)
    else:
        logger.info('changing carpool destination')
        new_destination = request.headers['New-Carpool-Destination']
        carpool_index = int(request.headers['Carpool-Index'])
        current_carpool = Carpool.query.filter_by(index=carpool_index).first()
        old_destination = current_carpool.destination
        current_carpool.destination = new_destination
        db.session.commit()
        logger.info('carpool destination changed to {} by {}'.format(new_destination, current_user))

        message = Message(
            'Carpool Destination Changed',
            recipients=[passenger.email_address for passenger in current_carpool.passengers],
            sender=('Mech Techs Carpooling','mechtechscarpooling@zohomail.com'),
            body=f"""
            Hello passengers of carpool for event {current_carpool.event.event_name}, \n\n
            The driver of the carpool has changed the destination from {old_destination} to {new_destination}. 
            Please make sure that you are ready to go to {new_destination} at the time of the carpool.
            """
        )
        mail.send(message)
        logger.info('Message sent to passengers of carpool.')
        return redirect(url_for('manage_carpools_page'))



@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_page():
    """
    Page that allows for the resetting of a password
    """
    if request.method == 'GET':
        return render_template('forgot_password_template.html', message='Enter your name to reset your password.', user=current_user)
    if request.method == 'POST':
        first_name = request.form['firstname'].lower()
        last_name = request.form['lastname'].lower()
        user = User.query.filter_by(first_name=first_name, last_name=last_name).first()
        if user:
            logger.info('User {} found'.format(user))
            message = Message(
                'Password Reset',
                recipients=[user.passenger_profile.email_address],
                sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                body=f"""
                Hello {user.first_name.capitalize()} {user.last_name.capitalize()}, \n\n
                You have requested a password reset. Please click the link below to reset your password. \n\n
                {url_for('reset_password_page', user_id=user.id, _external=True, token=user.get_reset_password_token())}
                """
            )
            mail.send(message)
            logger.info('Password reset link sent to user.')
            return render_template('forgot_password_template.html', message='Password reset link sent to your email address.', user=current_user)
        else:
            return render_template('forgot_password_template.html', message='User not found. Please register or try again.', user=current_user)

@app.route('/reset-password/<user_id>/<token>', methods=['GET', 'POST'])
def reset_password_page(user_id, token):
    """
    Page that allows for the resetting of a password
    user_id: the id of the user that is resetting their password
    token: the token that is used to verify that the user is who they say they are
    """
    if request.method == 'GET':
        user = User.query.filter_by(id=user_id).first()
        if user and user.verify_reset_password_token(token):
            return render_template('reset_password_template.html', user=current_user, user_id=user_id, token=token)
        else:
            return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)
    if request.method == 'POST':
        user = User.query.filter_by(id=user_id).first()
        if user and user.verify_reset_password_token(token):
            if request.form['password'] == request.form['confirmpassword']:
                user.password = generate_password_hash(request.form['password'], method='sha256')
                db.session.commit()
                logger.info('Password reset for user {}'.format(user))
                return redirect(url_for('login_page'))
            else: return render_template('reset_password_template.html', message='Passwords do not match. Please try again.', user=current_user, user_id=user_id, token=token)
        else:
            return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)

@app.route('/convert-to-driver', methods=['GET', 'POST'])
@login_required
def passenger_to_driver_page():
    """
    Page to change a passenger to a driver
    """
    if request.method == 'GET':
        return render_template('passenger_to_driver_template.html', user=current_user)
    if request.method == 'POST':
        new_driver = Driver(
            first_name = current_user.first_name,
            last_name = current_user.last_name,
            email_address = current_user.passenger_profile.email_address,
            phone_number = current_user.passenger_profile.phone_number,
            num_seats = request.form['numberofseats'],
            num_years_with_license = request.form['licenseyears'],
            car_type_1 = request.form['cartype1'],
            car_type_2 = request.form['cartype2'],
            car_color_1 = request.form['carcolor1'],
            car_color_2 = request.form['carcolor2'],
            emergency_contact_number = current_user.passenger_profile.emergency_contact_number,
            emergency_contact_relation = current_user.passenger_profile.emergency_contact_relation,
            student_or_parent = request.form['studentorparent'],
            address_line_1 = current_user.passenger_profile.address_line_1,
            address_line_2 = current_user.passenger_profile.address_line_2,
            city = current_user.passenger_profile.city,
            zip_code = current_user.passenger_profile.zip_code,
        )

        db.session.add(new_driver)
        db.session.commit()
        logger.info('New driver created: {}'.format(new_driver))
        current_user.driver_id = new_driver.index
        current_user.driver_profile = new_driver
        db.session.commit()
        logger.info('User {} converted to driver'.format(current_user))
        return redirect(url_for('home_page'))

        
@app.route('/admin')
@admin_required
def admin_home_page():
    """
    Page that allows for creation of events, creation of regions, and viewing of the valid authorization keys
    """

    return render_template('admin_home_template.html', user=current_user)


@app.route('/manage-users')
@admin_required
def manage_users_page():
    """
    Admin page that allows for the management of users
    """
    return render_template('manage_users_template.html', users=User.query.order_by(User.is_admin.desc()).all(), user=current_user)

@app.route('/admin-delete-user/<user_id>')
@admin_required
def admin_delete_user(user_id):
    """
    Method to delete a user
    """

    # grabbing the user
    user_to_delete = User.query.get(user_id)
    logger.info('Delete requested for user {} {}'.format(user_to_delete.first_name, user_to_delete.last_name))

    # checking that the user being deleted is not of a higher level than the current one
    if user_to_delete.is_admin >= current_user.is_admin:
        return redirect(url_for('manage_users_page'))

    # notifying the user that they are being deleted
    try:
        message = Message (
            subject='Your Account has been deleted',
            recipients= [user_to_delete.passenger_profile.email_address],
            sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
            body=f"""
            Hello {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()}, \n\n
            Your account has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
            """,
        )
        mail.send(message)
        logger.info('User {} notified of deletion'.format(user_to_delete))
    except Exception as e:
        logger.warning('User {} not notified of deletion, probably due to invalid email address'.format(user_to_delete))
        logger.debug(e)

    # notifying their passengers (if any) that they are being deleted
    try:
        user_to_delete_upcoming_carpools = [carpool for carpool in user_to_delete.driver_profile.carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(days=1)]
    except AttributeError as e:
        logger.debug(e)
        user_to_delete_upcoming_carpools = []
    
    for carpool in user_to_delete_upcoming_carpools:
        for passenger in carpool.passengers:
            try:
                message = Message (
                    subject='Your Driver has been deleted',
                    recipients= [passenger.passenger_profile.email_address],
                    sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com')
                    )
                message.body = f"""
                Hello {passenger.first_name.capitalize()} {passenger.last_name.capitalize()}, \n\n
                Your driver {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
                mail.send(message)
                logger.info('Passenger {} notified of driver deletion'.format(passenger))
            except Exception as e:
                logger.warning('Passenger {} not notified of driver deletion, probably due to invalid email address'.format(passenger))
                logger.debug(e)

    # notifying their drivers (if any) that they are being deleted
    user_to_delete_upcoming_carpools = [carpool for carpool in user_to_delete.passenger_profile.carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(days=1)]
    for carpool in user_to_delete_upcoming_carpools:
        try:
            message = Message (
                subject='Your Passenger has been deleted',
                recipients= [carpool.driver.user[0].passenger_profile.email_address],
                sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                body=f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                Your passenger {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
            )
        except Exception as e:
            logger.warning('Driver {} not notified of passenger deletion, probably due to invalid email address'.format(carpool.driver))
            logger.debug(e)


    # deleting the user and their carpools
    if user_to_delete.driver_profile is not None:
        for carpool in user_to_delete.driver_profile.carpools:
            carpool.driver = None
            carpool.driver_index = None

    for carpool in user_to_delete.passenger_profile.carpools:
        try:
            carpool.passengers.remove(user_to_delete)
        except ValueError as e: # this means that the user was not in the carpool
            logger.debug(e)
            pass

    db.session.commit()
    db.session.delete(user_to_delete.passenger_profile)
    try:
        db.session.delete(user_to_delete.driver_profile)
    except Exception as e:
        logger.debug(e) # passing after this

    db.session.delete(user_to_delete)
    db.session.commit()

    # redirecting back to the admin user page
    logger.info('User deleted.')
    return redirect(url_for('manage_users_page'))


@app.route('/give-admin/<user_id>')
@admin_required
def give_admin(user_id):
    """
    Method to give someone (regular) admin
    """
    user_to_change = User.query.get(user_id)
    # checking that they are not already super admin (that would be bad)
    if user_to_change.is_admin > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('manage_users_page'))

    user_to_change.is_admin = 1
    db.session.commit()
    logger.info('User {} {} given admin'.format(user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('manage_users_page'))

@app.route('/give_super_admin/<user_id>')
@admin_required
def give_super_admin(user_id):
    """
    Method to give someone super admin
    user_id: the id of the user to give super admin
    """
    user_to_change = User.query.get(user_id)
    user_to_change.is_admin = 2
    db.session.commit()
    logger.info('User {} {} given super admin'.format(user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('manage_users_page'))

@app.route('/remove-admin/<user_id>')
@admin_required
def remove_admin(user_id):
    """
    Method to remove someone from admin
    user_id: id of user to remove admin from
    """
    user_to_change = User.query.get(user_id)
    # checking that the person removing is of higher admin than user
    if user_to_change.is_admin >= current_user.is_admin:
        logger.info('User {} {} is of higher admin than user {} {}'.format(current_user.first_name.capitalize(), current_user.last_name.capitalize(), user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
        return redirect(url_for('manage_users_page'))

    if user_to_change.is_admin > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('manage_users_page'))

    user_to_change.is_admin = 0
    db.session.commit()
    logger.info('User {} {} removed from admin'.format(user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('manage_users_page'))


@app.route('/safety')
def safety():
    """
    Be safe
    """
    return render_template('safety.html', user=current_user)

@app.route('/delete-event/<event_index>')
@login_required
def delete_event(event_index):
    """
    Method to delete an event
    """
    try:
        event_to_delete = Event.query.get(event_index)
    except Exception as e:
        logger.debug(e)
        logger.info('Event {} not found'.format(event_index))
        return redirect(url_for('events_page'))
    
    # checking that the user is the creator of the event
    if not ((event_to_delete.user == current_user) or (current_user.is_admin > 0)):
        logger.info('A person attempted to delete an event they were not authorized to delete')
        return redirect(url_for('events_page'))
    
    # notifying the drivers of the event
    for carpool in event_to_delete.carpools:
        try:
            message = Message (
                subject='Your carpool event has been deleted',
                recipients= [carpool.driver.user[0].passenger_profile.email_address],
                sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                body=f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
            )
            mail.send(message)
            logger.info('Driver {} notified of event deletion'.format(carpool.driver))
        except Exception as e:
            logger.debug(e)
            logger.warning('Driver {} not notified of event deletion, probably due to invalid email address'.format(carpool.driver))
    
    # notifying the passengers of the event
    for carpool in event_to_delete.carpools:
        try:
            message = Message (
                subject='Your carpool event has been deleted',
                recipients= [passenger.passenger_profile.email_address for passenger in carpool.passengers],
                sender=('Mech Techs Carpooling', 'mechtechscaprooling@zohomail.com'),
                body=f"""
                Hello passengers, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
            )
            mail.send(message)
            logger.info('Passengers notified of event deletion')
        except Exception as e:
            logger.debug(e)
            logger.warning('Passengers not notified of event deletion, probably due to an invalid email address')
    
    # deleting the carpools of the event
    for carpool in event_to_delete.carpools:
        db.session.delete(carpool)

    # deleting the event
    db.session.delete(event_to_delete)
    db.session.commit()

    logger.info('Event {} deleted'.format(event_to_delete.event_name))
    return redirect(url_for('events_page'))


@app.route('/request-carpool/<event_index>', methods=['GET', 'POST'])
def passenger_carpool_request_page(event_index):
    """
    Page for a passenger to request a carpool
    event_index: index of the event
    """
    if request.method == 'GET':
        regions=Region.query.all()
        try:
            event = Event.query.get(event_index)
        except Exception as e:
            logger.debug(e)
            logger.info('Event {} not found'.format(event_index))
            return redirect(url_for('events_page'))

        if current_user.is_authenticated:
            event.passengers_needing_ride.append(current_user.passenger_profile)
            db.session.commit()
            logger.info('Passenger {} added to event as needing ride {}'.format(current_user.passenger_profile, event))

            # email the people in the area
            # finding the drivers in the area -- yes i can do this if i set lazy to dynamic but thats a lot of work
            drivers_in_area = [driver for driver in Driver.query.filter_by(region_name=region_name).all() if driver not in [carpool.driver for carpool in event.carpools]]      
            for driver in drivers_in_area:
                try:
                    message = Message (
                        subject='Passenger needs ride',
                        recipients= [driver.user[0].passenger_profile.email_address],
                        sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                        body=f"""
                        Hello {driver.first_name.capitalize()} {driver.last_name.capitalize()}, \n\n
                        A passenger in your area needs a ride to the event {event.event_name}. If you are going to the event,
                        please consider signing up to give them a ride.
                        """)
                    mail.send(message)
                    logger.info('Driver {} notified of passenger needing ride'.format(driver))
                except Exception as e:
                    logger.debug(e)
                    logger.warning('Driver {} not notified of passenger needing ride, probably due to invalid email address'.format(driver))
            logger.info('finished notifying drivers.')
            return redirect(url_for('event_page', event_index=event.index))
        else:
            regions = Region.query.all()
            return render_template('passenger_carpool_request_template.html', event=event, user=current_user, regions=regions)
    if request.method == 'POST':

        # making sure that the event exists ...
        try:
            event = Event.query.get(event_index)
        except Exception as e:
            logger.debug(e)
            logger.info('Event {} not found'.format(event_index))
            return redirect(url_for('events_page'))
        
        # getting the form data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        email_address = request.form['email']
        phone_number = request.form['phonenumber']
        region_name = request.form['region']
        
        # making sure that the user is not already in the database
        passenger = Passenger.query.filter_by(first_name=first_name, last_name=last_name).first()
        if passenger is not None:
            logger.info('Passenger {} already exists'.format(passenger))
            return render_template('error_page_template', main_message='You are already in the database', sub_message='Please log in to request a carpool.')
        
        # creating the passenger
        passenger = Passenger(first_name=first_name, last_name=last_name, email_address=email_address, phone_number=phone_number, region_name=region_name)
        db.session.add(passenger)
        db.session.commit()
        logger.info('Passenger {} created'.format(passenger))

        # adding the passenger to the event
        event.passengers_needing_ride.append(passenger)
        db.session.commit()

        # emailing the people in the region
        # finding the drivers in the area that haven't signed up to carpool
        drivers_in_area = [driver for driver in Driver.query.filter_by(region_name=region_name).all() if driver not in [carpool.driver for carpool in event.carpools]]
                    
        for driver in drivers_in_area:
            try:
                message = Message (
                    subject='Passenger needs ride',
                    recipients= [driver.user[0].passenger_profile.email_address],
                    sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                    body=f"""
                    Hello {driver.first_name.capitalize()} {driver.last_name.capitalize()}, \n\n
                    A passenger in your area needs a ride to the event {event.event_name}. If you are going to the event,
                    please consider signing up to give them a ride.
                    """)
                mail.send(message)
                logger.info('Driver {} notified of passenger needing ride'.format(driver))
            except Exception as e:
                logger.debug(e)
                logger.warning('Driver {} not notified of passenger needing ride, probably due to invalid email address'.format(driver))
        logger.info('finished notifying drivers.')
        return redirect(url_for('event_page', event_index=event.index))


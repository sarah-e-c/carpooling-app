from lib2to3.pgen2 import driver
from carpooling import db
from carpooling import app
from carpooling.models import Driver, AuthKey, Event, Passenger, Region, Carpool, StudentAndRegion, User
import logging
import time
from carpooling.utils import PersonAlreadyExistsException
from flask import render_template, request, redirect, url_for, make_response, flash, session
import secrets
import os
import datetime
from sqlalchemy import func
import hashlib
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash


DEFAULT_NUMBER_OF_CARPOOLS = 4

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/driver/<lastname>/<firstname>')
def driver_page(lastname, firstname):
    """
    View a driver's page
    """
    logger.info('driver_page')
    if app.driver_access_flag:
        logger.info('access granted')
        app.driver_access_flag = False
    else:
        try:
            driver_access_key_time = float(request.cookies.get('driver_access_key_time'))
            if time.time() - driver_access_key_time  > 60*60*24*30:
                logger.info('redirecting to driver_login')
                logger.info(time.time() - driver_access_key_time)
                return redirect(url_for('get_driver_access', firstname=firstname, lastname=lastname))
        except ValueError as e:
            return redirect(url_for('get_driver_access', firstname=firstname, lastname=lastname))
        except TypeError as e:
            return redirect(url_for('get_driver_access', firstname=firstname, lastname=lastname))
    
    logger.info('driver access granted in driver page')
    try:
        driver = Driver.query.filter_by(last_name=lastname, first_name=firstname).one()
    except:
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

                
    return render_template('driver_page_template.html', **driver_info, user=current_user)



@app.route('/get-driver-access/<lastname>/<firstname>', methods=['GET', 'POST'])
def get_driver_access(lastname, firstname):
    logger.info('get_driver_access')
    if request.method == 'GET':
        return render_template('get_driver_access_template.html', lastname=lastname, firstname=firstname, user=current_user)

    if request.method == 'POST':
        if request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key or request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key:
            app.__setattr__('driver_access_flag', True)
            response = make_response(redirect(url_for('driver_page', lastname=lastname, firstname=firstname)))
            response.set_cookie('driver_access_flag_time', str(time.time()))
            logger.info('driver access granted')
            return response
        else:
            return render_template('error_page_template.html', main_message='Incorrect key', sub_message='The key you entered was incorrect. Please try again.', user=current_user)



@app.route('/')
@app.route('/home')
def home_page(logout=False):
    """
    Home page
    """
    logout = request.args.get('logout')
    if logout:
        logout_user()
        logger.info(f'User {current_user} logged out')
    return render_template('index.html', user=current_user)


@app.route('/register-driver', methods=['GET','POST'])
@app.route('/registerdriver', methods=['GET','POST'])
@app.route('/registeruser', methods=['GET','POST'])
@app.route('/register', methods=['GET','POST'])
@app.route('/register-user', methods=['GET','POST'])
def register_new_driver_page():
    """
    Page to register a new driver to the database.
    """
    
    # updating the auth keys
    if (datetime.datetime.now() - AuthKey.query.order_by(AuthKey.index.desc()).first().date_created).days > 29:
        new_auth_key = AuthKey(auth_key=secrets.token_hex(16))
        db.session.add(new_auth_key)
        db.session.commit()
    
    if request.method == 'GET':
        message = request.args.get('message')
        if message is None:
            message = 'Register to be a driver for team 422!'
        return render_template('driver_sign_up_template.html', message=message, user=current_user)
    if request.method == 'POST':

        
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
            'num_seats': request.form['numberofseats']
        }
        try:
            if (Driver.query.filter_by(first_name = driver_info['first_name'], last_name = driver_info['last_name']).count() > 0):
                raise PersonAlreadyExistsException()
            if (Passenger.query.filter_by(first_name = driver_info['first_name'], last_name = driver_info['last_name']).count() > 0):
                raise PersonAlreadyExistsException()
            
            new_driver = Driver(**driver_info)

            # deleting the unneeded rows so it can also be converted to passenger
            del driver_info['student_or_parent']
            del driver_info['num_years_with_license']
            del driver_info['num_seats']
            del driver_info['car_type_1']
            del driver_info['car_color_1']
            del driver_info['car_type_2']
            del driver_info['car_color_2']


            new_passenger = Passenger(**driver_info)
            db.session.add(new_passenger)
            db.session.add(new_driver)
            db.session.commit()
            logger.info(f'New driver added to database: {new_driver}')

            user_info = {
                'first_name': new_driver.first_name,
                'last_name': new_driver.last_name,
                'password': generate_password_hash(request.form['password'], method='sha256'),
                'driver_id': new_driver.index,
                'passenger_id': new_passenger.index
            }

            new_user = User(**user_info)
            db.session.add(new_user)
            db.session.commit()
            logger.info('New user registered.')

        except PersonAlreadyExistsException as e:
            logger.info(e)
            return redirect(url_for("register_new_driver_page", message='A person with that name already exists.'))
        except Exception as e:
            logger.info(e)
            return redirect(url_for("register_new_driver_page", message='Something went wrong. Make sure that all inputs are valid.'))
        return render_template('error_page_template.html', main_message='Success!', sub_message='Thank you for helping team 422!', user=current_user)
    else: 
        return render_template('error_page_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)


@app.route('/admin', methods=['GET', 'POST'])
def admin_login_page():
    """
    Admin login page
    """
    if request.method == 'GET':
        return render_template('admin.html', user=current_user)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.environ['ADMIN_USERNAME'] and password == os.environ['ADMIN_PASSWORD']:
            app.admin_access_flag = True
            return redirect(url_for('valid_auth_keys_page'))
        else:
            return render_template('error_page_template.html', main_message='Incorrect username or password', sub_message='The username or password you entered was incorrect. Please try again.', user=current_user)


@app.route('/valid-auth-keys')
def valid_auth_keys_page():
    """
    This page is only accessible if the admin has logged in.
    Page for admins to see all valid auth keys and when they were created.
    """
    if app.admin_access_flag:
        app.admin_access_flag = False
        auth_keys = AuthKey.query.order_by(AuthKey.date_created).all()
        return_list = []
        return_list_2 = []
        for item in auth_keys:
            return_list.append(item.key)
            return_list_2.append(item.date_created)
        
        return (f'Valid auth keys: {return_list} <br> Date created: {return_list_2}')
    else:
        return 'You are not authorized to view this page.'

@app.route('/events')
def events_page():
    """
    Events page
    """
    current_events = Event.query.filter(Event.event_date >= datetime.datetime.now()).all()
    print(current_events)
    
    return render_template('events_page_template.html', events=current_events, user=current_user)

@app.route('/event/<event_index>')
def event_page(event_index):
    """
    Event page
    """
    event = Event.query.get(event_index)
    logger.info(Event.query.all()[0].index)
    logger.info(event)
   
    return render_template('event_page_template.html', event=event, regions=Region.query.all(), user=current_user)

@app.route('/create-event', methods=['GET', 'POST'])
def create_event():
    """
    Create event page. Used for admins to create an event needs
    """
    if request.method == 'GET':
        message = request.args.get('message')
        if message is None:
            message = 'Create an Event'
        return render_template('create_event_template.html', message=message, user=current_user)

    
    if request.method == 'POST':
        event_info = {
            'event_name': request.form['eventname'],
            'event_date': datetime.datetime.strptime(request.form['eventdate'], '%Y-%m-%d'),
            'event_start_time': datetime.datetime.strptime(request.form['eventstarttime'], '%H:%M'),
            'event_end_time': datetime.datetime.strptime(request.form['eventendtime'], '%H:%M'),
            'event_location': request.form['eventlocation'],
            'event_description': request.form['eventdescription']
        }
        try:
            new_event = Event(**event_info)
            db.session.add(new_event)
            db.session.commit()

            for region in Region.query.all():
                # for each region, create carpools
                for _ in range(DEFAULT_NUMBER_OF_CARPOOLS):
                    carpool = Carpool(event_index=new_event.index, region_name=region.name, num_passengers=0, destination=region.dropoff_location)
                    db.session.add(carpool)
            
            db.session.commit()
            logger.info(f'New event added to database: {new_event} with carpools: {new_event.carpools}')

        except Exception as e:
            logger.info(e)
            return redirect(url_for("create_event", message='Something went wrong. Make sure that all inputs are valid.'))

        return render_template('error_page_template.html', main_message='Success!', sub_message='An event has been created! People can now sign up!', user=current_user)
    else: 
        return render_template('error_page_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)


@app.route('/driver-signup/<carpool_index>', methods=['GET', 'POST'])
def driver_carpool_signup_page(carpool_index):
    """
    Page that drivers go to when they are signing up for a carpool. Still needs a check for sign in
    """
    if request.method == 'GET':
        if current_user.is_authenticated:
            carpool = Carpool.query.get(carpool_index)
            carpool.driver = current_user.driver_profile
            carpool.num_passengers = current_user.driver_profile.num_seats
            carpool.driver_index = current_user.driver_profile.index
            db.session.commit()
            logger.info(f'{current_user} signed up for carpool {carpool}')
            return render_template('error_page_template.html', main_message='Success!', sub_message='You have signed up to drive! Thank you for helping the team!', user=current_user) 

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
            return render_template('error_page_template.html', main_message='Success!', sub_message='You have successfully signed up for a carpool!', user=current_user)




@app.route('/passenger-signup/<carpool_index>', methods=['GET', 'POST'])
def passenger_carpool_signup_page(carpool_index):
    """
    Page for the passenger to sign up for a carpool
    """

    if request.method == 'GET':
        carpool = Carpool.query.get(carpool_index)
        return render_template('passenger_carpool_sign_up_template.html', carpool=carpool, message='Sign up for a carpool!', user=current_user)


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
                #TODO

                logger.info('new temp passenger created')
                return render_template('error_page_template.html', main_message='Success!', sub_message='A new passenger was registered, and you have successfully signed up for a carpool!', user=current_user)
            except Exception as e:
                logger.debug(e)
                return render_template('passenger_carpool_sign_up_template.html', carpool=carpool, message='There was an error registering a new passenger. Try again.', user=current_user)

        else:
            passenger.extra_information = request.form['note']
            carpool.passengers.append(passenger)
            db.session.add(passenger)
            db.session.commit()
            logger.info('existing passenger added to carpool without sign in')
            return render_template('error_page_template.html', main_message='Success!', sub_message='The passenger already existed in the database. Please register to use all features.', user=current_user)


    carpool  = Carpool.query.get(carpool_index)
    return str(carpool.passengers[0].carpools) + str(len(carpool.passengers))




@app.route('/register-passenger', methods=['GET', 'POST'])
def register_passenger_page():
    """
    Register passenger page.
    """
    if request.method == 'GET':
        regions = Region.query.all()
        return render_template('passenger_sign_up_template.html', regions=regions, user=current_user)

    if request.method == 'POST':
        if request.form['password'] != request.form['confirmpassword']: # the form password is unequal to this password
            regions = Region.query.all()
            return render_template('passenger_sign_up_template.html', message='Passwords do not match. Please try again.', regions=regions, user=current_user)

        studentandregion = StudentAndRegion.query.filter_by(student_first_name=request.form['firstname'], student_last_name=request.form['lastname']).first()
        if studentandregion is None:
            region_name = request.form['region']
            

        else:
            region_name = studentandregion.region_name

        try:
            passenger_information = {
                'first_name': request.form['firstname'].lower(),
                'last_name': request.form['lastname'].lower(),
                'email_address': request.form['email'],
                'phone_number': request.form['phonenumber'],
                'region_name': region_name,
                'extra_information': request.form['note'],
                'emergency_contact_number': request.form['emergencycontact'],
                'emergency_contact_relation': request.form['emergencycontactrelation']

            }

            passenger = Passenger(**passenger_information)
            db.session.add(passenger)
            db.session.commit()
            logger.info('A new passenger has been added to the database!')

            user_information = {
                'first_name': request.form['firstname'].lower(),
                'last_name': request.form['lastname'].lower(),
                'password': generate_password_hash(request.form['password'], method='sha256'),
                'passenger_id': passenger.index,
                'driver_id': None,
            }
        
            user = User(**user_information)
            db.session.add(user)
            db.session.commit()


        except Exception as urMom:
            logger.info(urMom)
            return render_template('passenger_sign_up_template.html', message='There was an error', user=current_user)
        
    
        return render_template('error_page_template.html', main_message='Success!', sub_message='You have signed up!', user=current_user)


        
        



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
                password = generate_password_hash(request.form['password'], method='sha256'),
                passenger_id = new_passenger.index,
                driver_id = existing_driver.index
            )
            db.session.add(new_user)
            db.session.commit()
            return render_template('error_page_template.html', main_message='Success!', sub_message='You have signed up and can now log in!', user=current_user)
        except Exception as e:
            logger.debug(e)
            return render_template('legacy_driver_to_login_template.html', message='There was an error. Please try again.', user=current_user)





@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """
    Login page for drivers and passengers.
    """
    if request.method == 'GET':
        return render_template('login.html', message='Login!', user=current_user)
    if request.method == 'POST':
        user = User.query.filter_by(first_name=request.form['firstname'].lower(), last_name=request.form['lastname'].lower()).first()
        if user is None:
            return render_template('login.html', message='That user does not exist. Please try again.', user=current_user)
        if user.password is None:
            return render_template('error_page_template.html', main_message='Not registered', sub_message='The user exists in the database but is not registered to a user. Please use update/register.', user=current_user)

        if check_password_hash(user.password, request.form['password']):
            login_user(user, remember=request.form['remember'])
            return redirect(url_for('home_page'))
        else:
            return render_template('login.html', message='Incorrect password. Please try again.', user=current_user)


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
    return render_template('login_help_page_template.html', user=current_user)

@app.route('/admin_home')
def admin_home_page():
    """
    Page that allows for creation of events, creation of regions, and viewing of the valid authorization keys
    """
    pass

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_page():
    pass #TODO

@login_required
@app.route('/user-profile/<user_id>', methods=['GET', 'POST'])
def user_profile_page(user_id):
    return render_template('user_profile_page_template.html', user=current_user)
    """
    Page that allows for the management of the user profile
    """
    pass

@login_required
@app.route('/update-user', methods=['GET', 'POST'])
def update_user_information_page():
    return 'update user information page'
    # TODO

    
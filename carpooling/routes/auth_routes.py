"""
All routes that have to do with authorization are defined here.
"""

from carpooling import db, mail
from carpooling.models import Driver, AuthKey, Passenger, Region, User
import logging
from carpooling.tasks import send_async_email
from carpooling.utils import PersonAlreadyExistsException, InvalidNumberOfSeatsException
from flask import render_template, request, redirect, url_for, make_response, flash, Blueprint, current_app
import secrets
import datetime
from flask_login import login_required, current_user, login_user
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeSerializer
from flask_mail import Message

auth_blueprint = Blueprint('auth', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


@auth_blueprint.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('main.home_page'))
        else:
            return render_template('login_template.html', message='Incorrect password. Please try again.', user=current_user)


@auth_blueprint.route('/reset-password/<user_id>/<token>', methods=['GET', 'POST'])
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
                return redirect(url_for('auth.login_page'))
            else: return render_template('reset_password_template.html', message='Passwords do not match. Please try again.', user=current_user, user_id=user_id, token=token)
        else:
            return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)


@auth_blueprint.route('/verify_auth_key/<next>/<kwargs_keys>/<kwargs_string>', methods=['GET', 'POST'])
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
                s = URLSafeSerializer(current_app.secret_key)
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
                s = URLSafeSerializer(current_app.secret_key)
                logger.info('setting cookie')
                response.set_cookie('driver-access', s.dumps(['access granted']), max_age=datetime.timedelta(seconds=60))
                return response

            else:
                # invalid key
                flash('Invalid Auth Key')
                logger.info('access denied')
                return render_template('get_driver_access_template.html', next=next, kwargs_keys=kwargs_keys, kwargs_string=kwargs_string, user=current_user, message='Invalid Key')

@auth_blueprint.route('/register', methods=['GET','POST'])
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
            return redirect(url_for("auth.register_new_driver_page", message='A person with that name already exists.'))
        except InvalidNumberOfSeatsException as e:
            logger.info(e)
            return redirect(url_for("auth.register_new_driver_page", message='The number of seats must be an integer.'))
        except Exception as e:
            logger.info(e)
            return redirect(url_for("auth.register_new_driver_page", message='Something went wrong. Make sure that all inputs are valid.'))
        
        return render_template('error_template.html', main_message='Success!', sub_message='Thank you for helping team 422!', user=current_user)



@auth_blueprint.route('/register-passenger', methods=['GET', 'POST'])
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


@auth_blueprint.route('/update-user', methods=['GET', 'POST'])
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

                return redirect(url_for("auth.user_profile_page"))
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
                return redirect(url_for("auth.user_profile_page"))
            except Exception as e:
                logger.debug(e)
                return render_template('update_user_information_template_passenger.html', message='There was an error. Please try again.', user=current_user, regions=regions)
            
    else: 
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)

@auth_blueprint.route('/convert-to-driver', methods=['GET', 'POST'])
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
        return redirect(url_for('main.home_page'))

@auth_blueprint.route('/forgot-password', methods=['GET', 'POST'])
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
            send_async_email.delay(user.passenger_profile.email_address, 'Password Reset', f"""
                Hello {user.first_name.capitalize()} {user.last_name.capitalize()}, \n\n
                You have requested a password reset. Please click the link below to reset your password. \n\n
                {url_for('auth.reset_password_page', user_id=user.id, _external=True, token=user.get_reset_password_token())}
                """ )
            logger.info('Password reset link task started.')
            return render_template('forgot_password_template.html', message='Password reset link sent to your email address.', user=current_user)
        else:
            return render_template('forgot_password_template.html', message='User not found. Please register or try again.', user=current_user)

@auth_blueprint.route('/user-profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    """
    Page that allows for the management of the user profile
    """
    if current_user.is_driver() == 'Yes':
        return render_template('user_profile_template.html', user=current_user)
    else: 
        return render_template('user_profile_passenger_template.html', user=current_user)

@auth_blueprint.route('/legacy-driver-to-current', methods=['GET', 'POST'])
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

@auth_blueprint.route('/login-help')
def login_help_page():
    """
    Page for people to go to to change their password, see if they exist, or other
    """
    return render_template('login_help_template.html', user=current_user)

@auth_blueprint.route('/generic-register', methods=['GET', 'POST'])
def generic_register_page():
    """
    Page that points to driver or passenger registration
    """
    return render_template('generic_register_template.html', user=current_user)


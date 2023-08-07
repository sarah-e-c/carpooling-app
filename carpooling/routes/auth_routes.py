"""
All routes that have to do with authorization are defined here.
"""

from carpooling import db, mail
from carpooling.models import Address, User
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
        user = User.query.filter_by(first_name=request.form['firstname'].lower(),
                                    last_name=request.form['lastname'].lower()).first()
        if user is None:
            logger.debug('attempted user does not exist')
            return render_template('login_template.html', message='That user does not exist. Please try again.',
                                   user=current_user)
        if user.password is None:
            logger.debug('attempted user is probably a legacy driver')
            return render_template('error_template.html', main_message='Not registered',
                                   sub_message='The user exists in the database but is not registered to a user. Please use update/register.',
                                   user=current_user)

        if check_password_hash(user.password, request.form['password']):
            try:
                remember = request.form.get('remember')
            except ValueError:
                remember = False
            login_user(user, remember=remember)
            return redirect(url_for('main.home_page'))
        else:
            return render_template('login_template.html', message='Incorrect password. Please try again.',
                                   user=current_user)


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
            return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.',
                                   user=current_user)
    if request.method == 'POST':
        user = User.query.filter_by(id=user_id).first()
        if user and user.verify_reset_password_token(token):
            if request.form['password'] == request.form['confirmpassword']:
                user.password = generate_password_hash(request.form['password'], method='sha256')
                db.session.commit()
                logger.info('Password reset for user {}'.format(user))
                return redirect(url_for('auth.login_page'))
            else:
                return render_template('reset_password_template.html',
                                       message='Passwords do not match. Please try again.', user=current_user,
                                       user_id=user_id, token=token)
        else:
            return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.',
                                   user=current_user)


# @auth_blueprint.route('/verify_auth_key/<next>/<kwargs_keys>/<kwargs_string>', methods=['GET', 'POST'])
# def verify_auth_key_page(next, kwargs_keys, kwargs_string):
#     """
#     Page that users are redirected to if they need to get an auth key
#     next: the next page to go to
#     kwargs_keys: the keys of the kwargs, encoded by the decorator
#     kwargs_string: the values of the kwargs, encoded by the decorator

#     This page is called by the decorator requires_auth_key, and is pretty much exclusivelt used for that purpose.

#     """
#     if request.method == 'GET':
#         # this is how the things are encoded
#         # kwargs_keys = '--'.join(kwargs)
#         # kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
#         return render_template('get_driver_access_template.html', next=next, kwargs_keys=kwargs_keys,
#                                kwargs_string=kwargs_string, user=current_user)
#     if request.method == 'POST':
#         try:
#             has_key = request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key or request.form['key'] == \
#                     AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key
#         except IndexError:
#             has_key = request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key

#         if has_key:
#             if current_user.is_authenticated:
#                 current_user.team_auth_key = AuthKey.query.order_by(AuthKey.index.desc()).first().key
#                 db.session.commit()
#                 logger.info('Driver access granted to user {}'.format(current_user))

#             # re-encoding the keys
#             kwargs = {}
#             for kwarg_key, kwarg in zip(kwargs_keys.split('--'), kwargs_string.split('--')):
#                 kwargs[kwarg_key] = kwarg

#             # setting the response
#             response = make_response(redirect(url_for(next, **kwargs)))
#             s = URLSafeSerializer(current_app.secret_key)
#             logger.info('setting cookie')
#             response.set_cookie('driver-access', s.dumps(['access granted']),
#                                 max_age=datetime.timedelta(seconds=60))
#             return response
#         else:
#             flash('Invalid Auth Key')  # theres no flash support but like whatever
#             return render_template('get_driver_access_template.html', next=next, kwargs_keys=kwargs_keys,
#                                    kwargs_string=kwargs_string, user=current_user, message='Invalid Key')


@auth_blueprint.route('/update-user', methods=['GET', 'POST'])
@login_required
def update_user_information_page():
    """
    Page that allows for the updating of user information -- basically just a copy of the sign up page but with default values
    """
    if (request.method == 'GET') and (current_user.num_seats is not None):
        return render_template('update_user_information_template.html', user=current_user)
    elif request.method == 'GET':
        logger.debug(current_user)
        return render_template('update_user_information_template_passenger.html', user=current_user)
    elif request.method == 'POST':
        # if the user is a driver
        if current_user.num_seats is not None:
            try:
                logger.info(request.form)
                current_user.addresses[0].address_line_1 = request.form['addressline1']
                current_user.addresses[0].address_line_2 = request.form['addressline2']
                current_user.addresses[0].city = request.form['city']
                current_user.addresses[0].zip_code = request.form['zipcode']
                current_user.addresses[0].latitude = request.form['latitude']
                current_user.addresses[0].longitude = request.form['longitude']
                current_user.addresses[0].code = request.form['place_id']
                current_user.first_name = request.form['firstname'].lower()
                current_user.last_name = request.form['lastname'].lower()
                current_user.email_address = request.form['email']
                current_user.phone_number = request.form['phonenumber']
                current_user.extra_information = request.form['note']
                current_user.car_type_1 = request.form['cartype1']
                current_user.car_color_1 = request.form['carcolor1']
                current_user.car_type_2 = request.form['cartype2']
                current_user.car_color_2 = request.form['carcolor2']
                current_user.emergency_contact_number = request.form['emergencycontact']
                current_user.emergency_contact_relation = request.form['emergencycontactrelation']
                current_user.num_seats = request.form['numberofseats']
                current_user.num_years_with_license = request.form['licenseyears']
                current_user.student_or_parent = request.form['studentorparent']
                db.session.commit()
                return redirect(url_for('auth.user_profile_page'))
            except Exception as e:
                logger.debug(e)
                flash("There was an error. Please make sure that your information is valid and try again.")
                return render_template('update_user_information_template.html', message='There was an error',
                                       user=current_user)
        # if the user is a passenger
        else:
            try:
                current_user.addresses[0].address_line_1 = request.form['addressline1']
                current_user.addresses[0].address_line_2 = request.form['addressline2']
                current_user.addresses[0].city = request.form['city']
                current_user.addresses[0].zip_code = request.form['zipcode']
                current_user.addresses[0].latitude = request.form['latitude']
                current_user.addresses[0].longitude = request.form['longitude']
                current_user.addresses[0].code = request.form['place_id']
                current_user.first_name = request.form['firstname'].lower()
                current_user.last_name = request.form['lastname'].lower()
                current_user.email_address = request.form['email']
                current_user.phone_number = request.form['phonenumber']
                current_user.extra_information = request.form['note']
                current_user.emergency_contact_number = request.form['emergencycontact']
                current_user.emergency_contact_relation = request.form['emergencycontactrelation']
                db.session.commit()
                return redirect(url_for('auth.user_profile_page'))
            except Exception as e:
                logger.debug(e)
                return render_template('update_user_information_template_passenger.html',
                                       message='There was an error. Please try again.', user=current_user)

    else:
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.',
                               user=current_user)


@auth_blueprint.route('/convert-to-driver', methods=['GET', 'POST'])
@login_required
def passenger_to_driver_page():
    """
    Page to change a passenger to a driver
    """
    if request.method == 'GET':
        return render_template('passenger_to_driver_template.html', user=current_user)
    if request.method == 'POST':
        # updating the user information
        current_user.num_seats = request.form['numberofseats']
        current_user.num_years_with_license = request.form['licenseyears']
        current_user.student_or_parent = request.form['studentorparent']
        current_user.car_type_1 = request.form['cartype1']
        current_user.car_color_1 = request.form['carcolor1']
        current_user.car_type_2 = request.form['cartype2']
        current_user.car_color_2 = request.form['carcolor2']
        db.session.commit()

        logger.info(f'User Data modified: {current_user}')
        return redirect(url_for('main.home_page'))


@auth_blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_page():
    """
    Page that allows for the resetting of a password
    """
    if request.method == 'GET':
        return render_template('forgot_password_template.html', message='Enter your name to reset your password.',
                               user=current_user)
    if request.method == 'POST':
        first_name = request.form['firstname'].lower()
        last_name = request.form['lastname'].lower()
        user = User.query.filter_by(first_name=first_name, last_name=last_name).first()
        if user:
            logger.info('User {} found'.format(user))
            send_async_email.delay(user.email_address, 'Password Reset', f"""
                Hello {user.first_name.capitalize()} {user.last_name.capitalize()}, \n\n
                You have requested a password reset. Please click the link below to reset your password. \n\n
                {url_for('auth.reset_password_page', user_id=user.id, _external=True, token=user.get_reset_password_token())}
                """)
            logger.info('Password reset link task started.')
            return render_template('forgot_password_template.html',
                                   message='Password reset link sent to your email address.', user=current_user)
        else:
            return render_template('forgot_password_template.html',
                                   message='User not found. Please register or try again.', user=current_user)


@auth_blueprint.route('/user-profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    """
    Page that allows for the management of the user profile
    """
    return render_template('user_profile_template.html', user=current_user)

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

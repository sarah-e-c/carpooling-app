
from carpooling.models import User, AuthKey
from carpooling import mail
from flask import redirect, url_for, session, request
from flask_mail import Message
from flask_login import current_user
from functools import wraps
from itsdangerous import URLSafeSerializer
import logging
from flask import current_app


logger = logging.getLogger(__name__)

class PersonAlreadyExistsException(Exception):
    """Exception for a person already existing """
    pass

class InvalidNumberOfSeatsException(Exception):
    """Exception for an invalid number of seats"""
    pass


def critical_error():
    """Critical error function"""
    logger.critical('Critical error')
    return 'Critical error'

def check_cookie():
    pass


def requires_auth_key(function):
    """
    Decorator for checking if a user has a valid auth key. If they do not, they are redirected to the auth key page.
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.is_admin > 0: # admins don't need auth keys
                return function(*args, **kwargs) 
            try:
                if not (current_user.team_auth_key == AuthKey.query.order_by(AuthKey.index.desc()).first().key) or (current_user.team_auth_key == AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key):
                # encoding the key word args for the url
                    kwargs_keys = '--'.join(kwargs)
                    kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                    if not kwargs_keys:
                        kwargs_keys = '--'
                    if not kwargs_string:
                        kwargs_string = '--'
                    return redirect(url_for('auth.verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))
            except:
                if not (current_user.team_auth_key == AuthKey.query.order_by(AuthKey.index.desc()).first().key):
                # encoding the key word args for the url
                    kwargs_keys = '--'.join(kwargs)
                    kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                    if not kwargs_keys:
                        kwargs_keys = '--'
                    if not kwargs_string:
                        kwargs_string = '--'
                    return redirect(url_for('auth.verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))
        else:
            s = URLSafeSerializer(current_app.secret_key)
            try:
                if s.loads(request.cookies.get('driver-access'))[0] == 'access granted':
                    logger.info('Access granted')
                    return function(*args, **kwargs)
                else:
                    kwargs_keys = '--'.join(kwargs)
                    kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                    if not kwargs_keys:
                        kwargs_keys = '--'
                    if not kwargs_string:
                        kwargs_string = '--'
                    return redirect(url_for('auth.verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))
            except TypeError as e: # this is very awful
                logger.debug(e)
                kwargs_keys = '--'.join(kwargs)
                kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                return redirect(url_for('auth.verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))

        return function(*args, **kwargs)
    return wrapper

def admin_required(function):
    """
    Decorator for checking if a user is an admin. If they are not, they are redirected to the home page.
    """
    
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.is_admin > 0:
                return function(*args, **kwargs)
            else:
                return redirect(url_for('main.home_page'))
        else:
            return redirect(url_for('main.home_page'))
    return wrapper

def super_admin_required():
    """
    Decorator for checking if a user is a super admin. If they are not, they are redirected to the home page.
    """
    
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.is_admin > 1:
                return function(*args, **kwargs)
            else:
                return redirect(url_for('main.home_page'))
        else:
            return redirect(url_for('main.home_page'))
    return wrapper

def driver_required(function):
    """
    Decorator for checking if a user is a driver. If they are not, they are redirected to the home page.
    """
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.driver_profile is not None:
                return function(*args, **kwargs)
            else:
                return redirect(url_for('main.home_page'))
        else:
            return redirect(url_for('main.home_page'))
    
    return wrapper


def initial_set_up():
    """
    Function for setting up the initial admin user.
    """
    pass # TODO

def send_email(to, subject, message):
    """
    Function for sending emails.
    to: recipient email.
    subject: subject of the email.
    message: message of the email.
    """
    try:
        msg = Message(subject, sender=(current_app.config['MAIL_USERNAME'], 'Mech Techs Carpooling'), recipients=[to])
        msg.body = message
        mail.send(msg)
        logger.info('Email sent to %s', to)
    except Exception as e:
        logger.debug(e)
        logger.warning('Email failed to send to {}, probably due to an invalid email adderss'.format(to))


    

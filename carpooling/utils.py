
from carpooling.models import User, AuthKey
from carpooling import app
from flask import redirect, url_for, session, request
from flask_login import current_user
from functools import wraps
from itsdangerous import URLSafeSerializer
import logging


logger = logging.getLogger(__name__)

class PersonAlreadyExistsException(Exception):
    """Exception for a person already existing """
    def __init__():
        super().__init__()

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
            try:
                if not (current_user.team_auth_key == AuthKey.query.order_by(AuthKey.index.desc()).first().key) or (current_user.team_auth_key == AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key):
                # encoding the key word args for the url
                    kwargs_keys = '--'.join(kwargs)
                    kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                    if not kwargs_keys:
                        kwargs_keys = '--'
                    if not kwargs_string:
                        kwargs_string = '--'
                    return redirect(url_for('verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))
            except:
                if not (current_user.team_auth_key == AuthKey.query.order_by(AuthKey.index.desc()).first().key):
                # encoding the key word args for the url
                    kwargs_keys = '--'.join(kwargs)
                    kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                    if not kwargs_keys:
                        kwargs_keys = '--'
                    if not kwargs_string:
                        kwargs_string = '--'
                    return redirect(url_for('verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))
        else:
            s = URLSafeSerializer(app.secret_key)
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
                    return redirect(url_for('verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))
            except TypeError as e: # this is very awful
                logger.debug(e)
                kwargs_keys = '--'.join(kwargs)
                kwargs_string = '--'.join([kwargs[kwarg] for kwarg in kwargs])
                return redirect(url_for('verify_auth_key_page', next=function.__name__, kwargs_keys=kwargs_keys, kwargs_string =kwargs_string))

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
                return redirect(url_for('home_page'))
        else:
            return redirect(url_for('home_page'))
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
                return redirect(url_for('home_page'))
        else:
            return redirect(url_for('home_page'))
    
    return wrapper




from lib2to3.pgen2 import driver
from carpooling import db
from carpooling import app
from carpooling.models import Driver, AuthKey
import logging
import time
from carpooling.utils import PersonAlreadyExistsException
from flask import render_template, request, redirect, url_for, make_response
import secrets
import os
import datetime
from sqlalchemy import func

admin_access_flag = False

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/driver/<lastname>/<firstname>')
def driver_page(lastname, firstname):
    """
    View a driver's page
    lastname -- driver's last name
    firstname -- driver's first name
    """
    logger.info('driver_page')
    if app.driver_access_flag:
        logger.info('access granted manually')
        app.driver_access_flag = False
    else:
        try:
            # testing to see if they have the cookie and if it's a month old
            driver_access_key_time = float(request.cookies.get('driver_access_key_time'))
            if time.time() - driver_access_key_time  > 60*60*24*30:
                logger.info('redirecting to driver_login')
                logger.info(time.time() - driver_access_key_time)
                response = make_response(redirect(url_for('get_driver_access', firstname=firstname, lastname=lastname)))
                response.status_code = 302
                return response
            else:
                logger.info(time.time() - driver_access_key_time)

        except ValueError as e:
            logger.info(request.cookies.get('driver_access_key_time'))
            logger.info('ValueError: {}'.format(e))
            response = make_response(redirect(url_for('get_driver_access', firstname=firstname, lastname=lastname)))
            response.status_code=302
            return response

        except TypeError as e:
            logger.info('TypeError: {}'.format(e))
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

                
    return render_template('driver_page_template.html', **driver_info)


@app.route('/get-driver-access/<lastname>/<firstname>', methods=['GET', 'POST'])
def get_driver_access(lastname, firstname):
    """
    Route to get driver access.
    lastname -- driver's last name (to be used in redirect)
    firstname -- driver's first name (to be used in redirect)
    """
    logger.info('get_driver_access')
    if request.method == 'GET':
        return render_template('get_driver_access_template.html', lastname=lastname, firstname=firstname)
    if request.method == 'POST':
        try: # try here makes it so that if there is not 2 keys to use then it will still work
            if ((request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key or request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key) or (request.form['key'] == os.environ.get('PERM_TEST_KEY'))):
                # if its right, set the cookie
                app.__setattr__('driver_access_flag', True)
                response = make_response(redirect(url_for('driver_page', lastname=lastname, firstname=firstname)))
                response.set_cookie('driver_access_key_time', str(time.time()), domain='127.0.0.1')
                logger.info('driver access granted with key and cookie set')
                return response
            else:
                logger.debug('wrong key was entered')
                response = make_response(render_template('error_page_template.html', main_message='Incorrect key', sub_message='The key you entered was incorrect. Please try again.'))
                response.status_code = 203
                return response
        except IndexError as e:
            # there is only one key in the database
            logger.debug('IndexError: {}'.format(e))
            logger.debug('Most likely on first key')
            if (request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key) or (request.form['key'] == os.environ.get('PERM_TEST_KEY')):
                # if its right, set the cookie
                app.__setattr__('driver_access_flag', True)
                response = make_response(redirect(url_for('driver_page', lastname=lastname, firstname=firstname)))
                response.status_code = 302
                response.set_cookie('driver_access_key_time', str(time.time()), domain='127.0.0.1')
                return response

            else:
                response = make_response(render_template('error_page_template.html', main_message='Incorrect key', sub_message='The key you entered was incorrect. Please try again.'))
                response.status_code = 203
                return response

        except Exception as e:
            logger.critical('Critical error: {}'.format(e))
            return 'Critical error: {}'.format(e)



@app.route('/register-driver', methods=['GET', 'POST'])
@app.route('/registerdriver', methods=['GET', 'POST'])
@app.route('/registeruser', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
@app.route('/register-user', methods=['GET', 'POST'])
def register_user_page():
    # updating the auth keys
    if request.method == 'GET':
        if (datetime.datetime.now() - AuthKey.query.order_by(AuthKey.index.desc()).first().date_created).days > 29:
            new_auth_key = AuthKey(auth_key=secrets.token_hex(16))
            db.session.add(new_auth_key)
            db.session.commit()
        
        message = request.args.get('message')
        if message is None:
            message = 'Register to be a driver for team 422!'
        return render_template('driver_sign_up_template.html', message=message)

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
            if Driver.query.filter_by(first_name = driver_info['first_name'], last_name = driver_info['last_name']).count() > 0:
                # driver already exists, let the user know
                logger.debug('driver already exists')
                return render_template('driver_sign_up_template.html', message='A person with that name already exists in the database.')
            new_driver = Driver(**driver_info)
            db.session.add(new_driver)
            db.session.commit()
            logger.info(f'New driver added to database: {new_driver}')

        except Exception as e: # im sorry :(
            logger.info(e)
            try:
                _ = int(request.form['numberofseats'])
            except Exception as e:
                return render_template('driver_sign_up_template.html', message='Max number of passengers must be an integer')
            return render_template('driver_sign_up_template.html', message='An error occurred. Make sure that all inputs are valid.')
        
        # if they got here, it was a success!
        return render_template('error_page_template.html', main_message='Success!', sub_message='Thank you for helping team 422!')


@app.route('/admin', methods=['GET', 'POST'])
def admin_login_page():
    """
    Admin login page
    """
    if request.method == 'GET':
        return render_template('admin.html', message='Please enter the admin credentials.')
    if request.method == 'POST':
        # validating login
        username = request.form['username']
        password = request.form['password']
        if username == os.environ['ADMIN_USERNAME'] and password == os.environ['ADMIN_PASSWORD']: # returning the valid auth keys -- this is pretty awful
            auth_keys = AuthKey.query.order_by(AuthKey.date_created).all()
            return_list = []
            return_list_2 = []

            for item in auth_keys:
                return_list.append(item.key)
                return_list_2.append(item.date_created) 
            return (f'Valid auth keys: {return_list} <br> Date created: {return_list_2}')

        else:
            # login was incorrect
            response = make_response(render_template('admin.html', message='Incorrect username or password.'))
            response.status_code = 203
            return response


@app.route('/')
@app.route('/home')
def home_page():
    """
    Home page
    """
    return render_template('home.html')



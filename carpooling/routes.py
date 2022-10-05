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

                
    return render_template('driver_page_template.html', **driver_info)



@app.route('/get-driver-access/<lastname>/<firstname>', methods=['GET'])
def get_driver_access(lastname, firstname):
    logger.info('get_driver_access')
    if request.method == 'GET':
        return render_template('get_driver_access_template.html', lastname=lastname, firstname=firstname)

@app.route('/verify-driver-access/<lastname>/<firstname>', methods=['POST'])
def verify_driver_permission(lastname, firstname):
    if request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).first().key or request.form['key'] == AuthKey.query.order_by(AuthKey.index.desc()).all()[1].key:
        app.__setattr__('driver_access_flag', True)
        response = make_response(redirect(url_for('driver_page', lastname=lastname, firstname=firstname)))
        response.set_cookie('driver_access_flag_time', str(time.time()))
        logger.info('driver access granted')
        return response
    else:
        return render_template('error_page_template.html', main_message='Incorrect key', sub_message='The key you entered was incorrect. Please try again.')


@app.route('/')
@app.route('/home')
def home_page():
    """
    Home page
    """
    return render_template('home.html')

@app.route('/handle_form', methods=['GET', 'POST'])
def handle_form():
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
                raise PersonAlreadyExistsException('A person with that name already exists.')
            new_driver = Driver(**driver_info)
            db.session.add(new_driver)
            db.session.commit()
            logger.info(f'New driver added to database: {new_driver}')
        except PersonAlreadyExistsException as e:
            logger.info(e)
            return redirect(url_for("register_user_page", message='A person with that name already exists.'))
        except Exception as e:
            logger.info(e)
            return redirect(url_for("register_user_page", message='Something went wrong. Make sure that all inputs are valid.'))
        return render_template('error_page_template.html', main_message='Success!', sub_message='Thank you for helping team 422!')
    else: 
        return render_template('error_page_template.html', main_message='Go Away', sub_message='You should not be here.')


@app.route('/register-driver')
@app.route('/registerdriver')
@app.route('/registeruser')
@app.route('/register')
@app.route('/register-user')
def register_user_page():
    # updating the auth keys
    if (datetime.datetime.now() - AuthKey.query.order_by(AuthKey.index.desc()).first().date_created).days > 29:
        new_auth_key = AuthKey(auth_key=secrets.token_hex(16))
        db.session.add(new_auth_key)
        db.session.commit()
    
    message = request.args.get('message')
    if message is None:
        message = 'Register to be a driver for team 422!'
    return render_template('driver_sign_up_template.html', message=message)


@app.route('/admin', methods=['GET', 'POST'])
def admin_login_page():
    """
    Admin login page
    """
    return render_template('admin.html')

@app.route('/verify-admin', methods=['POST'])
def verify_admin():
    """
    Verifies the admin key and sets the admin_access_flag to True if the key is correct.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == os.environ['ADMIN_USERNAME'] and password == os.environ['ADMIN_PASSWORD']:
            app.admin_access_flag = True
            return redirect(url_for('valid_auth_keys_page'))
        else:
            return render_template('error_page_template.html', main_message='Incorrect username or password', sub_message='The username or password you entered was incorrect. Please try again.')


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
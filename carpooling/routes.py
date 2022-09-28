from lib2to3.pgen2 import driver
from carpooling import db
from carpooling import app
from carpooling.models import Driver
import logging
import time
from flask import render_template, request, redirect, url_for

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/driver/<lastname>/<firstname>')
def driver_page(lastname, firstname):
    logging.debug('here')
    try:
        driver = Driver.query.filter_by(last_name=lastname, first_name=firstname).one()
    except:
        return 'No driver was found.'
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



@app.route('/')
@app.route('/home')
def home_page():
    return f"did you mean to register? {url_for('register_user_page')}"
    # with open ('carpooling/templates/mechtech_template.html') as f:
    #     return f.read()

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
                raise Exception('A person with that name already exists.')
            new_driver = Driver(**driver_info)
            db.session.add(new_driver)
            db.session.commit()
            logger.info(f'New driver added to database: {new_driver}')
        except Exception as e:
            logger.info(e)
            if e == Exception('A person with that name already exists.'):
                return redirect(url_for("register_user_page", message='A person with that name already exists.'))
            else:
                return redirect(url_for("register_user_page", message='Something went wrong. Make sure that all inputs are valid.'))
        return 'Submitted Successfully! Thank you for helping the team!'
    else: 
        return 'wrong page'

    
@app.route('/register-driver')
@app.route('/registerdriver')
@app.route('/registeruser')
@app.route('/register')
@app.route('/register-user')
def register_user_page():
    message = request.args.get('message')
    if message is None:
        message = 'Register to be a driver for team 422!'
    return render_template('driver_sign_up_template.html', message=message)
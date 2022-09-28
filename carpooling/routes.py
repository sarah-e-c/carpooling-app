from carpooling import db
from carpooling import app
from carpooling.models import Driver
import logging
import time
from flask import render_template

logging.basicConfig(level=logging.DEBUG)

@app.route('/driver/<lastname>/<firstname>')
def driver_page(lastname, firstname):
    logging.debug('here')
    driver = Driver.query.filter_by(last_name=lastname, first_name=firstname).one()
    driver_info = {'lastname': driver.last_name.capitalize(),
                    'firstname':  driver.last_name.capitalize(),
                    'car_type_1': driver.car_type_1, # driver.car_type_1
                    'car_color_1': driver.car_color_1,
                    'car_type_2': driver.car_type_2,
                    'car_color_2': driver.car_color_2,
                    'car_type_3': driver.car_type_3,
                    'car_color_3': driver.car_color_3,
                    'number_seats': driver.num_seats,
                    'Phone number': driver.phone_number,
                    'Email Address': driver.email_address,
                    'Student or Parent': driver.student_or_parent}
    return render_template('driver_page_template.html', **driver_info)


#@app.route('/')
@app.route('/home')
def home_page():
    return render_template('driver_page_template.html')
    # with open ('carpooling/templates/mechtech_template.html') as f:
    #     return f.read()





@app.route('/register-user')
def register_user_page():
    pass 
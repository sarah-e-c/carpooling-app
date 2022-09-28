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
                    'firstname': driver.first_name.capitalize(),
                    'car_type_1': driver.car_type_1,
                    'Car 1 Color': driver.car_color_1,
                    'Car 2 Type': driver.car_type_2,
                    'Car 2 Color': driver.car_color_2,
                    'Car 3 Type': driver.car_type_3,
                    'Car 3 Color': driver.car_color_3,
                    'Number of seats': driver.num_seats,
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
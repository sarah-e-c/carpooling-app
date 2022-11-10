"""
Command to fill the database with fake people.
"""
import logging
import requests
import click
from flask.cli import with_appcontext
from carpooling import db
from carpooling.models import Passenger, Address, User, Driver, Event, CarpoolSolution, GeneratedCarpool, GeneratedCarpoolPart
from werkzeug.security import generate_password_hash
import random

@click.command(name='fill-fake-people')
@click.argument('number_of_people')
@with_appcontext
def fill_fake_people_command(number_of_people):
    """
    Method to fill the database with fake people.
    """
    source = requests.get(f'https://randomuser.me/api/?nat=us&results={number_of_people}').json()
    for i in range(len(source['results'])):
        new_address = Address(
                address_line_1=str(source['results'][0]['location']['street']['number']) +' ' +source['results'][i]['location']['street']['name'],
                address_line_2= None,
                city=source['results'][i]['location']['city'],
                state=source['results'][i]['location']['state'],
                zip_code=source['results'][i]['location']['postcode'],
                latitude=source['results'][i]['location']['coordinates']['latitude'],
                longitude=source['results'][i]['location']['coordinates']['longitude'],
                code = 0,
            )
        db.session.add(new_address)
        new_driver = Driver(
            first_name=source['results'][i]['name']['first'].lower(),
            last_name=source['results'][i]['name']['last'].lower(),
            email_address=source['results'][i]['email'],
            phone_number=source['results'][i]['phone'],
            emergency_contact_number=source['results'][i]['cell'],
            emergency_contact_relation='friend',
            car_type_1 = 'Mazda 6',
            car_color_1 = 'red',
            car_color_2 = 'blue',
            car_type_2 = 'Honda Civic', 
            num_seats = 3,
            region_name='West Henrico',
            student_or_parent = 'Student',
            address=[new_address],
            address_line_1=str(source['results'][0]['location']['street']['number']) +' ' +source['results'][i]['location']['street']['name'],
            address_line_2= None,
            city=source['results'][i]['location']['city'],
            zip_code=source['results'][i]['location']['postcode'],
        )
        db.session.add(new_driver)
    
        new_passenger = Passenger(
            first_name=source['results'][i]['name']['first'].lower(),
            last_name=source['results'][i]['name']['last'].lower(),
            email_address=source['results'][i]['email'],
            phone_number=source['results'][i]['phone'],
            emergency_contact_number=source['results'][i]['cell'],
            emergency_contact_relation='friend',
            region_name='West Henrico',
            address_line_1=str(source['results'][0]['location']['street']['number']) +' ' +source['results'][i]['location']['street']['name'],
            address_line_2= None,
            city=source['results'][i]['location']['city'],
            zip_code=source['results'][i]['location']['postcode'],

            address=[new_address])
        
        db.session.add(new_passenger)
    
        new_user = User(
            first_name=source['results'][i]['name']['first'].lower(),
            last_name=source['results'][i]['name']['last'].lower(),
            password = generate_password_hash('password'),
            driver_profile = new_driver,
            passenger_profile = new_passenger,
            is_admin = 0
        )
        db.session.add(new_user)
        db.session.commit()
    
    
        logging.info('added driver: ' + new_driver.first_name + ' ' + new_driver.last_name)
    
    

        
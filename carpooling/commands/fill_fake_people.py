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
import logging
#from random_address import real_random_address_by_state

logger = logging.getLogger(__name__)


real_random_address_by_state = None #temporarily disabled

@click.command(name='fill-fake-people')
@click.argument('number_of_people')
@with_appcontext
def fill_fake_people_command(number_of_people):
    """
    Method to fill the database with fake people.
    """
    db.create_all()
    source = requests.get(f'https://randomuser.me/api/?nat=us&results={number_of_people}').json()


    for i in range(len(source['results'])):
        address_source  = real_random_address_by_state('CA')
        new_address = Address(
                address_line_1=address_source['address1'],
                address_line_2= address_source['address2'],
                city=address_source['city'],
                state=address_source['state'],
                zip_code=address_source['postalCode'],
                latitude=address_source['coordinates']['lat'],
                longitude=address_source['coordinates']['lng'],
                code = 0,
            )
        db.session.add(new_address)
        seed = random.randint(0, 1)
        logger.info(seed)
        if seed == 1: # is driver
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
                address_line_1=address_source['address1'],
                address_line_2= address_source['address2'],
                city=address_source['city'],
                zip_code=address_source['postalCode'],
            )
            db.session.add(new_driver)
        else:
            new_driver = None
    
        new_passenger = Passenger(
            first_name=source['results'][i]['name']['first'].lower(),
            last_name=source['results'][i]['name']['last'].lower(),
            email_address=source['results'][i]['email'],
            phone_number=source['results'][i]['phone'],
            emergency_contact_number=source['results'][i]['cell'],
            emergency_contact_relation='friend',
            region_name='West Henrico',
            address_line_1=address_source['address1'],
            address_line_2= address_source['address2'],
            city=address_source['city'],
            zip_code=address_source['postalCode'],
            address=[new_address])
        
        db.session.add(new_passenger)
    
        new_user = User(
            first_name=source['results'][i]['name']['first'].lower(),
            last_name=source['results'][i]['name']['last'].lower(),
            password = generate_password_hash('password'),
            driver_profile = new_driver,
            passenger_profile = new_passenger,
            is_admin = 2
        )
        db.session.add(new_user)
        db.session.commit()

        if seed == 1:
            logging.info('added driver: ' + new_driver.first_name + ' ' + new_driver.last_name)
        else:
            logging.info('added passenger: ' + new_passenger.first_name + ' ' + new_passenger.last_name)
    
    

        
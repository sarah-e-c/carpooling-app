from carpooling import app, db
from carpooling import models
import os

from carpooling import routes
import logging 
import secrets # lkj
import datetime




logger = logging.getLogger(__name__)


def test_set_up():
    logging.basicConfig(level=logging.DEBUG)
    if len(db.engine.table_names()) < 100:
        logger.info('first time setup')
        try:
            models.AuthKey.query.delete() # only for testing
            models.Driver.query.delete() # only for testing
            models.Event.query.delete() # only for testing
            models.Carpool.query.delete() # only for testing
            models.Region.query.delete() # only for testing
            models.Passenger.query.delete() # only for testing
            models.User.query.delete() # only for testing
        except:
            pass
    
        db.create_all()
        first_key = models.AuthKey(
            key = secrets.token_hex(4)
        )

        test_man = models.Driver(
            last_name = 'test',
            first_name = 'test',
            car_type_1 = 'test',
            car_color_1 = 'test',
            car_type_2 = 'test',
            car_color_2 = 'test',
            num_seats = 1,
            phone_number = 'test',
            email_address = 'test',
            student_or_parent = 'student',
            emergency_contact_number = 'test',
            emergency_contact_relation = 'test',
            num_years_with_license = 1
        )

        test_event = models.Event(
            event_name = 'test',
            event_start_time = datetime.datetime.now() + datetime.timedelta(days=1),
            event_end_time = datetime.datetime.now() + datetime.timedelta(days=1),
            event_date = datetime.datetime.now() + datetime.timedelta(days=1),
            event_location = 'test'
        )

        test_region = models.Region(
            name = 'test',
            dropoff_location = 'test'
        )

        test_carpool = models.Carpool(
            driver_index = 1,
            num_passengers = 5,
            event_index = 1,
            destination = 'test',
            region_name = 'test'
        )

        test_carpool_2 = models.Carpool(
            num_passengers = 3,
            event_index = 1,
            destination = 'test',
            region_name = 'test'
        )

        test_passenger = models.Passenger(
            last_name = 'test',
            first_name = 'test',
            phone_number = 'test',
            email_address = 'test',
            emergency_contact_number = 'test',
            emergency_contact_relation = 'test',
            region_name = 'test',
        )

        test_passenger_2 = models.Passenger(
            last_name = 'test2',
            first_name = 'test2',
            phone_number = 'test',
            email_address = 'test',
            emergency_contact_number = 'test',
            emergency_contact_relation = 'test',
            region_name = 'test',
        )

        test_passenger_3 = models.Passenger(
            last_name = 'test3',
            first_name = 'test3',
            phone_number = 'test',
            email_address = 'test',
            emergency_contact_number = 'test',
            emergency_contact_relation = 'test',
            region_name = 'test',
        )

        test_carpool.passengers.append(test_passenger)
        test_carpool.passengers.append(test_passenger_2)
        test_carpool.passengers.append(test_passenger_3)

        # db.session.add(test_passenger)
        # db.session.add(test_passenger_2)
        # db.session.add(test_passenger_3)


        db.session.add(test_carpool)
        db.session.add(test_carpool_2)


        db.session.add(test_region)
        db.session.add(test_event)
        db.session.add(first_key)
        db.session.add(test_man)
        db.session.commit()
        logger.info('first time setup complete')

def initial_set_up():
    """
    Method to intially set up the database
    """
    models.AuthKey.query.delete() 
    first_key = models.AuthKey(
        key = secrets.token_hex(4)
    )
    models.Carpool.query.delete()
    models.User.query.delete()
    models.Driver.query.delete()
    models.Passenger.query.delete()
    models.Event.query.delete()
    
    models.Region.query.delete()
    south_region = models.Region(
        name='Prince George-Petersburg-Colonial Heights-South Chesterfield',
        dropoff_location='Southpark Mall',
        color='#8B0000',
    )
    henrico_region = models.Region(
        name='Henrico and Northern Areas',
        dropoff_location='Short Pump Town Center',
        color='#FF8C00',
    )

    eastern_region = models.Region(
        name='New Kent-Charles City-East Prince George',
        dropoff_location='New Kent High School',
        color='#FF00FF',
    )

    richmond_region = models.Region(
        name='Richmond',
        dropoff_location='Richmond International Raceway',
        color='#FFFF00',
    )

    chesterfield_region = models.Region(
        name='Central Chesterfield',
        dropoff_location='Chesterfield Towne Center',
        color='#00FF00',
    )

    west_region = models.Region(
        name='Western Counties',
        dropoff_location='Liberty University',
        color='#008000',
    )

    db.session.add(south_region)
    db.session.add(henrico_region)
    db.session.add(richmond_region)
    db.session.add(west_region)
    db.session.add(eastern_region)
    db.session.add(chesterfield_region)
    db.session.add(first_key)
    db.session.commit()

def make_admin(first_name, last_name):
    """
    Method you can hard code to make someone admin
    """
    user = models.User.query.filter_by(first_name=first_name, last_name=last_name).first()
    user.is_admin = 2
    db.session.commit()

if __name__ == '__main__': # run app
    with app.app_context() as f:
        # db.create_all()
        # initial_set_up()
        make_admin('sarah', 'crowder')
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
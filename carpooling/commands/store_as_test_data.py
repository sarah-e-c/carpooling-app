"""
Command to freeze the current state of the database as test data.
"""

import json
import os
import sys

from carpooling import db
from carpooling import models
from flask.cli import with_appcontext
import click

import logging

logger = logging.getLogger(__name__)

@click.command('store-as-test-data')
@with_appcontext
def store_as_test_data_command():
    with open('testing/example_data/setup_data/people_data.json', 'w') as f:
        f.write(json.dumps(get_people_data(), indent=4))

    with open('testing/example_data/setup_data/events_data.json', 'w') as f:
        f.write(json.dumps(get_events_data(), indent=4))

def get_people_data() ->dict:
    users = models.User.query.all()
    people_dict = {}
    for user in users:
        person_dict = {}
        person_dict['first_name'] = user.first_name
        person_dict['last_name'] = user.last_name
        person_dict['email_address'] = user.email_address
        person_dict['phone_number'] = user.phone_number
        if user.driver_profile is not None:
            person_dict['is_driver'] = True
            person_dict['num_seats'] = user.num_seats
            person_dict['car_type_1'] = user.car_type_1
            person_dict['car_type_2'] = user.car_type_2
            person_dict['car_color_1'] = user.car_color_1
            person_dict['car_color_2'] = user.car_color_2
            person_dict['student_or_parent'] = user.student_or_parent
        else:
            person_dict['is_driver'] = False
            person_dict['num_seats'] = None
            person_dict['car_type_1'] = None
            person_dict['car_type_2'] = None
            person_dict['car_color_1'] = None
            person_dict['car_color_2'] = None
            person_dict['student_or_parent'] = None

        person_dict['emergency_contact_number'] = user.emergency_contact_number
        person_dict['emergency_contact_relation'] = user.emergency_contact_relation
        person_dict['extra_information'] = user.extra_information
        person_dict['region_name'] = user.region_name
        person_dict['is_admin'] = user.is_admin
        
        person_dict['address'] = {
            'latitude': user.get_latitude(),
            'longitude': user.get_longitude(),
            'code': user.get_address_code(),
            'address_line_1': user.get_address_line_1(),
            'city': user.get_city(),
            'state': user.get_state(),
            'zip_code': user.get_zip_code(),
            'address_line_2': user.get_address_line_2(),
        }
        person_dict['password'] = user.password
        
        people_dict[user.id] = person_dict
    logger.info(f'people_dict: {people_dict}')
    return people_dict
        
def get_events_data():
    events_dict = {}
    events = models.Event.query.all()
    for event in events:
        event_dict = {}
        event_dict['event_name'] = event.name
        event_dict['event_description'] = event.description
        event_dict['event_start_time'] = event.start_time.strftime('%I:%M:%S')
        event_dict['event_end_time'] = event.end_time.strftime('%I:%M:%S')
        event_dict['event_date'] = event.date.strftime('%Y-%m-%d')
        event_dict['event_location'] = event.location
        event_dict['destination_id'] = event.destination_id
        events_dict[event.index] = event_dict
    return events_dict

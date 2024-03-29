import datetime
import random

from flask import current_app
from flask.cli import with_appcontext

from carpooling import db
from carpooling import models
from carpooling import create_app
import secrets
import click
import json


@click.command('init-db')
@click.argument('is_testing', default=False)
@with_appcontext
def init_db_command(is_testing=False):
    db.drop_all()
    db.create_all()
    if is_testing:
        create_test_data()
    print('all done!')

def init_db_command_for_code(is_testing=False):
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        if is_testing:
            create_test_data()
    print('all done!')


def create_test_data(people_filepath=None, events_filepath=None, signup_filepath=None):

    # filling in the people
    if people_filepath is None:
        people_filepath='testing/example_data/setup_data/people_data.json'
    with open(people_filepath) as f:
        data = json.load(f)
    
    organization = models.Organization(name="Test Organization", access_key=secrets.token_urlsafe(8))
    db.session.add(organization)
    db.session.commit()
    destination_address = models.Address(
        latitude = 37.5579166667,
        longitude = -77.27135,
        code=0,
        address_line_1 = '1000 N Lombardy Street',
        city = 'Richmond',
        state = 'VA',
        zip_code = '23220',
    )
    first_destination = models.Destination(
        name='Maggie L. Walker Governor\'s School',
        address=destination_address,
        organization=organization
    )
    db.session.add(first_destination)
    db.session.commit()
    for id, person in data.items():
        new_address = models.Address(
            latitude = person['address']['latitude'],
            longitude = person['address']['longitude'],
            code = random.random(),  # person['address']['code'],
            address_line_1 = person['address']['address_line_1'],
            city = person['address']['city'],
            state = person['address']['state'],
            zip_code = person['address']['zip_code'],
            address_line_2 = person['address']['address_line_2'],
        )
        new_user = models.User(
            first_name=person['first_name'],
            last_name=person['last_name'],
            email_address=person['email_address'],
            phone_number=person['phone_number'],
            num_seats=person['num_seats'],
            car_type_1=person['car_type_1'],
            car_type_2=person['car_type_2'],
            car_color_1=person['car_color_1'],
            car_color_2=person['car_color_2'],
            emergency_contact_number=person['emergency_contact_number'],
            emergency_contact_relation=person['emergency_contact_relation'],
            extra_information=person['extra_information'],
            student_or_parent=person['student_or_parent'],
            addresses=[new_address],
            password=person['password']
        )
        db.session.add(new_user)
        new_user.organizations.append(organization)

    db.session.commit()

    # creating first destination
    if events_filepath is None:
        events_filepath='testing/example_data/setup_data/events_data.json'
    with open(events_filepath) as f:
        data = json.load(f)
    for id, event in data.items():

        new_event = models.Event(
            name=event['event_name'],
            description=event['event_description'],
            date=datetime.datetime.strptime(event['event_date'], '%Y-%m-%d'),
            start_time=datetime.datetime.strptime(event['event_start_time'], '%H:%M:%S'),
            end_time=datetime.datetime.strptime(event['event_end_time'], '%H:%M:%S'),
            location=event['event_location'],
            destination=models.Destination.query.get(event['destination_id']),
            destination_id=event['destination_id'],
            organization=organization
        )
        db.session.add(new_event)
    db.session.commit()

    # filling in the signups
    if signup_filepath is None:
        signup_filepath='testing/example_data/setup_data/example_signup_csv.csv'
    with open(signup_filepath, 'r') as f:
        data = f.readlines()
    for line in data[1:]:
        line = line.strip()
        line = line.split(',')
        user= models.User.query.filter_by(first_name=line[0], last_name=line[1]).first()
        def parse_response(response: str) -> bool:
            if (response.lower() == 'yes') or (response.lower() == 'y') or (response.lower() == 'true') or (response.lower() == 't'):
                return True
            elif (response.lower() == 'no') or (response.lower() == 'n') or (response.lower() == 'false') or (response.lower() == 'f'):
                return False
            else:
                return False
            
        new_signup = models.EventCarpoolSignup(
            event=new_event,
            user=user,
            willing_to_drive=parse_response(line[2]),
            needs_ride=parse_response(line[3]),
        )
        db.session.add(new_signup)
    db.session.commit()

# def create_first_key():
#     first_key = models.AuthKey(
#         key = secrets.token_hex(4)
#     )
#     db.session.add(first_key)
#     db.session.commit()

def create_first_destination():
    destination_address = models.Address(
        latitude = 37.5579166667,
        longitude = -77.27135,
        code=0,
        address_line_1 = '1000 N Lombardy Street',
        city = 'Richmond',
        state = 'VA',
        zip_code = '23220',
    )
    first_destination = models.Destination(
        name='Maggie L. Walker Governor\'s School',
        address=destination_address,
    )
    db.session.add(first_destination)
    db.session.commit()
    return first_destination

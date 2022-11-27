import carpooling.celeryapp as celeryapp
from carpooling.logic.carpool_matching import evaluate_best_solution_one_way
from carpooling.logic.carpool_matching.data_classes import DRIVER_WAITING_TIME
from carpooling.logic.carpool_matching.general_functions import load_people_from_sql
from carpooling.models import Event, AuthKey, User, Address, CarpoolSolution, GeneratedCarpool, GeneratedCarpoolPart
from flask import current_app
import logging
import time
from carpooling import mail
from flask_mail import Message
import datetime
import secrets
import requests
from io import StringIO

FROM_BUILD_TYPE = 'from'
TO_BUILD_TYPE = 'to'
logger = logging.getLogger(__name__)

# i have no idea why this is necessary and why it works PLEASE DO NOT TOUCH
celery = celeryapp.celery
db_session = celeryapp.db_session
if celery is None:
    # celery = celeryapp.create_celery_app(app)
    # celeryapp.celery = celery
    logger.debug('registered task blueprints in celery tasks module')
else:
    logger.debug('celery already exists')


@celery.task()
def test_task():
    print('test task started')
    time.sleep(5)
    print('test task finished')
    return 'test task'


@celery.task
def send_async_email(to, subject, message):
    """
    Function for sending emails.
    to: recipient email.
    subject: subject of the email.
    message: message of the email.
    """
    logger.info(current_app.config['MAIL_SERVER'])
    try:
        msg = Message(subject, sender=(current_app.config['MAIL_USERNAME'], 'Mech Techs Carpooling'),
                      recipients=[to])
        msg.body = message
        mail.send(msg)
        logger.info('Email sent to %s', to)
    except Exception as e:
        logger.debug(e)
        logger.warning('Email failed to send to {}, probably due to an invalid email address'.format(to))


@celery.task
def send_async_email_to_many(to: list, subject: str, message: str):
    """
    Function for sending emails.
    to: list of recipient emails.
    subject: subject of the email.
    message: message of the email.
    """
    logger.info(current_app.config['MAIL_SERVER'])
    if len(to) < 1:
        raise AssertionError
    try:
        msg = Message(subject, sender=(current_app.config['MAIL_USERNAME'], 'Mech Techs Carpooling'), recipients=to)
        msg.body = message
        mail.send(msg)
        logger.info('Email sent to %s', to)
    except AssertionError as e:
        logger.debug(e)
        logger.info('Email failed to send because of empty recipient list')
    except Exception as e:
        logger.debug(e)
        logger.warning('Email failed to send to {}, probably due to an invalid email address'.format(to))


@celery.task(name='maintenance_task')
def maintenance_task():
    # checking if an event should have a carpooling build done for it
    events = Event.query.filter(Event.date > datetime.datetime.now()).all()
    logger.debug('fetched events from database {}'.format(events))

    for event in events:
        is_within_2_days = event.date - datetime.datetime.now() < datetime.timedelta(days=2)
        # is_within_2_days = True
        if is_within_2_days and event.needs_matching_build_to:
            build_address_match_one_way.delay(event.index, build_type=TO_BUILD_TYPE)  # creating a carpooling build
        if is_within_2_days and event.needs_matching_build_from:
            build_address_match_one_way.delay(event.index, build_type=FROM_BUILD_TYPE)  # creating a carpooling build

    logger.debug('started building carpooling solutions for events if needed')

    # checking if an auth key is needed
    if AuthKey.query.order_by(AuthKey.index.desc()).first().date_created < datetime.datetime.now() - datetime.timedelta(
            days=28):
        new_auth_key = AuthKey(key=secrets.token_hex(4))
        db_session.session.add(new_auth_key)
        db_session.commit()

    # making sure that there is no unidentified addresses in the database, if they can't be identified, the driver is notified
    problematic_users = [user for user in User.query.all() if user.addresses[0].latitude is None]
    if len(problematic_users) > 0:
        logger.debug('found {} users with no addresses'.format(len(problematic_users)))

    for user in problematic_users:
        try:
            logger.info('getting address for user {}'.format(user))
            source = requests.get(
                f"https://maps.googleapis.com/maps/api/geocode/json?address={user.get_address_line_1().replace(' ', '%20') + '%20' + user.get_city() + '%20VA'}&key=AIzaSyD_JtvDeZqiy9sxCKqfggODYMhuaeeLjXI")
            if source.json()['status'] == 'OK':
                new_address = Address(address_line_1=user.get_address_line_1(),
                                      address_line_2=user.addresses[0].address_line_2,
                                      latitude=source.json()['results'][0]['geometry']['location']['lat'],
                                      longitude=source.json()['results'][0]['geometry']['location']['lng'],
                                      place_id=source.json()['results'][0]['place_id'],
                                      city=user.get_city(),
                                      state='VA', )
                db_session.add(new_address)
                db_session.commit()
                # TODO this doesn't work with the new address model

                user.address_id = new_address.id
                if user.num_seats is not None:
                    user.address_id = new_address.id
                db_session.commit()
                logger.info(f'identified address for user {user.id} successfully!')
        except Exception as e:
            logger.info(f'failed to identify address for user {user.id}')
            logger.debug(e)
            send_async_email.delay(user.email, 'Address Identification Failed',
                                   'We were unable to identify your address. If you would like to use address services, then please make sure that you have entered a valid address in your profile.')

    return "maintenance task finished"


@celery.task()
def build_address_match_one_way(event_id, build_type):
    """
    Types are 'from' and 'to'
    """
    logger.info('started build task with event id {} and build type {}'.format(event_id, build_type))
    # first thing is to set the flag to false
    event = Event.query.get(event_id)
    set_flags.delay(event_id, build_type, False)

    try:
        people = load_people_from_sql(event_id)
        solution = evaluate_best_solution_one_way(people, event.destination.address_id, build_type,
                                                  return_='best_solution', use_placeid=False)
        # putting the solution into the database
        if solution.type == 'to':
            for carpool in solution.carpools:
                route_specific_times = [event.start_time]
                last_time = event.start_time
                for i, route in enumerate(carpool.route[::-1]):
                    driver_waiting_time_taken = datetime.timedelta(minutes=DRIVER_WAITING_TIME)
                    last_route_time_taken = datetime.timedelta(seconds=carpool.route_times[
                        len(carpool.route_times) - 1 - i])  # Google Maps gives seconds for some reason
                    route_specific_times.append(last_time - driver_waiting_time_taken - last_route_time_taken)
                    last_time = route_specific_times[-1]
                route_specific_times = route_specific_times[::-1]
                carpool.__setattr__('route_specific_times', route_specific_times)

        elif solution.type == 'from':
            for carpool in solution.carpools:
                route_specific_times = [event.end_time]
                last_time = event.end_time
                for i, route in enumerate(carpool.route):
                    driver_waiting_time_taken = datetime.timedelta(minutes=DRIVER_WAITING_TIME)
                    last_route_time_taken = datetime.timedelta(seconds=carpool.route_times[i])
                    route_specific_times.append(last_time + driver_waiting_time_taken + last_route_time_taken)
                    last_time = route_specific_times[-1]

                carpool.__setattr__('route_specific_times', route_specific_times)

        # writing the solutions to the database
        new_solution = CarpoolSolution(
            utility_value=solution.total_utility_value,
            event_id=event.index,
            is_best=False,
            type=build_type
        )
        celery.__getattribute__('to_add_to_session').append(new_solution)

        for carpool in solution.carpools:
            driver_id = User.query.get(
                carpool.driver.id_).id
            new_carpool = GeneratedCarpool(
                carpool_solution=new_solution,
                from_address_id=carpool.route[0],
                to_address_id=carpool.route[-1],
                driver_id=driver_id,  # yes this is bad
                event_id=event.index,
                from_time=carpool.route_specific_times[0],
                to_time=carpool.route_specific_times[-1],
            )
            for passenger in carpool.passengers:
                new_carpool.passengers.append(User.query.get(passenger.id_))
            celery.__getattribute__('to_add_to_session').append(new_carpool)
            for i in range(len(carpool.route) - 1):
                new_part = GeneratedCarpoolPart(
                    generated_carpool=new_carpool,
                    from_address_id=carpool.route[i],
                    to_address_id=carpool.route[i + 1],
                    driver_id=driver_id,  # yes this is bad
                    idx=i,
                    passengers=new_carpool.passengers,
                    from_time=carpool.route_specific_times[i],
                    to_time=carpool.route_specific_times[i + 1],
                )
                celery.__getattribute__('to_add_to_session').append(new_part)

    except Exception as e:
        # Setting the flag back to true so that the task will be run again
        set_flags.delay(event_id, build_type, True)
        raise e


@celery.task()
def set_flags(event_id, build_type: str, flag: bool):
    """
    Task to set the flags from the session. Is built like this because it's hard to commit
    to the database from inside a celery task, but it automatically does it on teardown.
    It's either that or I missed something very obvious.
    :param event_id: the index of the event to set the flag for (yes I know I need to rename this)
    :param build_type: the type of build to set the flag for. Either 'from' or 'to', otherwise it will raise an error
    :param flag: the flag to set it to.
    """
    event = Event.query.get(event_id)
    if build_type == FROM_BUILD_TYPE:
        event.needs_matching_build_from = flag
    elif build_type == TO_BUILD_TYPE:
        event.needs_matching_build_to = flag
    else:
        raise AssertionError
    return "flag set"


@celery.task()
def get_people_string_io():
    # example  for the tes 
    return StringIO("first name, last name, willing to drive, needs ride \n Sarah, Crowder, yes, yes")

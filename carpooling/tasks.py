import carpooling.celeryapp as celeryapp
from carpooling.models import Event, AuthKey, User, Address
from flask import current_app
import logging
import time
from carpooling import mail
from flask_mail import Message
import datetime
import secrets
import requests
from io import StringIO

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


@celery.task()
def maintenance_task():
    # checking if an event should have a carpooling build
    events = Event.query.filter_by(Event.date > datetime.datetime.now()).all()
    for event in events:
        if datetime.datetime.now() > event.date - datetime.timedelta(days=2):
            build_address_match.delay(event.id)  # creating a carpooling build
            pass

    # checking if an auth key is needed
    if AuthKey.query.order_by(AuthKey.index.desc()).first().date_created < datetime.datetime.now() - datetime.timedelta(
            days=28):
        new_auth_key = AuthKey(key=secrets.token_hex(4))
        db_session.session.add(new_auth_key)
        db_session.commit()

    # making sure that there is no unidentified addresses in the database, if they can't be identified, the driver is notified
    problematic_users = User.query.filter(User.address_id == None).all()

    for user in problematic_users:
        try:
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
def build_address_match():
    # building address match
    pass


@celery.task()
def get_people_string_io():
    # example  for the tes 
    return StringIO("first name, last name, willing to drive, needs ride \n Sarah, Crowder, yes, yes")

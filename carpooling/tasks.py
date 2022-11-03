from carpooling import create_app
import carpooling.celeryapp as celeryapp
from flask import current_app
import logging
import time
from carpooling import mail
from flask_mail import Message

logger = logging.getLogger(__name__)

# i have no idea why this is necessary and why it works PLEASE DO NOT TOUCH
celery = celeryapp.celery
if celery is None:
    app = create_app()
    celery = celeryapp.create_celery_app(app)
    celeryapp.celery = celery
    logger.debug('registered task blueprints in celery tasks module')
else:
    logger.debug('celery already exists')



@celery.task()
def test_task():
    print('test task started')
    time.sleep(5)
    print('test task finished')
    return 'test task'

@celery.task()
def send_async_email(to, subject, message):
    """
    Function for sending emails.
    to: recipient email.
    subject: subject of the email.
    message: message of the email.
    """
    logger.info(current_app.config['MAIL_SERVER'])
    try:
        msg = Message(subject, sender=(current_app.config['MAIL_USERNAME'], 'Mech Techs Carpooling'), recipients=[to])
        msg.body = message
        mail.send(msg)
        logger.info('Email sent to %s', to)
    except Exception as e:
        logger.debug(e)
        logger.warning('Email failed to send to {}, probably due to an invalid email address'.format(to))

@celery.task()
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
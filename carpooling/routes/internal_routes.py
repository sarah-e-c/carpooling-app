"""
Routes that are used only for internal purposes. (Like leaving carpools). Usually only referenced by javascript.
"""

from carpooling import db, mail
from carpooling.models import Event, Carpool,  User
import logging
from carpooling.utils import admin_required
from flask import render_template, request, redirect, url_for, Blueprint
import datetime
from flask_login import login_required, current_user
from flask_mail import Message

internal_blueprint = Blueprint('internal', __name__, template_folder='templates')
logger = logging.getLogger(__name__)

@internal_blueprint.route('/delete-event/<event_index>')
@login_required
def delete_event(event_index):
    """
    Method to delete an event
    """
    try:
        event_to_delete = Event.query.get(event_index)
    except Exception as e:
        logger.debug(e)
        logger.info('Event {} not found'.format(event_index))
        return redirect(url_for('main.events_page'))
    
    # checking that the user is the creator of the event
    if not ((event_to_delete.user == current_user) or (current_user.is_admin > 0)):
        logger.info('A person attempted to delete an event they were not authorized to delete')
        return redirect(url_for('main.events_page'))
    
    # notifying the drivers of the event
    for carpool in event_to_delete.carpools:
        try:
            message = Message (
                subject='Your carpool event has been deleted',
                recipients= [carpool.driver.user[0].passenger_profile.email_address],
                sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                body=f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
            )
            mail.send(message)
            logger.info('Driver {} notified of event deletion'.format(carpool.driver))
        except Exception as e:
            logger.debug(e)
            logger.warning('Driver {} not notified of event deletion, probably due to invalid email address'.format(carpool.driver))
    
    # notifying the passengers of the event
    for carpool in event_to_delete.carpools:
        try:
            message = Message (
                subject='Your carpool event has been deleted',
                recipients= [passenger.passenger_profile.email_address for passenger in carpool.passengers],
                sender=('Mech Techs Carpooling', 'mechtechscaprooling@zohomail.com'),
                body=f"""
                Hello passengers, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
            )
            mail.send(message)
            logger.info('Passengers notified of event deletion')
        except Exception as e:
            logger.debug(e)
            logger.warning('Passengers not notified of event deletion, probably due to an invalid email address')
    
    # deleting the carpools of the event
    for carpool in event_to_delete.carpools:
        db.session.delete(carpool)

    # deleting the event
    db.session.delete(event_to_delete)
    db.session.commit()

    logger.info('Event {} deleted'.format(event_to_delete.event_name))
    return redirect(url_for('main.events_page'))

@internal_blueprint.route('/remove-admin/<user_id>')
@admin_required
def remove_admin(user_id):
    """
    Method to remove someone from admin
    user_id: id of user to remove admin from
    """
    user_to_change = User.query.get(user_id)
    # checking that the person removing is of higher admin than user
    if user_to_change.is_admin >= current_user.is_admin:
        logger.info('User {} {} is of higher admin than user {} {}'.format(current_user.first_name.capitalize(), current_user.last_name.capitalize(), user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
        return redirect(url_for('admin.manage_users_page'))

    if user_to_change.is_admin > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('admin.manage_users_page'))

    user_to_change.is_admin = 0
    db.session.commit()
    logger.info('User {} {} removed from admin'.format(user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('admin.manage_users_page'))

@internal_blueprint.route('/give-admin/<user_id>')
@admin_required
def give_admin(user_id):
    """
    Method to give someone (regular) admin
    """
    user_to_change = User.query.get(user_id)
    # checking that they are not already super admin (that would be bad)
    if user_to_change.is_admin > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('admin.manage_users_page'))

    user_to_change.is_admin = 1
    db.session.commit()
    logger.info('User {} {} given admin'.format(user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('admin.manage_users_page'))

@internal_blueprint.route('/give_super_admin/<user_id>')
@admin_required
def give_super_admin(user_id):
    """
    Method to give someone super admin
    user_id: the id of the user to give super admin
    """
    user_to_change = User.query.get(user_id)
    user_to_change.is_admin = 2
    db.session.commit()
    logger.info('User {} {} given super admin'.format(user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('admin.manage_users_page'))

@internal_blueprint.route('/admin-delete-user/<user_id>')
@admin_required
def admin_delete_user(user_id):
    """
    Method to delete a user
    """

    # grabbing the user
    user_to_delete = User.query.get(user_id)
    logger.info('Delete requested for user {} {}'.format(user_to_delete.first_name, user_to_delete.last_name))

    # checking that the user being deleted is not of a higher level than the current one
    if user_to_delete.is_admin >= current_user.is_admin:
        return redirect(url_for('admin.manage_users_page'))

    # notifying the user that they are being deleted
    try:
        message = Message (
            subject='Your Account has been deleted',
            recipients= [user_to_delete.passenger_profile.email_address],
            sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
            body=f"""
            Hello {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()}, \n\n
            Your account has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
            """,
        )
        mail.send(message)
        logger.info('User {} notified of deletion'.format(user_to_delete))
    except Exception as e:
        logger.warning('User {} not notified of deletion, probably due to invalid email address'.format(user_to_delete))
        logger.debug(e)

    # notifying their passengers (if any) that they are being deleted
    try:
        user_to_delete_upcoming_carpools = [carpool for carpool in user_to_delete.driver_profile.carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(days=1)]
    except AttributeError as e:
        logger.debug(e)
        user_to_delete_upcoming_carpools = []
    
    for carpool in user_to_delete_upcoming_carpools:
        for passenger in carpool.passengers:
            try:
                message = Message (
                    subject='Your Driver has been deleted',
                    recipients= [passenger.passenger_profile.email_address],
                    sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com')
                    )
                message.body = f"""
                Hello {passenger.first_name.capitalize()} {passenger.last_name.capitalize()}, \n\n
                Your driver {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
                mail.send(message)
                logger.info('Passenger {} notified of driver deletion'.format(passenger))
            except Exception as e:
                logger.warning('Passenger {} not notified of driver deletion, probably due to invalid email address'.format(passenger))
                logger.debug(e)

    # notifying their drivers (if any) that they are being deleted
    user_to_delete_upcoming_carpools = [carpool for carpool in user_to_delete.passenger_profile.carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(days=1)]
    for carpool in user_to_delete_upcoming_carpools:
        try:
            message = Message (
                subject='Your Passenger has been deleted',
                recipients= [carpool.driver.user[0].passenger_profile.email_address],
                sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                body=f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                Your passenger {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """
            )
        except Exception as e:
            logger.warning('Driver {} not notified of passenger deletion, probably due to invalid email address'.format(carpool.driver))
            logger.debug(e)


    # deleting the user and their carpools
    if user_to_delete.driver_profile is not None:
        for carpool in user_to_delete.driver_profile.carpools:
            carpool.driver = None
            carpool.driver_index = None

    for carpool in user_to_delete.passenger_profile.carpools:
        try:
            carpool.passengers.remove(user_to_delete)
        except ValueError as e: # this means that the user was not in the carpool
            logger.debug(e)
            pass

    db.session.commit()
    db.session.delete(user_to_delete.passenger_profile)
    try:
        db.session.delete(user_to_delete.driver_profile)
    except Exception as e:
        logger.debug(e) # passing after this

    db.session.delete(user_to_delete)
    db.session.commit()

    # redirecting back to the admin user page
    logger.info('User deleted.')
    return redirect(url_for('admin.manage_users_page'))

@login_required
@internal_blueprint.route('/cancel-carpool/<carpool_id>')
def cancel_carpool(carpool_id):
    """
    Page that allows for the cancellation of a carpool. Is not really used except for through carpool management page. Emails the passengers.
    """
    
    for carpool in current_user.driver_profile.carpools:
        if str(carpool.index) == carpool_id:
            logger.debug('got here')
            try:
                message = Message(
                    subject='Carpool Cancelled',
                    recipients=[passenger.email_address for passenger in carpool.passengers],
                    sender=('Mech Techs Carpooling', 'mechtechscarpooling@zohomail.com'),
                    body=f'Hello passengers, \n\n Your carpool for {carpool.event.event_name} has been cancelled. Please contact the driver for more information, or sign up for another carpool.'
                )
                mail.send(message)
            except AssertionError as e:
                logger.debug('No passengers were on the carpool')
            logger.info('Email sent to passengers of carpool {} about cancellation'.format(carpool))

            carpool.driver = None
            carpool.driver_id = None
            carpool.passengers = []  
            carpool.destination = carpool.region.dropoff_location
            db.session.commit()
            return redirect(url_for('main.manage_carpools_page'))
    
    logger.debug(f'{current_user.driver_profile.carpools}')
    return render_template('error_template.html', main_message='Go Away', sub_message='You do not have access to cancel this carpool.', user=current_user)


@internal_blueprint.route('/change-carpool-destination', methods=['GET', 'POST'])
@login_required
def change_carpool_destination():
    """
    Page that allows for the change of the destination of a carpool.
    """
    if request.method == 'GET':
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.', user=current_user)
    else:
        logger.info('changing carpool destination')
        new_destination = request.headers['New-Carpool-Destination']
        carpool_index = int(request.headers['Carpool-Index'])
        current_carpool = Carpool.query.filter_by(index=carpool_index).first()
        old_destination = current_carpool.destination
        current_carpool.destination = new_destination
        db.session.commit()
        logger.info('carpool destination changed to {} by {}'.format(new_destination, current_user))

        message = Message(
            'Carpool Destination Changed',
            recipients=[passenger.email_address for passenger in current_carpool.passengers],
            sender=('Mech Techs Carpooling','mechtechscarpooling@zohomail.com'),
            body=f"""
            Hello passengers of carpool for event {current_carpool.event.event_name}, \n\n
            The driver of the carpool has changed the destination from {old_destination} to {new_destination}. 
            Please make sure that you are ready to go to {new_destination} at the time of the carpool.
            """
        )
        mail.send(message)
        logger.info('Message sent to passengers of carpool.')
        return redirect(url_for('main.manage_carpools_page'))


@internal_blueprint.route('/leave-carpool/<carpool_id>')
@login_required
def leave_carpool(carpool_id):
    """
    Route that allows a passenger to leave a carpool
    """
    for carpool in current_user.passenger_profile.carpools: # making sure that the current user is in the carpool
        if str(carpool.index) == carpool_id:
            try:
                message = Message('A passenger has left the carpool.', recipients=[carpool.driver.email_address], sender=('Mech Techs Carpooling','mechtechscarpooling@zohomail.com'))
                message.body = f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                {current_user.first_name.capitalize()} {current_user.last_name.capitalize()} has left the carpool. Please check the carpool management page to see if you need to cancel the carpool.
                """
                mail.send(message)
                logger.info('Message sent to a driver.')
            except Exception as e:
                logger.warning(e)
                # maybe send an email to the admin
            
            carpool.passengers.remove(current_user.passenger_profile)
            db.session.commit()
            logger.info(f'User {current_user} left carpool {carpool}')

    return redirect(url_for('main.manage_carpools_page'))
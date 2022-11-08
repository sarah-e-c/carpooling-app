"""
Routes that are used only for internal purposes. (Like leaving carpools). Usually only referenced by javascript.
"""

from carpooling import db, mail
from carpooling.models import Event, Carpool,  User, EventCheckIn, Destination, Address
import logging
from carpooling.tasks import send_async_email, send_async_email_to_many
from carpooling.utils import admin_required, requires_auth_key
from flask import render_template, request, redirect, url_for, Blueprint, make_response
import datetime
from flask_login import login_required, current_user
from flask_mail import Message
from io import StringIO
import csv


internal_blueprint = Blueprint(
    'internal', __name__, template_folder='templates')
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
        logger.info(
            'A person attempted to delete an event they were not authorized to delete')
        return redirect(url_for('main.events_page'))

    # notifying the drivers of the event
    for carpool in event_to_delete.carpools:
        send_async_email.delay(carpool.driver.user[0].passenger_profile.email_address, 'The event you signed up to carpool for has been deleted.', f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """)

    # notifying the passengers of the event
    for carpool in event_to_delete.carpools:
        send_async_email_to_many.delay([passenger.passenger_profile.email_address for passenger in carpool.passengers], 'The event you had signed up for a carpool for has been deleted', f"""
                Hello passengers, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """)

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
        logger.info('User {} {} is of higher admin than user {} {}'.format(current_user.first_name.capitalize(
        ), current_user.last_name.capitalize(), user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
        return redirect(url_for('admin.manage_users_page'))

    if user_to_change.is_admin > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('admin.manage_users_page'))

    user_to_change.is_admin = 0
    db.session.commit()
    logger.info('User {} {} removed from admin'.format(
        user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
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
    logger.info('User {} {} given admin'.format(
        user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
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
    logger.info('User {} {} given super admin'.format(
        user_to_change.first_name.capitalize(), user_to_change.last_name.capitalize()))
    return redirect(url_for('admin.manage_users_page'))


@internal_blueprint.route('/admin-delete-user/<user_id>')
@admin_required
def admin_delete_user(user_id):
    """
    Method to delete a user
    """

    # grabbing the user
    user_to_delete = User.query.get(user_id)
    logger.info('Delete requested for user {} {}'.format(
        user_to_delete.first_name, user_to_delete.last_name))

    # checking that the user being deleted is not of a higher level than the current one
    if user_to_delete.is_admin >= current_user.is_admin:
        return redirect(url_for('admin.manage_users_page'))


    # notifying the user that they are being deleted
    send_async_email.delay(user_to_delete.passenger_profile.email_address, 'Your Account has been deleted', f"""
            Hello {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()}, \n\n
            Your account has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
            """)

    # notifying their passengers (if any) that they are being deleted
    try:
        user_to_delete_upcoming_carpools = [
            carpool for carpool in user_to_delete.driver_profile.carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(days=1)]
    except AttributeError as e:
        logger.debug(e)
        user_to_delete_upcoming_carpools = []

    for carpool in user_to_delete_upcoming_carpools:
        for passenger in carpool.passengers:
            send_async_email.delay(passenger.passenger_profile.email_address, 'Your driver has been deleted',f"""
                Hello {passenger.first_name.capitalize()} {passenger.last_name.capitalize()}, \n\n
                Your driver {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """ )

    # notifying their drivers (if any) that they are being deleted
    user_to_delete_upcoming_carpools = [
        carpool for carpool in user_to_delete.passenger_profile.carpools if carpool.event.event_date > datetime.datetime.now() - datetime.timedelta(days=1)]
    for carpool in user_to_delete_upcoming_carpools:
        send_async_email.delay(carpool.driver.user[0].passenger_profile.email_address, 'A passenger of yours has been deleted', f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                Your passenger {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """)

    # deleting the user and their carpools
    if user_to_delete.driver_profile is not None:
        for carpool in user_to_delete.driver_profile.carpools:
            carpool.driver = None
            carpool.driver_index = None

    for carpool in user_to_delete.passenger_profile.carpools:
        try:
            carpool.passengers.remove(user_to_delete)
        except ValueError as e:  # this means that the user was not in the carpool
            logger.debug(e)
            pass

    db.session.commit()
    db.session.delete(user_to_delete.passenger_profile)
    try:
        db.session.delete(user_to_delete.driver_profile)
    except Exception as e:
        logger.debug(e)  # passing after this

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
            send_async_email_to_many.delay([passenger.email_address for passenger in carpool.passengers], 'Carpool Cancelled', f'Hello passengers, \n\n Your carpool for {carpool.event.event_name} has been cancelled. Please contact the driver for more information, or sign up for another carpool.')

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
        logger.info('carpool destination changed to {} by {}'.format(
            new_destination, current_user))

        send_async_email_to_many.delay([passenger.email_address for passenger in current_carpool.passengers], 'Carpool Destination Changed', f"""
            Hello passengers of carpool for event {current_carpool.event.event_name}, \n\n
            The driver of the carpool has changed the destination from {old_destination} to {new_destination}. 
            Please make sure that you are ready to go to {new_destination} at the time of the carpool.
            """)
        return redirect(url_for('main.manage_carpools_page'))


@internal_blueprint.route('/leave-carpool/<carpool_id>')
@login_required
def leave_carpool(carpool_id):
    """
    Route that allows a passenger to leave a carpool
    """
    for carpool in current_user.passenger_profile.carpools:  # making sure that the current user is in the carpool
        if str(carpool.index) == carpool_id:
            send_async_email.delay(carpool.driver.email_address, 'A passenger has left the carpool', f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                {current_user.first_name.capitalize()} {current_user.last_name.capitalize()} has left the carpool. Please check the carpool management page to see if you need to cancel the carpool.
                """)

            carpool.passengers.remove(current_user.passenger_profile)
            db.session.commit()
            logger.info(f'User {current_user} left carpool {carpool}')

    return redirect(url_for('main.manage_carpools_page'))



@internal_blueprint.route('/event-checkin/<event_index>', methods=['GET', 'POST'])
@login_required
def event_check_in_page(event_index):
    """
    Function to sign up for an event.
    """

    if EventCheckIn.query.filter_by(event_id=event_index, user_id=current_user.id).first() is not None:
        logger.info('Passenger {} already signed up for event {}'.format(current_user.passenger_profile, event_index))
        existing_check_in = EventCheckIn.query.filter_by(event_id=event_index, user_id=current_user.id).first()
        existing_check_in.re_check_in_time = datetime.datetime.now()
        db.session.commit()
        logger.info('Passenger {} re-checked in for event {}'.format(current_user.passenger_profile, event_index))
        return redirect(url_for('event_page', event_index=event_index))

    logger.info('Passenger {} checking in for event {}'.format(current_user.passenger_profile, event_index))
    new_event_check_in = EventCheckIn(event_id=event_index, user_id=current_user.id)
    db.session.add(new_event_check_in)
    db.session.commit()
    return redirect(url_for('event_page', event_index=event_index))

@internal_blueprint.route('/event-checkout/<event_index>', methods=['GET', 'POST'])
@login_required
def event_check_out_page(event_index):
    """
    Function to check out of an event.
    """
    logger.info('Passenger {} checking out of event {}'.format(current_user.passenger_profile, event_index))
    event_check_in = EventCheckIn.query.filter_by(event_id=event_index, user_id=current_user.id).first()
    event_check_in.re_check_in_time = None
    event_check_in.check_out_time = datetime.datetime.now()
    db.session.commit()
    return redirect(url_for('event_page', event_index=event_index))


@internal_blueprint.route('/download-hours-csv/<event_index>')
@admin_required
def download_hours_csv(event_index):
    """
    Function to download the hours csv as an admin
    """
    check_ins = EventCheckIn.query.filter_by(event_id=event_index)
    event_name = Event.query.get(event_index).event_name
    heading_row = ["First Name", "Last Name", "Check In Time", "Check Out Time", "Check In Hours"]
    strio = StringIO()
    cw = csv.writer(strio)
    cw.writerow(heading_row)
    csv_content = []
    for check_in in check_ins:
        new_row = [check_in.user.first_name.capitalize(),
        check_in.user.last_name.capitalize(),
        check_in.check_in_time.strftime('%I:%M %p'),
        check_in.check_out_time.strftime('%I:%M %p'),
        str(check_in.check_out_time - check_in.check_in_time)]
        csv_content.append(new_row)
    cw.writerows(csv_content)
    output = make_response(strio.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={event_name}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@internal_blueprint.route('/create-destination', methods=['GET', 'POST'])
@requires_auth_key
def create_destination():
    """
    Creates a destination
    """

    if request.method == 'GET':
        return redirect(url_for('main.create_event_page'))
    # creating the destination
    new_address = Address(address_line_1=request.form['addressline1'],
                          zip_code=request.form['zipcode'],
                          city=request.form['city'],
                          state=request.form['state'],
                          latitude=request.form['latitude'],
                          longitude=request.form['longitude'],
                          code=request.form['place_id'])

    db.session.add(new_address)
    db.session.add(new_address)
    db.session.commit()

    logger.info('Address {} created'.format(new_address))


    new_destination = Destination(name=request.form['destinationname'],
                                    address_id=new_address.id)

    db.session.add(new_destination)
    db.session.commit()
    logger.info('Destination {} created'.format(new_destination))

    return redirect(url_for('main.create_event_page'))
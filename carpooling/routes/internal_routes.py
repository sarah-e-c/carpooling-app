"""
Routes that are used only for internal purposes. (Like leaving carpools). Usually only referenced by javascript.
"""

from carpooling import db, mail
from carpooling.models import Event, Carpool, User, EventCheckIn, Destination, Address, GeneratedCarpool, \
    EventCarpoolSignup, GeneratedCarpoolResponse, Organization
import logging
from carpooling.tasks import send_async_email, send_async_email_to_many
from carpooling.utils import admin_required, requires_auth_key
from flask import render_template, request, redirect, url_for, Blueprint, make_response, jsonify, session, flash
import datetime
from flask_login import login_required, current_user, login_user
from flask_mail import Message
from io import StringIO
import csv
import json
from werkzeug.security import generate_password_hash
import secrets
import json

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
    if not ((event_to_delete.user == current_user) or (current_user.is_admin() > 0)):
        logger.info(
            'A person attempted to delete an event they were not authorized to delete')
        return redirect(url_for('main.events_page'))

    # notifying the drivers of the event
    for carpool in event_to_delete.carpools:
        if carpool.driver != None:
            send_async_email.delay(carpool.driver.email_address,
                                   'The event you signed up to carpool for has been deleted.', f"""
                    Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                    The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                    """)

    # notifying the passengers of the event
    for carpool in event_to_delete.carpools:
        send_async_email_to_many.delay([passenger.email_address for passenger in carpool.passengers],
                                       'The event you had signed up for a carpool for has been deleted', f"""
                Hello passengers, \n\n
                The event {event_to_delete.name} has been deleted by the event creator or admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """)
    # deleting the carpools of the event
    for carpool in event_to_delete.carpools:
        db.session.delete(carpool)

    # deleting the carpool signups
    for carpool_signup in event_to_delete.event_carpool_signups:
        db.session.delete(carpool_signup)

    # deleting the event
    db.session.delete(event_to_delete)
    db.session.commit()

    logger.info('Event {} deleted'.format(event_to_delete.name))
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
    if user_to_change.is_admin() >= current_user.is_admin():
        logger.info('User {} {} is of higher admin than user {} {}'.format(current_user.first_name.capitalize(
        ), current_user.last_name.capitalize(), user_to_change.first_name.capitalize(),
            user_to_change.last_name.capitalize()))
        return redirect(url_for('admin.manage_users_page'))

    if user_to_change.is_admin() > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('admin.manage_users_page'))

    user_to_change.set_admin_level(0)
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
    if user_to_change.is_admin() > 1:
        logger.info('User {} is already super admin'.format(user_to_change))
        return redirect(url_for('admin.manage_users_page'))

    user_to_change.set_admin_level(1)
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
    user_to_change.set_admin_level(2)
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
    if user_to_delete.is_admin() >= current_user.is_admin():
        return redirect(url_for('admin.manage_users_page'))

    # notifying the user that they are being deleted
    send_async_email.delay(user_to_delete.email_address, 'Your Account has been deleted', f"""
            Hello {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()}, \n\n
            Your account has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
            """)

    # notifying their passengers (if any) that they are being deleted
    try:
        user_to_delete_upcoming_carpools = [
            carpool for carpool in user_to_delete.driver_profile.carpools if
            carpool.event.date > datetime.datetime.now() - datetime.timedelta(days=1)]
    except AttributeError as e:
        logger.debug(e)
        user_to_delete_upcoming_carpools = []

    for carpool in user_to_delete_upcoming_carpools:
        for passenger in carpool.passengers:
            send_async_email.delay(passenger.email_address, 'Your driver has been deleted', f"""
                Hello {passenger.first_name.capitalize()} {passenger.last_name.capitalize()}, \n\n
                Your driver {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """)

    # notifying their drivers (if any) that they are being deleted
    user_to_delete_upcoming_carpools = [
        carpool for carpool in user_to_delete.carpools if
        carpool.event.date > datetime.datetime.now() - datetime.timedelta(days=1)]
    for carpool in user_to_delete_upcoming_carpools:
        if carpool.driver is not None:
            send_async_email.delay(carpool.driver.email_address, 'Your passenger has been deleted', f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                Your passenger {user_to_delete.first_name.capitalize()} {user_to_delete.last_name.capitalize()} has been deleted by admin {current_user.first_name.capitalize()} {current_user.last_name.capitalize()}. If you believe this is an error, please contact them.
                """)

    # deleting the user and their carpools
    if user_to_delete.driver_profile is not None:
        for carpool in user_to_delete.driver_profile.carpools:
            carpool.driver = None
            carpool.driver_index = None

    for carpool in user_to_delete.carpools:
        try:
            carpool.passengers.remove(user_to_delete)
        except ValueError as e:  # this means that the user was not in the carpool
            logger.debug(e)
            pass

    db.session.commit()
    db.session.delete(user_to_delete)
    try:
        db.session.delete(user_to_delete.driver_profile)
    except Exception as e:
        logger.debug(e)  # passing after this

    db.session.delete(user_to_delete)
    db.session.commit()

    # redirecting back to the admin user page
    logger.info('User deleted.')
    return redirect(url_for('admin.manage_users_page'))


# @login_required
# @internal_blueprint.route('/cancel-carpool/<carpool_id>')
# def cancel_carpool(carpool_id):
#     """
#     Page that allows for the cancellation of a carpool. Is not really used except for through carpool management page. Emails the passengers.
#     """

#     for carpool in current_user.driver_carpools:
#         if str(carpool.index) == carpool_id:
#             send_async_email_to_many.delay([passenger.email_address for passenger in carpool.passengers],
#                                            'Carpool Cancelled',
#                                            f'Hello passengers, \n\n Your carpool for {carpool.event.name} has been cancelled. Please contact the driver for more information, or sign up for another carpool.')

#             carpool.driver = None
#             carpool.driver_id = None
#             carpool.passengers = []
#             carpool.destination = carpool.region.dropoff_location
#             db.session.commit()
#             return redirect(url_for('main.manage_carpools_page'))

#     logger.debug(f'{current_user.driver}')
#     return render_template('error_template.html', main_message='Go Away',
#                            sub_message='You do not have access to cancel this carpool.', user=current_user)


@internal_blueprint.route('/change-carpool-destination', methods=['GET', 'POST'])
@login_required
def change_carpool_destination():
    """
    Page that allows for the change of the destination of a carpool.
    """
    if request.method == 'GET':
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.',
                               user=current_user)
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

        send_async_email_to_many.delay([passenger.email_address for passenger in current_carpool.passengers],
                                       'Carpool Destination Changed', f"""
            Hello passengers of carpool for event {current_carpool.event.name}, \n\n
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
    for carpool in current_user.passenger_carpools:  # making sure that the current user is in the carpool
        if str(carpool.index) == carpool_id:
            send_async_email.delay(carpool.driver.email_address, 'A passenger has left the carpool', f"""
                Hello {carpool.driver.first_name.capitalize()} {carpool.driver.last_name.capitalize()}, \n\n
                {current_user.first_name.capitalize()} {current_user.last_name.capitalize()} has left the carpool. Please check the carpool management page to see if you need to cancel the carpool.
                """)

            carpool.passengers.remove(current_user)
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
        logger.info('Passenger {} already signed up for event {}'.format(current_user, event_index))
        existing_check_in = EventCheckIn.query.filter_by(event_id=event_index, user_id=current_user.id).first()
        existing_check_in.re_check_in_time = datetime.datetime.now()
        db.session.commit()
        logger.info('Passenger {} re-checked in for event {}'.format(current_user, event_index))
        return redirect(url_for('main.event_page', event_index=event_index))

    logger.info('Passenger {} checking in for event {}'.format(current_user, event_index))
    new_event_check_in = EventCheckIn(event_id=event_index, user_id=current_user.id)
    db.session.add(new_event_check_in)
    db.session.commit()
    return redirect(url_for('main.event_page', event_index=event_index))


@internal_blueprint.route('/event-checkout/<event_index>', methods=['GET', 'POST'])
@login_required
def event_check_out_page(event_index):
    """
    Function to check out of an event.
    """
    logger.info('Passenger {} checking out of event {}'.format(current_user, event_index))
    event_check_in = EventCheckIn.query.filter_by(event_id=event_index, user_id=current_user.id).first()
    event_check_in.re_check_in_time = None
    event_check_in.check_out_time = datetime.datetime.now()
    db.session.commit()
    return redirect(url_for('main.event_page', event_index=event_index))


@internal_blueprint.route('/download-hours-csv/<event_index>')
@admin_required
def download_hours_csv(event_index):
    """
    Function to download the hours csv as an admin
    """
    check_ins = EventCheckIn.query.filter_by(event_id=event_index)
    event_name = Event.query.get(event_index).name
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
    new_address = Address.query.filter_by(code=request.form['place_id']).first()
    if not new_address:
        new_address = Address(id=None,
                          address_line_1=request.form['addressline1'],
                          zip_code=request.form['zipcode'],
                          city=request.form['city'],
                          state=request.form['state'],
                          latitude=request.form['latitude'],
                          longitude=request.form['longitude'],
                          code=request.form['place_id'])

    db.session.add(new_address)
    db.session.commit()

    logger.info('Address {} created'.format(new_address))
    logger.info(request.form)

    new_destination = Destination(name=request.form['destinationname'],
                                  address_id=new_address.id,
                                  organization=Organization.query.get(int(session['organization'])),
                                  organization_id=int(session['organization']))

    db.session.add(new_destination)
    db.session.commit()
    logger.info('Destination {} created'.format(new_destination))

    return redirect(url_for('main.create_event_page'))


@internal_blueprint.route('/get-generated-carpool-data/<carpool_id>', methods=['GET', 'POST'])
@login_required
def get_generated_carpool_data(carpool_id):
    """
    Internal function to get the generated carpool data to render on the carpool summary page
    """
    # get the carpool
    carpool = GeneratedCarpool.query.get(carpool_id)

    # checking if the person is eligible to view the carpool
    if (carpool.driver.id != current_user.id and len([passenger for passenger in carpool.passengers if
                                                      passenger.id == current_user.id]) == 0) and not current_user.is_admin():
        return redirect(url_for('main.index'))

    carpool_data = {'driverName': carpool.driver.first_name.capitalize() + ' ' + carpool.driver.last_name.capitalize(),
                    'driverPhone': carpool.driver.phone_number,
                    'driverEmail': carpool.driver.email_address,
                    'passengers': [
                        {'passengerName': passenger.first_name.capitalize() + ' ' + passenger.last_name.capitalize()}
                        for passenger in carpool.passengers],
                    'origin': f"{carpool.from_address.address_line_1} {carpool.from_address.city} {carpool.from_address.state}",
                    'destination': f'{carpool.to_address.address_line_1} {carpool.to_address.city} {carpool.to_address.state}',
                    'waypoints': [
                        {'location': f'{part.to_address.address_line_1} {part.to_address.city} {part.to_address.state}',
                         'stopover': True} for part in carpool.generated_carpool_parts[:-1]],
                    }
    return json.dumps(carpool_data)


@internal_blueprint.route('/create-carpool-signup/<event_index>', methods=['GET', 'POST'])
@login_required
def create_carpool_signup(event_index):
    """
    Function to sign up for a carpool event
    """
    if request.method == 'GET':
        return redirect(url_for('main.event_page', event_index=event_index))

    if request.method == 'POST':
        logger.info('Passenger {} signing up for carpool event {}'.format(current_user, event_index))

        willing_to_drive = request.form.get('willing_to_drive') == 'on'
        logger.info(f'willing to drive: {willing_to_drive}, {request.form}')
        needs_ride = request.form.get('needs_ride') == 'on'

        new_signup = EventCarpoolSignup(event_id=event_index,
                                        user_id=current_user.id,
                                        willing_to_drive=willing_to_drive,
                                        needs_ride=needs_ride)
        current_user.event_carpool_signups.append(new_signup)
        db.session.commit()
        logger.info('Passenger {} signed up for carpool event {}'.format(current_user, event_index))
        return redirect(url_for('main.event_page', event_index=event_index))


@internal_blueprint.route('/cancel-carpool-signup/<event_index>', methods=['GET'])
@login_required
def cancel_carpool_signup(event_index):
    """
    Function to cancel a carpool signup
    """
    logger.info('Passenger {} cancelling carpool signup for event {}'.format(current_user, event_index))
    signup = EventCarpoolSignup.query.filter_by(event_id=event_index, user_id=current_user.id).first()
    if signup is not None:
        db.session.delete(signup)
        db.session.commit()
        logger.info('Passenger {} cancelled carpool signup for event {}'.format(current_user, event_index))
    return redirect(url_for('main.event_page', event_index=event_index))


@internal_blueprint.route('/confirm-carpool/<carpool_id>', methods=['GET'])
@login_required
def confirm_carpool(carpool_id):
    """
    Function to confirm a carpool
    """
    logger.info('Passenger {} confirming carpool {}'.format(current_user, carpool_id))
    carpool = GeneratedCarpool.query.get(carpool_id)
    new_response = GeneratedCarpoolResponse(
        user=current_user,
        generated_carpool=carpool,
        is_accepted=True,
    )
    current_user.pool_points += eval(carpool.carpool_solution.pool_points)[current_user.id]
    logger.info('Added {} pool points to user {}'.format(eval(carpool.carpool_solution.pool_points)[current_user.id], current_user))
    db.session.add(new_response)
    db.session.commit()

    # checking if all the passengers have confirmed
    for person in carpool.passengers:
        if len([response for response in carpool.generated_carpool_responses if
                response.user.id == person.id and response.is_accepted]) == 0:
            return redirect(url_for('main.manage_carpools_page'))
    if len([response for response in carpool.generated_carpool_responses if
            response.user.id == carpool.driver.id and response.is_accepted]) == 0:
        return redirect(url_for('main.manage_carpools_page'))

    # if all the passengers have confirmed, then we can set everything as accepted and notify the drivers and passengers
    carpool.is_accepted = True
    db.session.commit()

    # notify the driver
    send_async_email_to_many.delay(
        to=[passenger.email_address for passenger in carpool.passengers] + [carpool.driver.email_address],
        subject='You\'re all good to go!',
        message="""
        You're all good to go! Your carpool for {} has been confirmed by everyone. You can view the details of your carpool at the following link: {}""".format(
            carpool.event.name,
            url_for('main.manage_carpools_page', _external=True))
    )
    return redirect(url_for('main.carpool_summary_page', carpool_index=carpool_id))


@internal_blueprint.route('/decline-carpool/<carpool_id>', methods=['GET'])
@login_required
def decline_carpool(carpool_id):
    """
    Function to decline a carpool
    """
    logger.info('Passenger {} declining carpool {}'.format(current_user, carpool_id))
    carpool = GeneratedCarpool.query.get(carpool_id)
    new_response = GeneratedCarpoolResponse(
        user=current_user,
        generated_carpool=carpool,
        is_accepted=False,
    )
    db.session.add(new_response)
    db.session.commit()
    # notify all the carpool recipients
    # if the person who declined is the driver, then we need to notify all the passengers
    if carpool.driver == current_user:
        send_async_email_to_many.delay(
            to=[passenger.email_address for passenger in carpool.passengers],
            subject='The driver, {}, cancelled the carpool.'.format(current_user.first_name.capitalize()),
            message="""
            {} has declined your carpool for {}. You can view the details of your carpool at the following link: {}""".format(
                current_user.first_name.capitalize(),
                carpool.event.name,
                url_for('main.manage_carpools_page', _external=True))
        )
    elif current_user in carpool.passengers:  # if they weren't the driver, then we need to notify everyone and remove them from the route
        send_async_email_to_many.delay(
            to=[passenger.email_address for passenger in carpool.passengers if passenger.email_address != current_user.email_address] + [carpool.driver.email_address],
            subject='{} declined the carpool.'.format(current_user.first_name.capitalize()),
            message=f"""
            {current_user.first_name.capitalize()} declined the carpool :(. Your route has been modified to reflect the
            change. You can view the details of your carpool at the following link: {url_for('main.manage_carpools_page', _external=True)}"""

        )
        # changing the carpool to reflect the change
        carpool.passengers.remove(current_user)
        to_address_part = \
            [part for part in carpool.generated_carpool_parts if part.to_address in current_user.addresses][0]
        from_address_part = \
            [part for part in carpool.generated_carpool_parts if part.from_address in current_user.addresses][0]

        next_parts = [part for part in carpool.generated_carpool_parts if part.idx > from_address_part.idx]
        for part in next_parts:
            part.idx -= 1
        to_address_part.to_address = from_address_part.to_address
        carpool.generated_carpool_parts.remove(from_address_part)
        db.session.delete(from_address_part)
        db.session.commit()
    else:
        logger.error('User {} is not in carpool {}'.format(current_user, carpool_id))

    return redirect(url_for('main.carpool_summary_page', carpool_id=carpool_id))


@internal_blueprint.route('/cancel-generated-carpool/<carpool_id>', methods=['GET'])
@login_required
def cancel_generated_carpool(carpool_id):
    """
    Function to cancel a generated carpool
    """

    # if they are not the driver, then redirect
    logger.info('Driver {} cancelling carpool {}'.format(current_user, carpool_id))
    carpool = GeneratedCarpool.query.get(carpool_id)
    current_user.pool_points -= eval(carpool.carpool_solution.pool_points)[current_user.id] - 5
    logger.info('Subtracting {} pool points to user {} plus an additional 5 for cancelling.'.format(eval(carpool.carpool_solution.pool_points)[current_user.id], current_user))
    if carpool.driver == current_user:
        # notify all the carpool recipients
        send_async_email_to_many.delay(
            to=[passenger.email_address for passenger in carpool.passengers],
            subject='The driver, {}, cancelled the carpool.'.format(current_user.first_name.capitalize()),
            message="""
            {} has cancelled your carpool for {}. You can view the details of your carpool at the following link: {}""".format(
                current_user.first_name.capitalize(),
                carpool.event.name,
                url_for('main.manage_carpools_page', _external=True))
        )
        db.session.delete(carpool)
        db.session.commit()
        return redirect(url_for('main.manage_carpools_page'))
    elif current_user in carpool.passengers:
        logger.info(f"passengers: {carpool.passengers}")
        logger.debug(f"current users email addresses: {[passenger.email_address for passenger in carpool.passengers]}")
        send_async_email_to_many.delay(

            to=[carpool.driver.email_address] + [passenger.email_address for passenger in carpool.passengers if passenger.email_address != current_user.email_address],
            subject='{} declined the carpool.'.format(current_user.first_name.capitalize()),
            message=f"""
                    {current_user.first_name.capitalize()} had to leave the carpool :(. Your route has been modified to reflect the
                    change. You can view the details of your carpool at the following link: {url_for('main.manage_carpools_page', _external=True)}"""

        )

        # setting their response to no
        carpool_response = [response for response in carpool.generated_carpool_responses if response.user == current_user][0]
        carpool_response.is_accepted = False
        logger.debug(
            'Passenger {} cancelling carpool {}, with resopnse {}'.format(current_user, carpool_id, carpool_response))

        # changing the carpool to reflect the change
        carpool.passengers.remove(current_user)
        to_address_part = \
            [part for part in carpool.generated_carpool_parts if part.to_address in current_user.addresses][0]
        from_address_part = \
            [part for part in carpool.generated_carpool_parts if part.from_address in current_user.addresses][0]

        next_parts = [part for part in carpool.generated_carpool_parts if part.idx > from_address_part.idx]
        for part in next_parts:
            part.idx -= 1
        to_address_part.to_address = from_address_part.to_address
        carpool.generated_carpool_parts.remove(from_address_part)
        db.session.delete(from_address_part)
        db.session.commit()
        logger.info('Passenger {} cancelled carpool {}'.format(current_user, carpool_id))
        return redirect(url_for('main.manage_carpools_page'))
    else:
        logger.info(f"User {current_user} is not a part of carpool {carpool_id}")
        return redirect(url_for('main.manage_carpools_page'))


@internal_blueprint.route('/register_new_user', methods=['POST'])
def register_new_user():
    def valid(s: str) -> str | None:
        return s if s else None
    
    new_organization = False
    try:
        new_name = request.form["organizationname"]
        logger.debug(new_name)
        if new_name:
            logger.debug(f"The new organization name is {new_name}")
            new_organization = True
        else:
            logger.debug("No new organization was found.")
    except KeyError as e:
        logger.debug(e)


    if new_organization:
        organization = Organization(name=request.form["organizationname"], access_key=secrets.token_urlsafe(8))
    else:
        organization = Organization.query.filter_by(access_key=request.form["organizationaccesskey"]).one()

    address = Address.query.filter_by(
        code=request.form['placeid']).first()
    
    if not address:
        address = Address(
            address_line_1=request.form['addressline1'],
            address_line_2=request.form['addressline2'],
            city=request.form['city'],
            state='VA',
            zip_code=request.form['zipcode'],
            latitude=request.form['latitude'],
            longitude=request.form['longitude'],
            code=request.form['placeid']
        )

    new_user = User(
        first_name=request.form['firstname'].lower(),
        last_name=request.form['lastname'].lower(),
        email_address=request.form['email'],
        phone_number=request.form['phonenumber'],
        car_type_1=valid(request.form['cartype1']),
        car_type_2=valid(request.form['cartype2']),
        car_color_1=valid(request.form['carcolor1']),
        car_color_2=valid(request.form['carcolor2']),
        emergency_contact_number=request.form['emergencycontact'],
        emergency_contact_relation=request.form['emergencycontactrelation'],
        num_years_with_license = valid(request.form['numyearswithlicense']),
        extra_information=request.form['note'],
        num_seats=valid(request.form['numberofseats']),
        student_or_parent=valid(request.form['studentorparent']),
        password=generate_password_hash(request.form['password'])
    )

    new_user.addresses.append(address)
    new_user.organizations.append(organization)
    db.session.add(new_user)
    db.session.commit()

    if new_organization:
        new_user.organizations[0].organization_user_links[0].admin_level = 2
    db.session.commit()
    login_user(new_user, remember=True)
    return redirect(url_for('main.home_page'))


@internal_blueprint.route('/email-address-exists/<email_address>')
def email_address_exists(email_address):
    user = User.query.filter_by(email_address=email_address).first()
    if user:
        return 'True'
    else:
        return 'False'
    
@internal_blueprint.route('/organization-key-exists/<organization_key>')
def organization_key_exists(organization_key):
    organization = Organization.query.filter_by(access_key=organization_key).first()
    return "True" if organization else "False"

@internal_blueprint.route('/change-organization/<organization_id>')
@login_required
def change_organization(organization_id):
    """
    route to change the organization that the user is logged into. Requires that they are a part of the organization.
    Reload is performed on the frontend to enact the change.
    """
    if int(organization_id) not in [organization.id for organization in current_user.organizations]:
        return 'Attempted to change organization into one user did not belong to.'
    
    session['organization'] = organization_id
    session['organizationname'] = Organization.query.get(int(organization_id)).name
    logger.debug("organization logged into changed.")
    flash(f'Current organization changed.')
    return "Successfully changed current organization."
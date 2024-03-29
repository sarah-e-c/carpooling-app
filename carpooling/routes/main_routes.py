"""
Main, user-facing routes for the application
"""
import secrets

from carpooling import db
from carpooling import mail
from carpooling.models import Address, Event, Carpool, User, Destination, \
    GeneratedCarpool, Organization
import logging
from carpooling.tasks import send_async_email
from carpooling.utils import driver_required
from flask import render_template, request, redirect, url_for, flash
import datetime
from flask_login import login_required, current_user, logout_user
from carpooling.utils import requires_auth_key
from flask_mail import Message
from flask import Blueprint, session
from carpooling import tasks_


main_blueprint = Blueprint('main', __name__, template_folder='templates')

DEFAULT_NUMBER_OF_CARPOOLS = 4

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# logFormatter = logging.Formatter(fmt=' %(name)s :: %(levelname)-8s :: %(message)s')
# logging.RootLogger(logging.DEBUG)


# h2 = logging.SMTPHandler(mailhost=app.config['MAIL_SERVER'],
#                             fromaddr=app.config['MAIL_USERNAME'],
#                             toaddrs=app.config['MAIL_USERNAME'],
#                             subject='Carpooling Error',
#                             credentials=(app.config['MAIL_USERNAME'],app.config['MAIL_PASSWORD']),
#                             secure=None)
# h2.setLevel(logging.CRITICAL)
# h2.setFormatter(logFormatter)
# logging.getLogger().addHandler(h2)


@main_blueprint.route('/')
def home_page(logout=False):
    """
    Home page. Also index page.
    """
    # if the user requested a logout, then they get logged out here
    logout = request.args.get('logout')
    if logout:
        logout_user()
        flash('You have been logged out.', 'message')
        logger.info(f'User {current_user} logged out')

    # finding the information needed for the dashboard... technically doesn't need to be done if not authenticated, but its not too bad
    events = Event.query.all()
    events = [event for event in events if event.date >=
              datetime.datetime.now() - datetime.timedelta(hours=36)]
    if current_user.is_authenticated:
        if current_user.num_seats is not None:
            driver_carpools = [carpool for carpool in Carpool.query.filter_by(driver_index=current_user.id).all(
            ) if carpool.event.date >= datetime.datetime.now() - datetime.timedelta(hours=36)]
        else:
            driver_carpools = []
        passenger_carpools = [carpool for carpool in current_user.passenger_carpools if carpool.event.date >=
                              datetime.datetime.now() - datetime.timedelta(hours=36)]
    else:
        driver_carpools = []
        passenger_carpools = []

    return render_template('index.html', user=current_user, driver_carpools=driver_carpools,
                           passenger_carpools=passenger_carpools, events=events)


@main_blueprint.route('/driver/<id>')
@requires_auth_key
def driver_page(id):
    """
    Driver page for passengers and other drivers to see
    last_name: last name of the driver
    first_name: first name of the driver
    """
    logger.info('driver page')
    try:
        driver = User.query.get(id)
    except:
        logger.info('no driver was found')
        return 'No driver was found.'

    logger.info('driver found')
    driver_info = {'lastname': driver.last_name.capitalize(),
                   'firstname': driver.first_name.capitalize(),
                   'car_type_1': driver.car_type_1,
                   'car_color_1': driver.car_color_1,
                   'car_type_2': driver.car_type_2,
                   'car_color_2': driver.car_color_2,
                   'number_seats': driver.num_seats,
                   'phone_number': driver.phone_number,
                   'email': driver.email_address,
                   'student_or_parent': driver.student_or_parent,
                   'emergencycontact': driver.emergency_contact_number,
                   'emergencycontactrelation': driver.emergency_contact_relation,
                   'licenseyears': driver.num_years_with_license,
                   'phone_number_string': f'tel:{driver.phone_number}',
                   'email_string': f'mailto:{driver.email_address}',
                   'extra_information': driver.extra_information}

    return render_template('driver_template.html', **driver_info, user=current_user)


@main_blueprint.route('/events')
def events_page():
    """
    Page to display all upcoming events. Probably should make an events log in the futre
    """
    current_events = Event.query.filter(
        Event.date >= datetime.datetime.now() - datetime.timedelta(hours=36)).all()
    return render_template('events_template.html', events=current_events, user=current_user)


@main_blueprint.route('/event/<event_index>')
def event_page(event_index):
    """
    Event page
    event_index: the index of the event that is wanted.
    """
    try:
        event = Event.query.get(event_index)
    except:  # the event doesn't exist
        redirect(url_for('main.events_page'))

    return render_template('event_template.html', event=event, user=current_user)


@main_blueprint.route('/create-event', methods=['GET', 'POST'])
@login_required
@requires_auth_key
def create_event_page():
    """
    Create event page. Used for verified users to create events.
    """
    try:
        if not session["organization"]:
            session["organization"] = current_user.organizations[0].id
    except KeyError as e:
        session["organization"] = current_user.organizations[0].id

    if request.method == 'GET':
        destinations = Destination.query.all()
        message = request.args.get('message')
        if message is None:
            message = 'Create an Event'
        return render_template('create_event_template.html', message=message, user=current_user,
                               destinations=destinations, organization=session["organization"])

    if request.method == 'POST':
        # getting the event info from the form
        # getting the matching build type
        matching_build_type = 0
        needs_matching_build_to = bool(request.form.get('needsmatchingbuildto', False))
        needs_matching_build_from = bool(request.form.get('needsmatchingbuildfrom', False))
        if needs_matching_build_to and needs_matching_build_from:
            matching_build_type = 3
        elif needs_matching_build_to:
            matching_build_type = 1
        elif needs_matching_build_from:
            matching_build_type = 2

        event_info = {
            'name': request.form['eventname'],
            'date': datetime.datetime.strptime(request.form['eventdate'], '%Y-%m-%d'),
            'start_time': datetime.datetime.strptime(request.form['eventstarttime'], '%H:%M'),
            'end_time': datetime.datetime.strptime(request.form['eventendtime'], '%H:%M'),
            'description': request.form['eventdescription'],
            'creator_id': current_user.id,
            'destination_id': Destination.query.filter_by(name=request.form['eventAddress']).one().id,
            'needs_matching_build_to': needs_matching_build_to,
            'needs_matching_build_from': needs_matching_build_from,
            'matching_build_type': matching_build_type,
            'organization_id': request.form['organization']
        }

        try:
            new_event = Event(**event_info)
            db.session.add(new_event)

            db.session.commit()
            logger.info(
                f'New event added to database: {new_event} with carpools: {new_event.carpools}')

        except Exception as e:  # i don't really know how this happens but its good to have
            logger.debug(e)
            return redirect(
                url_for("main.create_event_page", message='Something went wrong. Make sure that all inputs are valid.'))

        flash("Your event, {}, was created successfully!".format(event_info["name"]), "success")
        return redirect(url_for('main.events_page'))
    else:
        return render_template('error_template.html', main_message='Go Away', sub_message='You should not be here.',
                               user=current_user)


@main_blueprint.route('/driver-signup/<carpool_index>', methods=['GET', 'POST'])
@driver_required
@requires_auth_key
def driver_carpool_signup_page(carpool_index):
    """
    Page that drivers go to when they are signing up for a carpool. Still needs a check for sign in
    :carpool_index index of the carpool to be signed up for
    """
    if request.method == 'GET':
        if current_user.is_authenticated:
            carpool = Carpool.query.get(carpool_index)
            if carpool.driver is not None:
                logger.info(f"Carpool {carpool} already has a driver")
                return redirect(url_for('main.event_page', event_index=carpool.event_index))
            carpool.driver = current_user
            carpool.num_passengers = current_user.num_seats
            carpool.driver_index = current_user.id
            db.session.commit()
            logger.info(f'{current_user} signed up for carpool {carpool}')
            # messaging the passengers in region that requested a carpool
            for passenger in [passenger for passenger in carpool.event.passengers_needing_ride if
                              passenger.region_name == carpool.region_name]:
                if passenger.region_name == carpool.region_name:
                    tasks_.send_async_email.delay(
                        passenger.email_address,
                        'Carpool Request',
                        f'Hi {passenger.first_name.capitalize()},\n\nYour request for a carpool has been fulfilled! Check the events page to sign up.\n\nThanks,\nCarpool Manager.'
                    )
            # removing the passengers needing a ride in the region
            for passenger in [passenger for passenger in carpool.event.passengers_needing_ride if
                              passenger.region_name == carpool.region_name]:
                carpool.event.passengers_needing_ride.remove(passenger)
                logger.info(f'passenger {passenger} removed from carpool {carpool}.')
            db.session.commit()

            return render_template('error_template.html', main_message='Success!',
                                   sub_message='You have signed up to drive! Thank you for helping the team!',
                                   user=current_user)

        carpool = Carpool.query.get(carpool_index)
        return render_template('driver_carpool_signup_template.html', carpool=carpool, message='Sign up for a carpool!',
                               user=current_user)
    if request.method == 'POST':
        try:
            carpool = Carpool.query.get(carpool_index)
        except Exception as e:
            logger.critical(e)
            logger.warning('This should never happen : (')
        driver = User.query.filter_by(first_name=request.form['firstname'].lower(
        ), last_name=request.form['lastname'].lower()).first()
        logger.debug(driver)
        if driver is None:
            return render_template('driver_carpool_signup_template.html', carpool=carpool,
                                   message='That driver does not exist. Please try again.', user=current_user)
        else:
            carpool.driver = driver
            try:
                carpool.num_passengers = int(
                    request.form['numberofpassengers'])
            except Exception as e:
                logger.debug(e)

            db.session.commit()
            logger.info(f'Driver {driver} signed up for carpool {carpool}')
            return render_template('error_template.html', main_message='Success!',
                                   sub_message='You have successfully signed up for a carpool!', user=current_user)


@main_blueprint.route('/passenger-carpool-signup/<carpool_index>')
def passenger_carpool_signup_page(carpool_index):
    """
    Page for the passenger to sign up for a carpool
    """

    if request.method == 'GET':
        if current_user.is_authenticated:
            carpool = Carpool.query.get(carpool_index)
            if carpool.driver is None:
                return redirect(url_for('main.event_page', event_index=carpool.event_index))
            carpool.passengers.append(current_user)
            db.session.commit()
            logger.info(f'{current_user} signed up for carpool {carpool}')
            return render_template('error_template.html', main_message='Success!',
                                   sub_message='You have signed up for a carpool!', user=current_user)
        else:
            carpool = Carpool.query.get(carpool_index)
            return render_template('passenger_carpool_signup_template.html', carpool=carpool,
                                   message='Sign up for a carpool!', user=current_user)

    if request.method == 'POST':
        carpool = Carpool.query.get(carpool_index)
        passenger = User.query.filter_by(first_name=request.form['firstname'].lower(
        ), last_name=request.form['lastname'].lower()).first()
        logger.debug(passenger)
        if passenger is None:
            return redirect(url_for('auth.register_new_passenger_page'))
            # try:
            #     new_passenger = User(
            #         first_name=request.form['firstname'].lower(),
            #         last_name=request.form['lastname'].lower(),
            #         email_address=request.form['email'].lower(),
            #         phone_number=request.form['phonenumber'],
            #         emergency_contact_number=request.form['emergencycontact'],
            #         emergency_contact_relation=request.form['emergencycontactrelation'],
            #         extra_information=request.form['note']
            #     )

            #     carpool.passengers.append(new_passenger)
            #     db.session.add(new_passenger)
            #     db.session.commit()
            #     logger.info('new temp passenger created')

            #     send_async_email.delay(carpool.driver.email_address, 'New Passenger Signup', f'New passenger {new_passenger} signed up for carpool {carpool}!')

            #     return render_template('error_template.html', main_message='Success!', sub_message='A new passenger was registered, and you have successfully signed up for a carpool!', user=current_user)

            # except Exception as e:
            #     logger.debug(e)
            #     return render_template('passenger_carpool_signup_template.html', carpool=carpool, message='There was an error registering a new passenger. Try again.', user=current_user)

        else:
            passenger.extra_information = request.form['note']
            carpool.passengers.append(passenger)
            db.session.add(passenger)
            db.session.commit()
            logger.info('existing passenger added to carpool without sign in')

            # send email to driver about new passenger
            send_async_email.delay(carpool.driver.email_address, 'New Passenger Sign Up',
                                   f'New passenger {passenger} signed up for carpool {carpool}!')
            return render_template('error_template.html', main_message='Success!',
                                   sub_message='The passenger already existed in the database. Please register to use all features.',
                                   user=current_user)

    carpool = Carpool.query.get(carpool_index)
    return str(carpool.passengers[0].carpools) + str(len(carpool.passengers))


@main_blueprint.route('/manage-carpools', methods=['GET', 'POST'])
@login_required
def manage_carpools_page():
    """
    Page that allows for the management of carpools
    """

    try:
        driver_carpools = current_user.driver_carpools
        logger.debug(driver_carpools)
        driver_carpools = [carpool for carpool in driver_carpools if carpool.event.date >
                           datetime.datetime.now() - datetime.timedelta(hours=30)]
        logger.debug(driver_carpools)
    except AttributeError as e:
        logger.debug('user is not a driver')
        logger.debug(e)
        driver_carpools = []
    passenger_carpools = current_user.passenger_carpools
    logger.debug(passenger_carpools)
    passenger_carpools = [carpool for carpool in passenger_carpools if carpool.event.date >
                          datetime.datetime.now() - datetime.timedelta(hours=30)]
    logger.debug(passenger_carpools)

    return render_template('manage_carpools_template.html', user=current_user, driver_carpools=driver_carpools,
                           passenger_carpools=passenger_carpools)


@main_blueprint.route('/passenger/<id>')
@login_required
@requires_auth_key
def passenger_page(id):
    """
    Page that allows for the viewing of passenger information. Is only accessible if the person is logged in 
    and has an upcoming carpool with the person in it.
    """

    current_user_carpools = Carpool.query.filter_by(
        driver_index=current_user.id).all()  # TODO:filter by current user and upcoming
    current_user_carpools = [carpool for carpool in current_user_carpools if carpool.event.end_time >
                             datetime.datetime.now() + datetime.timedelta(hours=5)]

    # checking if the person is able to see
    for carpool in current_user_carpools:
        if (carpool.event.start_time) > datetime.datetime.now():
            for passenger in carpool.passengers:
                if (passenger.id == id):
                    return render_template('passenger_template.html', user=current_user, passenger=passenger)

    passenger = User.query.filter_by(id=id).first()
    if current_user.is_admin() > 1 and session["organization"] in [organization.id for organization in passenger.organizations]:
        return render_template('passenger_template.html', user=current_user, passenger=passenger)

    if current_user == passenger:
        return render_template('passenger_template.html', user=current_user, passenger=passenger)

    # if the person is not able to see the passenger

    return render_template('error_template.html', main_message='Go Away',
                           sub_message='You do not have access to see the passenger.', user=current_user)


@main_blueprint.route('/safety')
def safety():
    """
    Be safe
    """
    return render_template('safety.html', user=current_user)


@main_blueprint.route('/request-carpool/<event_index>/<region_name>', methods=['GET', 'POST'])
def passenger_carpool_request_page(event_index, region_name): # temp disabled
    """
    Page for a passenger to request a carpool
    event_index: index of the event
    """
    if request.method == 'GET':
        try:
            event = Event.query.get(event_index)
        except Exception as e:
            logger.debug(e)
            logger.info('Event {} not found'.format(event_index))
            return redirect(url_for('main.events_page'))

        if current_user.is_authenticated:
            event.passengers_needing_ride.append(
                current_user)
            db.session.commit()
            logger.info('Passenger {} added to event as needing ride {}'.format(
                current_user, event))

            # email the people in the area
            # finding the drivers in the area -- yes i can do this if i set lazy to dynamic but thats a lot of work
            drivers_in_area = [driver for driver in User.query.filter_by(region_name=region_name).all(
            ) if driver not in [carpool.driver for carpool in event.carpools]]
            for driver in drivers_in_area:
                send_async_email.delay(driver.email_address, 'Passenger needs ride', f"""
                        Hello {driver.first_name.capitalize()} {driver.last_name.capitalize()}, \n\n
                        A passenger in your area needs a ride to the event {event.name}. If you are going to the event,
                        please consider signing up to give them a ride.
                        """)

            logger.info('finished notifying drivers.')
            return redirect(url_for('main.event_page', event_index=event.index))
        else:
            return redirect(url_for('auth.generic_register_page'))
            return render_template('passenger_carpool_request_template.html', event=event, user=current_user,
                                   regions=regions, region_name=region_name)
    if request.method == 'POST':
        return
        # making sure that the event exists ...

        try:
            event = Event.query.get(event_index)
        except Exception as e:
            logger.debug(e)
            logger.info('Event {} not found'.format(event_index))
            return redirect(url_for('main.events_page'))

        # getting the form data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        email_address = request.form['email']
        phone_number = request.form['phonenumber']
        region_name = request.form['region']

        # making sure that the user is not already in the database
        passenger = User.query.filter_by(
            first_name=first_name, last_name=last_name).first()
        if passenger is not None:
            logger.info('Passenger {} already exists'.format(passenger))
            return render_template('error_page_template', main_message='You are already in the database',
                                   sub_message='Please log in to request a carpool.')

        # creating the passenger
        passenger = User(first_name=first_name, last_name=last_name,
                         email_address=email_address, phone_number=phone_number, region_name=region_name)
        db.session.add(passenger)
        db.session.commit()
        logger.info('Passenger {} created'.format(passenger))

        # adding the passenger to the event
        event.passengers_needing_ride.append(passenger)
        db.session.commit()

        # emailing the people in the region
        # finding the drivers in the area that haven't signed up to carpool
        drivers_in_area = [driver for driver in Driver.query.filter_by(region_name=region_name).all(
        ) if driver not in [carpool.driver for carpool in event.carpools]]

        for driver in drivers_in_area:
            send_async_email.delay(driver.email_address, 'Passenger Needs Ride', f"""
                    Hello {driver.first_name.capitalize()} {driver.last_name.capitalize()}, \n\n
                    A passenger in your area needs a ride to the event {event.name}. If you are going to the event,
                    please consider signing up to give them a ride.
                    """)

        logger.info('finished notifying drivers.')
        return redirect(url_for('main.event_page', event_index=event.index))


@main_blueprint.route('/user-route-summary/<carpool_index>')
@login_required
def view_carpool_page(carpool_index):
    """
    Page to view a carpool
    """
    carpool = GeneratedCarpool.query.get(carpool_index)
    if carpool is None:
        logger.info('Carpool {} not found'.format(carpool_index))
        return redirect(url_for('main.events_page'))

    # if (current_user.id != carpool.driver.id) and (current_user not in carpool.passengers):
    #     logger.info('User {} is not authorized to view {}'.format(current_user, carpool_index))
    #     return redirect(url_for('main.events_page')) TODO

    return render_template('user_route_summary_template.html', carpool=carpool, user=current_user)


@main_blueprint.route('/view-organization')
@login_required
def view_organization_page():
    """
    Page to view the organization
    """
    return render_template('view_organization_template.html', user=current_user, organization=Organization.query.get(session['organization']))

@main_blueprint.route('/about')
def about_page():
    """
    Page to view information about the app
    """
    return render_template('about_template.html', user=current_user)

@main_blueprint.route('/contact')
def contact_page():
    """
    Page to contact the developers
    """
    return render_template('contact_template.html', user=current_user)


@main_blueprint.route('/add_new_organization', methods=['GET', 'POST'])
@login_required
def add_new_organization_page():
    """
    Page to add a new organization
    """
    if request.method == "GET":
        return render_template('add_new_organization_template.html', user=current_user)
    if request.method == "POST":
        if request.form.get("neworganizationname") is not None:
            new_organization = Organization(name=request.form.get("neworganizationname"), description=request.form.get("neworganizationdescription"), access_key=secrets.token_urlsafe(8))
            db.session.add(new_organization)
            current_user.organizations.append(new_organization)
            db.session.commit()
            session["organization"] = new_organization.id
            current_user.set_admin_level(2)
            flash("Your organization, {}, was created successfully!".format(new_organization.name), "success")
            return redirect(url_for("main.home_page"))
        else:
            new_organization = Organization.query.filter_by(access_key=request.form.get("organizationkey")).first()
            if new_organization is None:
                flash("That organization does not exist. Please try again.", "error")
                return redirect(url_for("main.add_new_organization_page"))
            else:
                current_user.organizations.append(new_organization)
                db.session.commit()
                session["organization"] = new_organization.id
                flash("You have successfully joined {}!".format(new_organization.name), "success")
                return redirect(url_for("main.home_page"))





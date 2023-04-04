import datetime

from carpooling import create_app
from carpooling import db
import logging

from carpooling.logic.carpool_matching.evaluate_best_solution_one_way import evaluate_best_solution_one_way, \
    DRIVER_WAITING_TIME
from carpooling.logic.carpool_matching.general_functions import load_people_from_sql
from carpooling.models import CarpoolSolution, GeneratedCarpool, GeneratedCarpoolPart, Event, User
import click
from flask.cli import with_appcontext
import pandas as pd

logger = logging.getLogger(__name__)


@click.command('test-address-matching')
@click.argument('type_', type=click.Choice(['to', 'from', 'both']))
@with_appcontext
def address_matching_test_command(type_):
    address_matching_test_implementation(type_)


def address_matching_test_command_debug_mode(type_: str):
    app = create_app()
    with app.app_context():
        address_matching_test_implementation(type_)


def address_matching_test_implementation(type_: str):
    people = load_people_from_sql(1)
    event = Event.query.first()

    solution = evaluate_best_solution_one_way(people, event.destination.id, type_, use_placeid=False,
                                               return_='one_solution')  # need to drop the addresses
    # calculating all the specific times
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
    logger.debug(f'Writing solution to the database')
    new_solution = CarpoolSolution(
        utility_value=solution.total_utility_value,
        event_id=event.index,
        is_best=False,
        type=type_
    )
    db.session.add(new_solution)

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
        db.session.add(new_carpool)
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
            db.session.add(new_part)
    db.session.commit()

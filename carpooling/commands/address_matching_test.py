from carpooling import create_app
from carpooling import db
from carpooling.logic.carpool_matching import load_people, evaluate_best_solution_to
from io import StringIO
import logging

from carpooling.logic.carpool_matching.evaluate_best_from_solution import evaluate_best_solution_from
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
    # with open('carpooling/logic/example_signup_csv.csv', 'r') as f:
    #     people = load_people(StringIO(f.read()))
    people = load_people_from_sql(1)
    event = Event.query.first()
    solutions = None
    if type_ == 'to':
        solutions = evaluate_best_solution_to(people, 1, use_placeid=False, return_=False)  # need to drop the addresses
    elif type_ == 'from':
        solutions = evaluate_best_solution_from(people, 1, use_placeid=False, return_=False)  # need to drop the addresses
    logger.info(solutions)
    if type(solutions) is not list:
        solutions = {0: solutions}
    # writing the solutions to the database
    for _, solution in solutions.items():
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
                carpool_solution_id=new_solution.id,
                from_address_id=carpool.route[0],
                to_address_id=carpool.route[-1],
                driver_id=driver_id,  # yes this is bad
                event_id=event.index,
            )
            for passenger in carpool.driver.driver_history[1:]:
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
                )
                db.session.add(new_part)
    db.session.commit()


def address_matching_test_command_debug_mode(type_: str):
    app = create_app()
    with app.app_context():
        people = load_people_from_sql(1)
        event = Event.query.first()
        if type_ == 'to':
            solutions = evaluate_best_solution_to(people, 1, use_placeid=False, return_='all_solutions')  # need to drop the addresses
        if type_ == 'from':
            solutions = evaluate_best_solution_from(people, 1, use_placeid=False, return_='all_solutions')  # need to drop the addresses
        # writing the solutions to the database
        for _, solution in solutions.items():
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
                    carpool_solution_id=new_solution.id,
                    from_address_id=carpool.route[0],
                    to_address_id=carpool.route[-1],
                    driver_id=driver_id,  # yes this is bad
                    event_id=event.index,
                )
                for passenger in carpool.driver.driver_history[1:]:
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
                    )
                    db.session.add(new_part)
        db.session.commit()


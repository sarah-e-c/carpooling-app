from carpooling import create_app
from carpooling import db
from carpooling.logic.carpool_matching import load_people, evaluate_best_solution_to
from io import StringIO
import logging
from carpooling.models import CarpoolSolution, GeneratedCarpool, GeneratedCarpoolPart, Event, Passenger
import click
from flask.cli import with_appcontext
import pandas as pd

logger = logging.getLogger(__name__)

@click.command('test-address-matching')
@with_appcontext
def address_matching_test_command():
        # with open('carpooling/logic/example_signup_csv.csv', 'r') as f:
        #     people = load_people(StringIO(f.read()))
        people = load_people(StringIO(pd.read_sql('select * from event_carpool_signups WHERE event_id=1', db.engine).to_csv()))
        event = Event.query.first()
        solutions = evaluate_best_solution_to(people, 1, use_placeid=False, return_=False) # need to drop the addresses
        logger.info(solutions)
        if type(solutions) is not list:
            solutions = {0: solutions}
        # writing the solutions to the database
        for _, solution in solutions.items():
            new_solution = CarpoolSolution(
                utility_value=solution.total_utility_value,
                event_id=event.index,
                is_best=False
            )
            db.session.add(new_solution)

            for carpool in solution.carpools:
                driver_id = Passenger.query.get(
                carpool.driver.id_).user.driver_profile.index
                new_carpool = GeneratedCarpool(
                    carpool_solution_id=new_solution.id,
                    from_address_id=carpool.route[0],
                    to_address_id=carpool.route[-1],
                    driver_id=driver_id,  # yes this is bad
                    event_id=event.index,
                )
                for passenger in carpool.driver.driver_history[1:]:
                    new_carpool.passengers.append(Passenger.query.get(passenger.id_))
                db.session.add(new_carpool)
                for i in range(len(carpool.route) - 1):
                    new_part = GeneratedCarpoolPart(
                        generated_carpool=new_carpool,
                        from_address_id=carpool.route[i],
                        to_address_id=carpool.route[i+1],
                        driver_id=driver_id,  # yes this is bad
                        idx=i,
                        passengers=new_carpool.passengers,
                    )
                    db.session.add(new_part)
        db.session.commit()

def address_matching_command_test_debug_mode():
    app = create_app()
    with app.app_context():
        with open('carpooling/logic/example_signup_csv.csv', 'r') as f:
            people = load_people(StringIO(f.read()))
        event = Event.query.first()
        solutions = evaluate_best_solution_to(people, 1, use_placeid=False, return_=False) # need to drop the addresses
        # writing the solutions to the database
        for _, solution in solutions.items():
            new_solution = CarpoolSolution(
                utility_value=solution.total_utility_value,
                event_id=event.index,
                is_best=False
            )
            db.session.add(new_solution)

            for carpool in solution.carpools:
                driver_id = Passenger.query.get(
                carpool.driver.id_).user.driver_profile.index
                new_carpool = GeneratedCarpool(
                    carpool_solution_id=new_solution.id,
                    from_address_id=carpool.route[0],
                    to_address_id=carpool.route[-1],
                    driver_id=driver_id,  # yes this is bad
                    event_id=event.index,
                )
                for passenger in carpool.driver.driver_history[1:]:
                    new_carpool.passengers.append(Passenger.query.get(passenger.id_))
                db.session.add(new_carpool)
                for i in range(len(carpool.route) - 1):
                    new_part = GeneratedCarpoolPart(
                        generated_carpool=new_carpool,
                        from_address_id=carpool.route[i],
                        to_address_id=carpool.route[i+1],
                        driver_id=driver_id,  # yes this is bad
                        idx=i,
                        passengers=new_carpool.passengers,
                    )
                    db.session.add(new_part)
        db.session.commit()

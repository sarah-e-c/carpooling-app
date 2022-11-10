from carpooling import create_app
from carpooling import db
from carpooling.logic.matcher import load_people, evaluate_best_solution_to
from io import StringIO
import logging
from carpooling.models import CarpoolSolution, GeneratedCarpool, GeneratedCarpoolPart, Event, Passenger
import click
from flask.cli import with_appcontext

logger = logging.getLogger(__name__)

@click.command('test-address-matching')
@with_appcontext
def test_address_matching_command():
    with open('carpooling/logic/example_signup_csv.csv', 'r') as f:
        people = load_people(StringIO(f.read()))
    event = Event.query.first()
    solutions = evaluate_best_solution_to(people, 1)
    logger.info(solutions)
    # writing the solutions to the database
    for _, solution in solutions.items():
        new_solution = CarpoolSolution(
            utility_value=solution.total_utility_value,
            event_id=event.index,
            is_best=False
        )
        db.session.add(new_solution)
        driver_id = Passenger.get(
            carpool.driver.id_).user.driver_profile.index
        for carpool in solution.carpools:
            new_carpool = GeneratedCarpool(
                carpool_solution_id=new_solution.id,
                from_address_id=carpool.route[0],
                to_address_id=carpool.route[-1],
                driver_id=driver_id,  # yes this is bad
                event_id=event.index,
                solution=new_solution
            )
            for passenger in carpool.driver_history[1:]:
                new_carpool.passengers.append(Passenger.get(passenger.id_))
            db.session.add(new_carpool)
            for i in range(len(carpool.routes) - 1):
                new_part = GeneratedCarpoolPart(
                    generated_carpool=new_carpool,
                    from_address_id=carpool.routes[i],
                    to_address_id=carpool.routes[i+1],
                    driver_id=driver_id,  # yes this is bad
                    event_id=event.index,
                    solution=new_solution,
                    idx=i,
                    passengers=new_carpool.passesngers,
                )
                db.session.add(new_part)
    db.session.commit()

from carpooling import create_app
from carpooling import db
from carpooling.logic.matcher import load_people, evaluate_best_solution
from io import StringIO


class TestAddressMatching():
    """
    Initialize the database
    """
    def run(self, is_testing=True):
        """
        run the command.
        """
        app = create_app()
        with app.app_context() as f:
            db.create_all()
            with open('carpooling/logic/example_signup_csv.csv', 'r') as f:
                people = load_people(StringIO(f.read()))
            solution = evaluate_best_solution(people, 0)
            print(solution)
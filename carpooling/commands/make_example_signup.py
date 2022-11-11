from flask.cli import with_appcontext
import click
from carpooling.models import Driver, User, Passenger, Address
import csv
import logging

logger = logging.getLogger(__name__)


@click.command('make-example-signup')
@with_appcontext
def make_example_signup_command():
    eligible_users = Passenger.query.join(Address, Address.passenger_id == Passenger.index).filter(Address.state == 'CA').all()


    # eligible_users_2 = User.query.join(Passenger).join(Address, Address.id == Passenger.address_id).all()
    # for user in eligible_users_2:
    #     print(user)

    with open('carpooling/logic/example_signup_csv.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['first name', 'last name', 'willing to drive', 'needs ride'])
        for user in eligible_users:
            writer.writerow([user.first_name, user.last_name, 'yes' if user.user[0].driver_profile else 'no', 'yes'])
    
    logger.info('wrote example signup csv')

        



    
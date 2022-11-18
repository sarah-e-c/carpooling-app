from flask.cli import with_appcontext
import click
from carpooling.models import Address
from carpooling.models import User as Passenger
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
        writer.writerow(['first_name', 'last_name', 'willing_to_drive', 'needs_ride'])
        for user in eligible_users:
            writer.writerow([user.first_name, user.last_name, 'yes' if user.user.driver_profile else 'no', 'yes'])
    
    logger.info('wrote example signup csv')

        



    
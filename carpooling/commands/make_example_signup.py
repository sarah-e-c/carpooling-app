from flask.cli import with_appcontext
import click

from carpooling import db
from carpooling.models import Address, User, AddressUserLink, EventCarpoolSignup
import csv
import logging

logger = logging.getLogger(__name__)


@click.command('make-example-signup')
@with_appcontext
def make_example_signup_command():
    """
    This command creates a signup for the example event.
    It also writes it to the database
    """
    eligible_users = User.query.join(AddressUserLink).join(Address).filter(Address.state == 'CA').all()

    # eligible_users_2 = User.query.join(Passenger).join(Address, Address.id == Passenger.address_id).all()
    # for user in eligible_users_2:
    #     print(user)

    with open('carpooling/logic/example_signup_csv.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['first_name', 'last_name', 'willing_to_drive', 'needs_ride'])
        for user in eligible_users:
            writer.writerow([user.first_name, user.last_name, 'yes' if user.num_seats else 'no', 'yes'])
            new_signup = EventCarpoolSignup(
                event_id=1,
                user_id=user.id,
                willing_to_drive=True if user.num_seats is not None else False,
                needs_ride=True,
            )
            db.session.add(new_signup)
    db.session.commit()

    logger.info('wrote example signup csv')

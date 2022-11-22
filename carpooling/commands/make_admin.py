from carpooling import create_app, db
from carpooling import models
from flask.cli import with_appcontext
import click


@click.command('make-admin')
@click.argument('first_name')
@click.argument('last_name')
@with_appcontext
def make_admin_command(first_name, last_name):
    """
    Method you can hard code to make someone admin
    """
    user = models.User.query.filter_by(first_name=first_name, last_name=last_name).first()
    user.is_admin = 2
    db.session.commit()

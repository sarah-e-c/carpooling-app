import datetime

from flask import current_app

from carpooling import db
from carpooling import models
from carpooling import create_app
import secrets

class InitDbCommand():
    """
    Initialize the database
    """
    def run(self, is_testing=True):
        """
        run the command.
        """
        app = create_app()
        with app.app_context() as f:
            init_db(is_testing=is_testing)

def init_db(is_testing=True):
    db.create_all()
    create_regions()
    create_first_key()


def create_regions():
    south_region = models.Region(
        name='West Henrico',
        dropoff_location='Short Pump Town Center',
        color='#8B0000',
    )
    henrico_region = models.Region(
        name='Central',
        dropoff_location='Capital Building',
        color='#FF8C00',
    )

    eastern_region = models.Region(
        name='Varina and New Kent',
        dropoff_location='New Kent High School',
        color='#FF00FF',
    )

    richmond_region = models.Region(
        name='Chesterfield',
        dropoff_location='360x288 Target',
        color='#FFFF00',
    )

    chesterfield_region = models.Region(
        name='I-95',
        dropoff_location='Southpark Mall',
        color='#00FF00',
    )
    west_region = models.Region(
        name='Goochland and Powhatan',
        dropoff_location='Audi Richmond',
        color='#00FFFF',)

    db.session.add(south_region)
    db.session.add(henrico_region)
    db.session.add(richmond_region)
    db.session.add(west_region)
    db.session.add(eastern_region)
    db.session.add(chesterfield_region)
    db.session.commit()

def create_first_key():
    first_key = models.AuthKey(
        key = secrets.token_hex(4)
    )
    db.session.add(first_key)
    db.session.commit()
import datetime

from flask import current_app
from flask.cli import with_appcontext

from carpooling import db
from carpooling import models
from carpooling import create_app
import secrets
import click


@click.command('init-db')
@with_appcontext
def init_db_command(is_testing=True):
    db.create_all()
    create_regions()
    create_first_key()
    create_first_destination()


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

def create_first_destination():
    destination_address = models.Address(
        latitude = 37.5579166667,
        longitude = -77.27135,
        code=0,
        address_line_1 = '1000 N Lombardy Street',
        city = 'Richmond',
        state = 'VA',
        zip_code = '23220',
    )
    first_destination = models.Destination(
        name='Maggie L. Walker Governor\'s School',
        address=destination_address,
    )
    db.session.add(first_destination)
    db.session.commit()
"""
Tests to test all 3 address matching functions
"""
import pytest
import unittest.mock as mock
from carpooling.models import EventCarpoolSignup
from testing.unit import client, app
import logging
from carpooling.logic.carpool_matching import evaluate_best_solution_to
import json
from carpooling.logic.carpool_matching import load_people
from carpooling import db
from io import StringIO
import pandas as pd
import csv

logger=logging.getLogger(__name__)

def get_mocked_address_data():
    """
    Mocks the requests.get function to return a json object with the address data
    """
    # assert url.startswith('https://maps.googleapis.com/maps/api/geocode/json?address=')

    pass


@mock.patch('requests.get')
def test_address_matching_to(client, app):
    """
    Tests the address matching function with the to address
    """
    with mock.patch('requests.get') as mock_get:
        with app.app_context():
            with open('testing/example_data/google_api_data/distance_matrix_example_1668711934.321238.json', 'r') as f:
                mock_get.return_value.json.return_value = json.load(f)
                mock_get.return_value.status_code = 200
                mock_get.return_value.ok = True
            
            signups = EventCarpoolSignup.query.filter_by(event_id=1).all()
            string_io = StringIO()
            writer = csv.writer(string_io)
            writer.writerow(['first_name', 'last_name', 'willing_to_drive', 'needs_ride'])
            for signup in signups:
                writer.writerow([signup.passenger.first_name, signup.passenger.last_name, signup.willing_to_drive, signup.needs_ride])
            string_io.seek(0)

            solution = evaluate_best_solution_to(load_people(string_io), destination_id=1, use_placeid=False)
        

    assert client.get('/').status_code == 200
    assert client.get('/events').status_code == 200
    
    logger.info(solution)


    pass

def test_address_matching_from():
    pass

def test_address_matching_both():
    pass



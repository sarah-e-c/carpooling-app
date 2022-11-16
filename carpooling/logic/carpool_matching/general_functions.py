import logging
from carpooling.models import Address, DistanceMatrix, Passenger, Destination
from .data_classes import API_KEY, PLACEHOLDER_HIGH_VALUE, MAX_TIME, Person
import requests
import numpy as np
import pandas as pd
from carpooling import db
import json
import time
from io import StringIO
from sqlalchemy import and_



logger = logging.getLogger(__name__)



def get_distance_matrix(origins, destinations, use_placeid=True) -> dict:
    """
    Call the Google Distance Matrix API to get the distance between all of the addresses.
    :param origins: the ids of the addresses in the database
    :param destinations: the ids of the addresses in the database
    """
    return_dict = {}
    if len(origins) * len(destinations) > 100:
        logger.warning(
            'too many origins and destinations, splitting into chunks')
        for origin_iter in range(0, len(origins), 10):
            for j in range(0, len(destinations), 10):
                origins_chunk = origins[origin_iter:origin_iter+10]
                destinations_chunk = destinations[j:j+10]
                if use_placeid:
                    origins_chunk_str = [f'place_id:{origin}' for origin in list(
                        Address.query.filter(Address.id.in_(origins_chunk)).with_entities(Address.code))]
                    destinations_chunk_str = [f'place_id:{destination}' for destination in list(
                        Address.query.filter(Address.id.in_(destinations_chunk)).with_entities(Address.code))]
                else:
                    origins_chunk_str = [f'{origin.address_line_1} {origin.city} {origin.state} {origin.zip_code}' for origin in list(
                        Address.query.filter(Address.id.in_(origins_chunk)).all())]
                    destinations_chunk_str = [f'{destination.address_line_1} {destination.city} {destination.state} {destination.zip_code}' for destination in list(
                        Address.query.filter(Address.id.in_(destinations_chunk)).all())]
                origins_str = '|'.join(origins_chunk_str)
                destinations_str = '|'.join(destinations_chunk_str)
                url = f'https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&origins={origins_str}&destinations={destinations_str}&key={API_KEY}'
                response = requests.get(url)
                response_json = response.json()
                with open(f"carpooling/logic/examples/distance_matrix_example_{time.time()}.json", "w") as f:
                    json.dump(response_json, f)
                if response.status_code != 200:
                    logger.error(f'error with request: {response.status_code}')
                    logger.error(response.text)
                    raise Exception('error with request')
                if response_json['status'] != 'OK':
                    logger.error(
                        f'error with request: {response_json["status"]}')
                    logger.error(response.text)
                    raise Exception('error with request')
                for p, row in zip(origins_chunk, response_json["rows"]):
                    if type(return_dict.get(p)) != dict:
                        return_dict[p] = {}
                    logger.info(f'origin: {p}, {row}')
                    for l, element in zip(destinations_chunk, row['elements']):
                        try:
                            return_dict[p][l] = {}
                            return_dict[p][l]["kilos"] = element["distance"]["value"]
                            return_dict[p][l]["seconds"] = element["duration"]["value"]
                        except Exception as e:
                            logger.warning(
                                'An address was not found, skipping')
                            logger.warning(e)

        logger.info(return_dict)
        return return_dict

    else:  # the number of origins and destinations is less than 100
        if use_placeid:
            origins_for_url = [address.code for address in list(
                Address.query.filter(Address.id.in_(origins)).all())]
            origins_for_url = ["place_id:" +
                               origin for origin in origins_for_url]
            destinations_for_url = [address.code for address in list(
                Address.query.filter(Address.id.in_(destinations)).all())]
            destinations_for_url = [
                "place_id:" + destination for destination in destinations_for_url]
            origins_for_url = '|'.join(origins_for_url)
            destinations_for_url = '|'.join(destinations_for_url)
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origins_for_url}&destinations={destinations_for_url}&key=AIzaSyD_JtvDeZqiy9sxCKqfggODYMhuaeeLjXI"
            headers = {}
        else:  # not using placeid
            origins_for_url = [f"{address.address_line_1} {address.city} {address.state} {address.zip_code}" for address in list(
                Address.query.filter(Address.id.in_(origins)).all())]
            origins_for_url = '|'.join(origins_for_url)
            destinations_for_url = [f"{address.address_line_1} {address.city} {address.state} {address.zip_code}" for address in list(
                Address.query.filter(Address.id.in_(destinations)).all())]
            destinations_for_url = '|'.join(destinations_for_url)
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origins_for_url}&destinations={destinations_for_url}&key=AIzaSyD_JtvDeZqiy9sxCKqfggODYMhuaeeLjXI"
            headers = {}

        response = requests.get(url, headers=headers).json()
        # TODO get this make the idea
        for origin_iter, row in zip(origins, response["rows"]):
            if type(return_dict.get(origin_iter)) != dict:
                return_dict[origin_iter] = {}
            for destination_iter, element in zip(destinations, row['elements']):
                try:
                    return_dict[origin_iter][destination_iter] = {}
                    return_dict[origin_iter][destination_iter]["kilos"] = element["distance"]["value"]
                    return_dict[origin_iter][destination_iter]["seconds"] = element["duration"]["value"]
                except KeyError as e:
                    logger.warning('An address was not found, skipping')

    return return_dict


def fill_distance_matrix(rsvp_list: list, destination_id: int, use_placeid=True) -> list[pd.DataFrame]:
    """
    Method that uses Google Maps API to get the distances between all points.
    :param rsvp_list: the list of Person objects to use
    """
    # TODO only get the values that are reasonably close to each other already.
    # We don't need a northside distance to a southside distance.
    # If its in the algorithm, then just input a high value

    destination_id = Destination.query.get(destination_id).address.id
    logger.info(destination_id)

    # query addresses
    used_addresses_ids = [address.id for address in Address.query.filter(
        Address.passenger_id.in_([user.id_ for user in rsvp_list])).all()]
    used_addresses_ids.append(destination_id)

    # filling in the distance matrix
    kilos_matrix = pd.DataFrame(
        index=used_addresses_ids, columns=used_addresses_ids)
    seconds_matrix = pd.DataFrame(
        index=used_addresses_ids, columns=used_addresses_ids)
    uu = 0
    for origin in used_addresses_ids:
        for destination in used_addresses_ids:
            if origin != destination:
                try:
                    values = DistanceMatrix.query.filter_by(
                        origin_id=origin, destination_id=destination).first()
                    logger.debug(values)
                    kilos_matrix.loc[origin, destination] = values.kilos
                    seconds_matrix.loc[origin, destination] = values.seconds
                except AttributeError as e:
                    uu += 1
                    kilos_matrix.loc[origin, destination] = np.nan
                    seconds_matrix.loc[origin, destination] = np.nan
                    logger.warning(f'no values for {origin} and {destination}')
            else:
                kilos_matrix.loc[origin, destination] = 0
                # doing this because its harder to detect 0s
                seconds_matrix.loc[origin, destination] = 0

    logger.info(f'number of nan values: {uu}')
    # step 1: determining which ones are new. We will do 3 calls to the api. Here is a handy graphic:
    """
                    new address new address old address old address
        old address XXXXXXXXXXX XXXXXXXXXXX YYYYYYYYYYY YYYYYYYYYYY
        old address XXXXXXXXXXX XXXXXXXXXXX YYYYYYYYYYY YYYYYYYYYYY
        new address XXXXXXXXXXX XXXXXXXXXXX XXXXXXXXXXX XXXXXXXXXXX
        new address XXXXXXXXXXX XXXXXXXXXXX XXXXXXXXXXX XXXXXXXXXXX
    """
    new_addresses = [address for address in kilos_matrix.index if kilos_matrix.loc[:, address].apply(
        lambda x: 0 if x in [0, np.nan] else 5).sum() < 5]  # all of them are null
    old_addresses = [address for address in kilos_matrix.index if not kilos_matrix.loc[:, address].apply(
        lambda x: 0 if x in [0, np.nan] else 5).sum() < 5]  # at least one is not null
    logger.debug(f'New addresses:  {new_addresses}')
    logger.debug(f'Old addresses: {old_addresses}')
    # getting the new values (if needed)

    if kilos_matrix.isnull().values.any():
        # call 1: origin is new, destination is new
        new_points = get_distance_matrix(
            new_addresses, new_addresses, use_placeid=use_placeid)
        # call 2: origin is new, destination is old

        # call 3: origin is old, destination is new

        for origin in new_points.keys():
            for destination in new_points[origin].keys():
                if origin != destination:
                    try:
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=new_points[origin][destination]['kilos'], seconds=new_points[origin][destination]['seconds']))
                        db.session.commit()
                        logger.info(
                            f'Added {origin} to {destination} to the database')
                        kilos_matrix.loc[origin,
                                         destination] = new_points[origin][destination]['kilos']
                        seconds_matrix.loc[origin,
                                           destination] = new_points[origin][destination]['seconds']
                    except KeyError as e:
                        logger.warning(
                            'An address was not found. Imputing a high value')
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=PLACEHOLDER_HIGH_VALUE, seconds=PLACEHOLDER_HIGH_VALUE))
                        kilos_matrix.loc[origin,
                                         destination] = PLACEHOLDER_HIGH_VALUE
                        seconds_matrix.loc[origin,
                                           destination] = PLACEHOLDER_HIGH_VALUE
                else:
                    db.session.add(DistanceMatrix(
                        origin_id=origin, destination_id=destination, kilos=0, seconds=0))
                    db.session.commit()
                    logger.info(
                        f'Added {origin} to {destination} to the database')
                    kilos_matrix.loc[origin, destination] = 0
                    seconds_matrix.loc[origin, destination] = 0
        db.session.commit()

        new_points_2 = get_distance_matrix(
            new_addresses, old_addresses, use_placeid=use_placeid)
        for origin in new_points_2.keys():
            for destination in new_points_2[origin].keys():
                if origin != destination:
                    try:
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=new_points_2[origin][destination]['kilos'], seconds=new_points_2[origin][destination]['seconds']))
                        kilos_matrix.loc[origin,
                                         destination] = new_points_2[origin][destination]['kilos']
                        seconds_matrix.loc[origin,
                                           destination] = new_points_2[origin][destination]['seconds']
                    except:
                        logger.warning(
                            'An address was not found. Skipping for now.')
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=PLACEHOLDER_HIGH_VALUE, seconds=PLACEHOLDER_HIGH_VALUE))
                        kilos_matrix.loc[origin,
                                         destination] = PLACEHOLDER_HIGH_VALUE
                        seconds_matrix.loc[origin,
                                           destination] = PLACEHOLDER_HIGH_VALUE
                else:
                    db.session.add(DistanceMatrix(
                        origin_id=origin, destination_id=destination, kilos=0, seconds=0))
                    kilos_matrix.loc[origin, destination] = 0
                    seconds_matrix.loc[origin, destination] = 0

        db.session.commit()

        new_points_3 = get_distance_matrix(
            old_addresses, new_addresses, use_placeid=use_placeid)
        for origin in new_points_3.keys():
            for destination in new_points_3[origin].keys():
                if origin != destination:
                    try:
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=new_points_3[origin][destination]['kilos'], seconds=new_points_3[origin][destination]['seconds']))
                        kilos_matrix.loc[origin,
                                         destination] = new_points_3[origin][destination]['kilos']
                        seconds_matrix.loc[origin,
                                           destination] = new_points_3[origin][destination]['seconds']
                    except:
                        logger.warning(
                            'An address was not found. Skipping for now.')
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=PLACEHOLDER_HIGH_VALUE, seconds=PLACEHOLDER_HIGH_VALUE))
                        kilos_matrix.loc[origin,
                                         destination] = PLACEHOLDER_HIGH_VALUE
                        seconds_matrix.loc[origin,
                                           destination] = PLACEHOLDER_HIGH_VALUE

                else:
                    db.session.add(DistanceMatrix(
                        origin_id=origin, destination_id=destination, kilos=0, seconds=0))
                    kilos_matrix.loc[origin, destination] = 0
                    seconds_matrix.loc[origin, destination] = 0

        db.session.commit()
        logger.info('new distances added to database')

    else:
        logger.info('all needed distances are already in the database')

    # committing the new values to the database and adding to the matrices

    if not kilos_matrix.isnull().values.any():
        logger.info('All values in the miles matrix are not null')
    else:
        origins_needed = [
            address for address in kilos_matrix.index if kilos_matrix.loc[address].isnull().any()]
        destinations_needed = [
            address for address in kilos_matrix.columns if kilos_matrix.loc[:, address].isnull().any()]
        logger.info(
            'There are null values in the miles matrix, filling them in')
        logger.info(f'Origins needed: {origins_needed}')
        logger.info(f'Destinations needed: {destinations_needed}')
        final_points = get_distance_matrix(
            origins_needed, destinations_needed, use_placeid=use_placeid)
        for origin in final_points.keys():
            for destination in final_points[origin].keys():
                if origin != destination:
                    try:
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=final_points[origin][destination]['kilos'], seconds=final_points[origin][destination]['seconds']))
                        kilos_matrix.loc[origin,
                                         destination] = final_points[origin][destination]['kilos']
                        seconds_matrix.loc[origin,
                                           destination] = final_points[origin][destination]['seconds']
                        logger.info(
                            f'Added {origin} to {destination} to the database')
                    except:
                        db.session.add(DistanceMatrix(origin_id=origin, destination_id=destination,
                                       kilos=PLACEHOLDER_HIGH_VALUE, seconds=PLACEHOLDER_HIGH_VALUE))
                        kilos_matrix.loc[origin,
                                         destination] = PLACEHOLDER_HIGH_VALUE
                        seconds_matrix.loc[origin,
                                           destination] = PLACEHOLDER_HIGH_VALUE
                        logger.warning(
                            'An address was not found. Imputing a high value')

                else:
                    db.session.add(DistanceMatrix(
                        origin_id=origin, destination_id=destination, kilos=0, seconds=0))
                    kilos_matrix.loc[origin, destination] = 0
                    seconds_matrix.loc[origin, destination] = 0
        db.session.commit()
        logger.info('new distances added to database')
    return kilos_matrix, seconds_matrix


def load_people(strio: StringIO):
    """
    Loads the people from the request form. If they are not in the database, they are not included.
    """
    signups_df = pd.read_csv(strio, sep=',')

    logger.debug('signups_df: {}'.format(signups_df))
    logger.debug('signups_df.columns: {}'.format(signups_df.columns))
    users = Passenger.query.filter(and_(Passenger.first_name.in_(signups_df['first name']),
                                        Passenger.last_name.in_(signups_df['last name']))).all()
    people_list = []
    for user in users:
        try:
            signups_df.loc[signups_df.apply(lambda s: (s['first name'] == user.first_name) & (
                s['last name'] == user.last_name), axis=1)].iloc[0]
        except IndexError:
            logger.warning('User {} {} not found in the signups'.format(
                user.first_name, user.last_name))
            continue
        logger.debug('user: {}'.format(user))
        new_person = Person(user.index, user.address[0].id,
                            (signups_df.loc[signups_df.apply(lambda s: (s['first name'] == user.first_name) & (
                                s['last name'] == user.last_name), axis=1)].iloc[0]['willing to drive'] == 'yes'),
                            user.user.driver_profile.num_seats if user.user.driver_profile else 0,
                            (signups_df.loc[signups_df.apply(lambda s: (s['first name'] == user.first_name) & (
                                s['last name'] == user.last_name), axis=1)].iloc[0]['needs ride'] == 'yes'),
                            MAX_TIME  # NEEDS CHANGED TODO
                            )
        logger.info('new person: {}'.format(new_person))
        people_list.append(new_person)
    return people_list
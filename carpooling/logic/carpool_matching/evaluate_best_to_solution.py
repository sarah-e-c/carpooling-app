
from .data_classes import Person, LocalPassenger, DRIVER_WAITING_TIME, Solution, MAX_ITER, LocalCarpool, LocalDriver
from .general_functions import fill_distance_matrix
from carpooling.models import Destination, Passenger
import numpy as np
import pandas as pd
from numpy.random import choice

import logging

logger = logging.getLogger(__name__)


TIME_TOLERANCE_CONSTANT = 1.5

def evaluate_best_solution_to(rsvp_list: list[Person], destination_id: int, return_='all_solutions', use_placeid=True) -> Solution:
    """
    Evaluating the best solution for a one-way event
    :param rsvp_list: the list of people who are going to the event, formatted into the Person class.
    :param destination_id: the id of the destination in the Destinations table.
    :param return_: the type of return value. Can be 'all_solutions' or 'best_solution'.
    :return: The best found solution for the event
    """

    # matrix of distances between each person. Each person is a column and a row.
    solutions_dict = {}
    kilos_matrix, seconds_matrix = fill_distance_matrix(
        rsvp_list, destination_id, use_placeid=use_placeid)
    # updating the perople with their distances

    destination_id = Destination.query.get(destination_id).address.id

    # making passengers and drivers for the matching matrix TODO possible multiprocessing
    passengers = []
    drivers = []
    people_dict = {}
    logger.info('rsvp_list: {}'.format(rsvp_list))
    for person in rsvp_list:
        # calculating their time tolerance
        time_tolerance = seconds_matrix.loc[person.location_id, destination_id] * TIME_TOLERANCE_CONSTANT
        person.time_tolerance = time_tolerance
        people_dict[person.id_] = {'Person': person,
                                   'Driver': None, 'Passenger': None}
        if person.is_driver:
            drivers.append(LocalDriver(id_=person.id_, location_id=person.location_id,
                           num_seats=person.num_seats, is_real_driver=True, time_tolerance=person.time_tolerance))
            people_dict[person.id_]['Driver'] = drivers[-1]
        if person.is_passenger:
            passengers.append(LocalPassenger(id_=person.id_, location_id=person.location_id,
                              can_drive=person.is_driver, num_seats=person.num_seats, time_tolerance=person.time_tolerance))
            people_dict[person.id_]['Passenger'] = passengers[-1]

    # marking the compatibility of the distance matrix

    def initialize_driver_compatibility(frame: pd.DataFrame, driver: LocalDriver):
        """
        Initialize the compatibility of a driver.
        :param frame: the carpool matching frame
        :param driver: the driver to initialize

        Note: driver must be in the frame
        """
        for passenger in frame.columns:
            if driver.id_ == passenger.id_:
                frame.loc[driver, passenger] = False
            # determining if picking up the passenger is within the time tolerance
            if seconds_matrix.loc[driver.location_id, passenger.location_id] + seconds_matrix.loc[passenger.location_id, destination_id] + DRIVER_WAITING_TIME <= driver.time_tolerance:
                # represents the extra time it would take for the driver to pick up the passenger
                frame.loc[driver, passenger] = seconds_matrix.loc[driver.location_id, passenger.location_id] + \
                    seconds_matrix.loc[passenger.location_id, destination_id] + \
                    DRIVER_WAITING_TIME - \
                    seconds_matrix.loc[driver.location_id, destination_id]
            else:
                frame.loc[driver, passenger] = False

    def calculate_selection_probability(frame: pd.DataFrame, driver: LocalDriver, passenger: LocalPassenger, max_value_in_frame: float) -> float:
        """
        Calculate the selection probability of a driver and passenger.
        :param frame: the carpool matching frame
        :param driver: the driver
        :param passenger: the passenger
        """
        if max_value_in_frame == 0:  # avoid div by 0
            return 0

        if np.isnan(frame.loc[driver, passenger]):
            return 0

        return 1 - (frame.loc[driver, passenger] / max_value_in_frame)

    static_carpool_matching_frame = pd.DataFrame(
        columns=passengers,
        index=drivers
    )
    for driver in static_carpool_matching_frame.index:
        initialize_driver_compatibility(static_carpool_matching_frame, driver)

    # now heres the fun part
    for i in range(1, MAX_ITER):
        # initializing the matching matrix
        carpool_matching_frame = static_carpool_matching_frame.copy()

        kilos_matrix.to_csv('kilos_matrix.csv')
        seconds_matrix.to_csv('seconds_matrix.csv')
        solutions_dict[f'iteration_{i}'] = Solution(kilos_matrix=kilos_matrix, seconds_matrix=seconds_matrix,
                                                    all_passengers=passengers,
                                                    all_drivers=drivers,
                                                    destination_id=destination_id)
        # while there are still viable pairs in the matrix
        logger.info('carpool_matching_frame: {}'.format(
            carpool_matching_frame))

        while carpool_matching_frame.cumsum().sum().sum() > 0:
            logger.info('Creating carpool for iteration {}'.format(i))
            max_value_in_frame = np.nanmax(
                carpool_matching_frame.values.flatten())
            if (max_value_in_frame == 0) or (np.isnan(max_value_in_frame)):
                logger.warning(
                    f'The max value in the frame is {max_value_in_frame}. Breaking out of the loop.')
                break

            driver = choice(carpool_matching_frame.index)
            probabilities = carpool_matching_frame.columns.map(lambda f: calculate_selection_probability(
                carpool_matching_frame, driver, f, max_value_in_frame))
            if np.nansum(probabilities) == 0:
                logger.warning(
                    f'The sum of the probabilities is 0. Breaking out of the loop.')
                continue
            probabilities_sum = np.nansum(probabilities)
            probabilities = list(
                map(lambda f: f / probabilities_sum, probabilities))
            passenger = choice(
                carpool_matching_frame.columns,
                p=probabilities)

            # matching the driver and the passenger and adding them to the solution
            if not driver.is_real_driver:
                solutions_dict[f'iteration_{i}'].get_carpool(
                    driver).add_passenger(passenger)
            else:
                new_carpool = LocalCarpool(
                    driver=driver, location_frame=seconds_matrix)
                new_carpool.add_passenger(passenger)
                solutions_dict[f'iteration_{i}'].add_carpool(new_carpool)

            # deleting the passenger and the driver from the matrix, replacing with a virtual driver if the seats aren't empty
            if driver.num_seats > 0:
                new_virtual_driver = passenger.make_virtual_driver(
                    driver, seconds_matrix.loc[driver.location_id, passenger.location_id])
                carpool_matching_frame.loc[new_virtual_driver,
                                           :] = carpool_matching_frame.loc[driver, :]
                # deleting the passenger from the matrix
                carpool_matching_frame.drop(
                    axis=1, columns=passenger, inplace=True)
                initialize_driver_compatibility(
                    carpool_matching_frame, new_virtual_driver)  # calculating the new row of the matrix that was made
            else:
                carpool_matching_frame.drop(
                    axis=1, columns=passenger, inplace=True)

            carpool_matching_frame.drop(driver, inplace=True)

        # now we have to calculate the fitness of the solution
        solutions_dict[f'iteration_{i}'].calculate_total_utility_value()

    if return_ == 'all_solutions':
        return solutions_dict
    else:
        return solutions_dict[max(solutions_dict, key=lambda f: solutions_dict[f].total_utility_value)]

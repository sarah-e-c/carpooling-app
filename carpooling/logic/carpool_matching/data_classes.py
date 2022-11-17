"""
File for implementing the matching algorithm. Inspired by works of
"""
from dataclasses import dataclass
import pandas as pd
import random
import requests
import time
from carpooling.models import Event, Address, DistanceMatrix,  Destination, Passenger
from carpooling import db
import numpy as np
import logging
from io import StringIO
import json
from numpy.random import choice
from sqlalchemy import and_


logger = logging.getLogger(__name__)


MAX_TIME = 90  # no more than 90 minutes of travel
DRIVER_WAITING_TIME = 5  # assuming 5 minutes of wait time between stops


PLACEHOLDER_HIGH_VALUE = 9999999999999

MAX_COMPUTATION_TIME = 5  # 5 minutes
MAX_ITER = 100  # 1000 iterations

API_KEY = 'AIzaSyD_JtvDeZqiy9sxCKqfggODYMhuaeeLjXI'


# weighting coefficients
# weight for the total distance of the route compared to the default.
ROUTE_DISTANCE_WEIGHT = 0.25
PASSENGERS_SERVED_WEIGHT = 0.25  # weight for percentage of needed passengers served
# weight for people with lots of points having more favorable routes than others
FAVORABLE_ROUTE_WEIGHT = 0.25
ROUTE_TIME_WEIGHT = 0.25  # weight for total time for each passenger

MAX_TIME = 23056
# add support for multiple places?


@dataclass(frozen=True)  # we want this to be hashable
class LocalDriver:
    """
    Class to represent a driver in the matching matrix
    """
    """
        Initialize a driver.
        :param location_id: the position of the driver
        :param is_real_driver: whether or not the driver is a real driver. Is false if the driver.
        :param num_seats: the number of seats in the carpool.
        :param time_tolerance: the time tolerance of the driver. Is calculated by their original route time.
    """
    id_: int
    location_id: int
    is_real_driver: bool
    num_seats: int
    time_tolerance: float
    driver_history: tuple = ()


@dataclass(frozen=True)  # we want this to be hashable
class LocalPassenger:
    """
    Class to represent a passenger in the matrix.
    """
    """
        Initialize a passenger.
        :param id_: the identifier of the passenger. If they are a mixed user, then this is the same as the driver id.
        :param location_id: the index of the location of the passenger
        ;param can_drive: whether or not the passenger can drive. Used in determining if the 
    """
    id_: int
    location_id: int
    can_drive: bool
    num_seats: int
    time_tolerance: float

    def make_virtual_driver(self, old_driver: LocalDriver, time_passage: float) -> LocalDriver:
        """
        Create a driver from a passenger. Used in the case that a passenger is a driver.
        :param old_driver: the driver that the new fake driver is replacing. TODO make the determine to maybe replace a driver
        """
        new_driver_history = []
        for item in old_driver.driver_history:
            new_driver_history.append(item)
        # this is here because im dumb
        new_driver_history.append(old_driver.id_)
        return LocalDriver(id_=self.id_,
                      location_id=self.location_id,
                      num_seats=old_driver.num_seats - 1,
                      is_real_driver=False,
                      time_tolerance=old_driver.time_tolerance - time_passage,

                      driver_history=tuple(new_driver_history))


class LocalCarpool:
    """
    Class for prospective carpool. Carpools are defined by drivers.
    """

    def __init__(self, driver: LocalDriver, location_frame: pd.DataFrame) -> None:
        self.passengers = []
        self.driver = driver
        self.route = [driver.location_id]
        self.total_time = 0
        self.location_frame = location_frame

    def add_passenger(self, passenger: LocalPassenger) -> None:
        """
        Adds a passenger to the carpool.
        """
        self.passengers.append(passenger)
        self.route.append(passenger.location_id)
        self.total_time += self.calculate_time_between_locations(
            self.route[-2], self.route[-1])

    def calculate_time_between_locations(self, location_id_1: int, location_id_2: int) -> float:
        """
        Calculates the time between locations.
        """
        return self.location_frame.loc[location_id_1, location_id_2]


class Solution:
    TOTAL_LENGTH_OBJECTIVE_WEIGHT = 0.5
    PASSENGERS_SERVED_OBJECTIVE_WEIGHT = 0.5

    def __init__(self, kilos_matrix: pd.DataFrame, seconds_matrix: pd.DataFrame, all_drivers, all_passengers, destination_id, type_='to'):
        self.carpools = []
        self.kilos_matrix = kilos_matrix
        self.seconds_matrix = seconds_matrix
        self.all_drivers = all_drivers
        self.all_passengers = all_passengers
        self.destination_id = destination_id
        self.length_objective_value = 0
        self.needed_passengers_served_objective_value = 0
        self.favorable_time_objective_value = 0
        self.favorable_route_objective_value = 0
        self.total_utility_value = 0
        self.type = type_


    def add_carpool(self, carpool: LocalCarpool):
        """
        Adds a carpool to the solution.
        """
        self.carpools.append(carpool)

    def get_carpool(self, driver: LocalDriver) -> LocalCarpool:
        """
        Gets the carpool of the solution that the driver is leading
        :param driver: the driver to get the carpool of. Can be true or virtual.
        """
        if driver.is_real_driver:
            return [carpool for carpool in self.carpools if carpool.driver == driver][0]
        else:
            return [carpool for carpool in self.carpools if carpool.driver.id_ == driver.driver_history[0]][0]

    # utility functions
    def calculate_length_objective_value(self):
        """
        Calculating the utility function for the total length traveled compared to the default.
        """
        if self.type == 'to':
            temp_value = 0
            for carpool in self.carpools:
                total_distance_before_carpool = 0
                total_distance_after_carpool = 0

                for passenger in carpool.passengers:
                    total_distance_before_carpool += self.kilos_matrix.loc[passenger.location_id][self.destination_id]
                total_distance_before_carpool += self.kilos_matrix.loc[carpool.driver.location_id][self.destination_id]
                for i in range(len(carpool.route) - 1):
                    total_distance_after_carpool += self.kilos_matrix.loc[carpool.route[i]][carpool.route[i + 1]]

                temp_value += (carpool.driver.num_seats/(carpool.driver.num_seats - 1)) * (1- total_distance_after_carpool/total_distance_before_carpool)
            self.length_objective_value = temp_value/len(self.carpools) 
            logger.info(f'Solution {self} has a length objective value of {self.length_objective_value}')
            return self.length_objective_value  


    def calculate_needed_passengers_served_value(self):
        """
        Calculating the value for passengers needing a carpool being served. (percentage)
        """
        served_passengers = []
        # all passengers that cannot drive
        for carpool in self.carpools:
            for passenger in carpool.passengers:
                served_passengers.append(passenger)
        
        needed_passengers = [passenger for passenger in self.all_passengers if not passenger.can_drive]
        served_passengers = [passenger for passenger in served_passengers if not passenger.can_drive]

        self.needed_passengers_served_objective_value = len(served_passengers) / len(needed_passengers) # ratio
        logger.info(f'Solution {self} has a needed passengers served objective value of {self.needed_passengers_served_objective_value}')
        return self.needed_passengers_served_objective_value


    def calculate_favorable_time_value(self):
        """
        Calculating the utility value for each route not being too long compared to each driver's original route.
        """

        return 1

    def calculate_favorable_route_value(self):
        """
        Calculating the utility function for the people who have been carpooling longer having a favorable time.
        """

        
        return 1

    def calculate_total_utility_value(self):
        """
        Weighted sums all of the utility functions.
        """
        for carpool in self.carpools:
            carpool.route.append(self.destination_id) # doing this because its too much work to do it there

        
        total_length_utility = self.calculate_length_objective_value()
        needed_passengers_served_utility = self.calculate_needed_passengers_served_value()
        self.total_utility_value = self.TOTAL_LENGTH_OBJECTIVE_WEIGHT * total_length_utility +\
             self.PASSENGERS_SERVED_OBJECTIVE_WEIGHT * needed_passengers_served_utility
        
        logger.info(f'Solution {self} has a total utility value of {self.total_utility_value}')




@dataclass()
class Person:
    """
        Initialize a passenger.
        :param id_: the identifier of the passenger. If they are a mixed user, then this is the same as the driver id.
        :param location_id: the index of the location of the passenger
        ;param is_driver : whether or not the passenger can drive. Used in determining the matching matrix.
        :param num_seats: the number of seats the passenger has available. Used in determining the matching matrix.
        :param is_passenger: whether or not the person is a passenger.
    """
    id_: int
    location_id: int
    is_driver: bool
    num_seats: int
    is_passenger: bool
    time_tolerance: float
"""
File for implementing the matching algorithm. Inspired by works of
"""
from dataclasses import dataclass
import pandas as pd
import random
import requests
import time
MAX_TIME = 90  # no more than 90 minutes of travel
DRIVER_WAITING_TIME = 5  # assuming 5 minutes of wait time between stops

MAX_COMPUTATION_TIME = 60 * 5  # 5 minutes
MAX_ITER = 1000  # 1000 iterations


# weighting coefficients
ROUTE_DISTANCE_WEIGHT = 0.25 # weight for the total distance of the route compared to the default. 
PASSENGERS_SERVED_WEIGHT = 0.25 # weight for percentage of needed passengers served
FAVORABLE_ROUTE_WEIGHT = 0.25 # weight for people with lots of points having more favorable routes than others
ROUTE_TIME_WEIGHT = 0.25  # weight for total time for each passenger


# add support for multiple places?

@dataclass(frozen=True)  # we want this to be hashable
class Driver:
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


@dataclass(frozen=True)  # we want this to be hashable
class Passenger:
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
    driver_history: list = []

    def create_virtual_driver(self, old_driver: Driver, time_passage: float) -> Driver:
        """
        Create a driver from a passenger. Used in the case that a passenger is a driver.
        :param old_driver: the driver that the new fake driver is replacing. TODO make the determine to maybe replace a driver
        """
        return Driver(id_=self.id_,
                      location_id=self.location_id,
                      num_seats=old_driver.num_seats - 1,
                      is_real_driver=False,
                      time_tolerance=old_driver.time_tolerance - time_passage,
                      driver_history=self.driver_history + [old_driver.id_])
class Carpool:
    """
    Class for prospective carpool. Carpools are defined by drivers.
    """

    def __init__(self, driver: Driver, location_frame: pd.DataFrame) -> None:
        self.passengers = []
        self.driver = driver
        self.route = [driver.location_id]
        self.total_time = 0
        self.location_frame = location_frame

    def add_passenger(self, passenger: Passenger) -> None:
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
    def __init__(self):
        self.carpools = []
        self.length_objective_value = 0
        self.needed_passengers_served_objective_value = 0
        self.favorable_time_objective_value = 0
        self.favorable_route_objective_value = 0
        self.total_utility_value = 0

    def add_carpool(self, carpool: Carpool):
        """
        Adds a carpool to the solution.
        """
        self.carpools.append(carpool)

    def get_carpool(self, driver: Driver) -> Carpool:
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
        Calculating the utility function for the total length traveled.
        """
        return 1
        pass

    def calculate_needed_passengers_served_value(self):
        """
        Calculating the value for passengers needing a carpool being served. (percentage)
        """
        return 1

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
        return 1


def fill_distance_matrix():
    """
    Method that uses Google Maps API to get the distances between all points.
    """
    # TODO only get the values that are reasonably close to each other already.
    # We don't need a northside distance to a southside distance.
    # If its in the algorithm, then just input a high value
    
    # for now just getting all of them because it is easier.
    # query addresses

    pass

def load_people(first_names, last_names):
    """
    Loads the people from the request form.
    """
    # TODO load in the csv file
    pass


@dataclass(frozen=True)
class Person:
    """
        Initialize a passenger.
        :param id_: the identifier of the passenger. If they are a mixed user, then this is the same as the driver id.
        :param location_id: the index of the location of the passenger
        ;param can_drive: whether or not the passenger can drive. Used in determining the matching matrix.
        :param is_passenger: whether or not the person is a passenger.
    """
    id_: int
    location_id: int
    is_driver: bool
    num_seats: int
    is_passenger: bool
    time_tolerance: float


def evaluate_best_solution(rsvp_list: list[Person], destination_id: int, return_ = 'all_solutions') -> Solution:
    """
    Evaluating the best solution for a one-way event
    :param rsvp_list: the list of people who are going to the event, formatted into the Person class.
    :param destination_id: the index of the destination of the event in the location matrix.
    :param return_: the type of return value. Can be 'all_solutions' or 'best_solution'.
    :return: The best found solution for the event
    """

    # matrix of distances between each person. Each person is a column and a row.
    solutions_dict = {}
    # TODO store these matrices in SQL
    locations = ['Maggie Walker', 'Home One']
    distance_matrix = pd.DataFrame(columns=locations, index=locations)
    if True:  # if the data is unloaded, then fill the distance matrix with Google Maps
        fill_distance_matrix()

    # making passengers and drivers for the matching matrix
    passengers = []
    drivers = []
    people_dict = {}
    for person in rsvp_list:
        people_dict[person.id_] = {'Person': person, 'Driver': None, 'Passenger': None}
        if person.is_driver:
            drivers.append(Driver(id_=person.id_, location_id=person.location_id,
                           num_seats=person.num_seats, is_real_driver=True, time_tolerance=person.time_tolerance))
            people_dict[person.id_]['Driver'] = drivers[-1]
        if person.is_passenger:
            passengers.append(Passenger(id_=person.id_, location_id=person.location_id,
                              can_drive=person.is_driver, num_seats=person.num_seats, time_tolerance=person.time_tolerance))
            people_dict[person.id_]['Passenger'] = passengers[-1]

    # initializing the matching matrix
    carpool_matching_frame = pd.DataFrame(
        columns=passengers,
        index=drivers
    )
    # marking the compatibility of the distance matrix

    def initialize_driver_compatibility(frame: pd.DataFrame, driver: Driver):
        """
        Initialize the compatibility of a driver.
        :param frame: the carpool matching frame
        :param driver: the driver to initialize

        Note: driver must be in the frame
        """
        for passenger in frame.loc[driver, :]:
            # determining if picking up the passenger is within the time tolerance
            if distance_matrix.loc[driver.location_id, passenger.location_id] + distance_matrix.loc[passenger.location_id, destination_id] + DRIVER_WAITING_TIME <= driver.time_tolerance:
                # represents the extra time it would take for the driver to pick up the passenger
                frame.loc[driver, passenger] = distance_matrix.loc[driver.location_id, passenger.location_id] + \
                    distance_matrix.loc[passenger.location_id, destination_id] + \
                    DRIVER_WAITING_TIME - \
                    distance_matrix.loc[driver.location_id, destination_id]
            else:
                frame.loc[driver, passenger] = False

    # marking the compatibility of the distance matrix
    for driver in carpool_matching_frame.index:
        initialize_driver_compatibility(carpool_matching_frame, driver)

    def calculate_selection_probability(frame: pd.DataFrame, driver: Driver, passenger: Passenger, max_value_in_frame: float) -> float:
        """
        Calculate the selection probability of a driver and passenger.
        :param frame: the carpool matching frame
        :param driver: the driver
        :param passenger: the passenger
        """
        return 1 - (frame.loc[driver, passenger] / max_value_in_frame)

    # now heres the fun part
    start_time = time.time()
    while time.time() - start_time < MAX_COMPUTATION_TIME:
        # yes this is a lot of for loops but this is how the paper does it
        for i in range(1, MAX_ITER):
            solutions_dict[f'iteration_{i}'] = Solution()
            # while there are still viable pairs in the matrix
            
            while carpool_matching_frame.cumsum().sum().sum() > 0:
                for driver in carpool_matching_frame.index:
                    passenger = random.choice(
                        carpool_matching_frame.loc[driver, :],
                        weights=carpool_matching_frame.loc[driver, :].map(lambda f: calculate_selection_probability(carpool_matching_frame, driver, f.passenger, max(carpool_matching_frame))))

                    # matching the driver and the passenger and adding them to the solution
                    if not driver.is_real_driver:
                        solutions_dict[f'iteration_{i}'].get_carpool(
                            driver).add_passenger(passenger)
                    else:
                        new_carpool = Carpool(driver=driver)
                        new_carpool.add_passenger(passenger)
                        solutions_dict[f'iteration_{i}'].add_carpool(new_carpool)
                     
                    # deleting the passenger and the driver from the matrix, replacing with a virtual driver if the seats aren't empty
                    if driver.num_seats > 0:
                        new_virtual_driver = passenger.make_virtual_driver()
                        carpool_matching_frame.loc[new_virtual_driver, :] = carpool_matching_frame.loc[driver, :]
                        # deleting the passenger from the matrix
                        carpool_matching_frame.drop(axis=1, columns=passenger, inplace=True)
                        initialize_driver_compatibility(
                            carpool_matching_frame, new_virtual_driver) # calculating the new row of the matrix that was made
                    else:
                        carpool_matching_frame.drop(axis=1, columns=passenger, inplace=True)

                    carpool_matching_frame.drop(driver, inplace=True)
            

            # now we have to calculate the fitness of the solution
            solutions_dict[f'iteration_{i}'].calculate_total_utility_value()

    if return_ == 'all_solutions':
        return solutions_dict
    else:
        return max(solutions_dict, key=lambda f: solutions_dict[f].total_utility_value)
    
if __name__ == '__main__':
    evaluate_best_solution(rsvp_list=[Person(id_=1, location_id=0, is_driver=True, is_passenger=True, num_seats=1, time_tolerance=1), Person(
        id_=2, location_id=0, is_driver=True, is_passenger=True, num_seats=1, time_tolerance=1)])

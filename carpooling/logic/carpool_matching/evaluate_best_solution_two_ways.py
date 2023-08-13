# TODO

from .data_classes import Person, LocalPassenger, DRIVER_WAITING_TIME, Solution, MAX_ITER, LocalCarpool, LocalDriver
from carpooling.logic.carpool_matching import evaluate_best_solution_one_way

"""
In theory, this will have different results than just doing one way version twice,
(according to the paper) but it's not essential right now
"""
def evaluate_best_solution_two_ways(rsvp_list: list[Person], destination_id: int, return_='all_solutions',
                                   use_placeid=True):
    solution   = evaluate_best_solution_one_way(rsvp_list, destination_id, 'to', return_, use_placeid)
    back_solution = solution.copy()
    for carpool in back_solution.carpools:
        carpool.route = carpool.route[::-1]
        carpool.route_times = carpool.route_times[::-1]
    for carpool in back_solution.carpools:
        for passenger in carpool.passengers:
            ideal_passenger_time = back_solution.seconds_matrix[passenger.location_id][back_solution.destination_id]/60
            passenger_total_time = sum(carpool.route_times[:carpool.route.index(passenger.location_id)])/60
            back_solution.pool_points_dict[passenger.id_] += (passenger_total_time - ideal_passenger_time) * 5
    
    return solution, back_solution

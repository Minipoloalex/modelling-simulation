from mesa import Agent
from enum import Enum
import math

from graph_utils import get_total_distance, get_closest_node


class WorkerType(Enum):
    ENVIROMENTALLY_CONSCIOUS = 1
    COST_SENSITIVE = 2
    CONSERVATIVE = 3


class WorkerAgent(Agent):
    transport_speed_kmh = {"bike": 10, "car": 60, "walk": 3, "electric_scooter": 15}
    transport_graph = {
        "bike": "bike",
        "walk": "walk",
        "car": "drive",
        "electric_scooter": "bike",
    }
    walk_speed_kmh = transport_speed_kmh["walk"]
    def __init__(
        self,
        model,
        worker_type,
        preferred_transport,
        company,
        home_position: tuple[int, int],
    ):
        super().__init__(model=model)
        self.worker_type = worker_type
        self.preferred_transport = preferred_transport
        self.company = company
        self.sustainable_choice = False

        # tuples so we can know the kms and how many times he used each transport
        self.kms_car = (0, 0)
        self.kms_bycicle = (0, 0)
        self.kms_walk = (0, 0)
        self.kms_electric_scooter = (0, 0)
        self.activities_during_day = []
        self.home_position = home_position

        self.home_nodes = {
            type: get_closest_node(graph, self.home_position)[0]
            for type, graph in self.model.graphs.items()
        }
        self.distances_to_work = {
            type: get_total_distance(
                graph, self.home_position, company.location_position
            )
            for type, graph in self.model.graphs.items()
        }
        self.distances_to_home = {
            type: get_total_distance(
                graph, company.location_position, self.home_position
            )
            for type, graph in self.model.graphs.items()
        }
        self.time_to_work = self.__get_time_from_distances(self.distances_to_work)
        self.time_to_home = self.__get_time_from_distances(self.distances_to_home)

        print("Distances to work, home. Time to work, home")
        print(self.distances_to_work)
        print(self.distances_to_home)
        print(self.time_to_work)
        print(self.time_to_home)

    def __get_time_from_distances(self, distances: dict[str, tuple[float]]):
        result = {}
        for transport, speed in self.transport_speed_kmh.items():
            graph_type = self.transport_graph[transport]

            # First you neeed to get from the source to the first node, then you can travel through the graph
            # Finally, you need to get to the destination
            path_distance, additional_distance = distances[graph_type]

            additional_time = additional_distance / self.walk_speed_kmh
            path_time = path_distance / speed
            result[transport] = path_time + additional_time
        return result

    def step(self):
        company_policy = self.company.policy
        # Get agents close to the agent (or from the same company)
        if company_policy == 0:
            # different thresholds for each worker type
            # too many cars (traffic): may choose bicycle?
            # TODO: add randomness
            many_cars = None

        # self.sustainable_choice: Depend on company policy and worker type (and other factors)

from mesa import Agent
from enum import Enum
import random
import math
from mesa.space import NetworkGrid
import networkx as nx
from graph_utils import get_path_information, get_closest_node
# self.time_to_work = self.__get_time_from_distances(self.distances_to_work)
# self.time_to_home = self.__get_time_from_distances(self.distances_to_home)

# print("Distances to work, home. Time to work, home")
# print(self.distances_to_work)
# print(self.distances_to_home)
# print(self.time_to_work)
# print(self.time_to_home)

# def __get_time_from_distances(self, distances: dict[str, tuple[float]]):
#     result = {}
#     for transport, speed in self.transport_speed_kmh.items():
#         graph_type = self.transport_graph[transport]

#         # First you neeed to get from the source to the first node, then you can travel through the graph
#         # Finally, you need to get to the destination
#         path_distance, additional_distance = distances[graph_type]

#         additional_time = additional_distance / self.walk_speed_kmh
#         path_time = path_distance / speed
#         result[transport] = path_time + additional_time
#     return result

# self.home_nodes = {
#     type: get_closest_node(graph, self.home_position)[0]
#     for type, graph in self.model.graphs.items()
# }
# self.visualization_home_node = self.home_nodes[self.model.visualization_graph_type]
# self.visualization_company_node = self.company.visualization_node
# self.model.grid.place_agent(self, self.visualization_home_node)

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
       
        information_to_work = {
            type: get_path_information(
                graph, self.home_position, company.location_position
            )
            for type, graph in self.model.graphs.items()
        }
        information_to_home = {
            type: get_path_information(
                graph, company.location_position, self.home_position
            )
            for type, graph in self.model.graphs.items()
        }
        distances_to_choose_transport = {
            type: (
                (information_to_home[type].transport_distance + information_to_work[type].transport_distance) / 2,
                (information_to_home[type].additional_distance + information_to_work[type].additional_distance) / 2,
            )
            for type in self.model.graphs.keys()
        }
        self.transport_chosen: str = self.choose_transport(distances_to_choose_transport)
        self.chosen_graph_name: str = self.transport_graph[self.transport_chosen]
        self.graph: nx.MultiDiGraph = self.model.graphs[self.chosen_graph_name]

        chosen_information_to_work = information_to_work[self.chosen_graph_name]
        chosen_information_to_home = information_to_home[self.chosen_graph_name]
        self.distances = {
            "to_work": (chosen_information_to_work.transport_distance, chosen_information_to_work.additional_distance),
            "to_home": (chosen_information_to_home.transport_distance, chosen_information_to_home.additional_distance),
        }
        self.paths = {
            "to_work": information_to_work[self.chosen_graph_name].path,
            "to_home": information_to_home[self.chosen_graph_name].path,
        }
        self.current_path_name = "to_work"
        self.current_path: list[int] = self.paths[self.current_path_name]

        self.model.grid.place_agent(self, self.current_path[0])

        self.node_index = 0
        self.partial_finish = False

    def switch_path(self) -> None:
        self.partial_finish = False
        self.current_path_name = "to_home" if self.current_path_name == "to_work" else "to_work"
        self.current_path = self.paths[self.current_path_name]
        self.node_index = 0

    def choose_transport(self, distances):
        transport_distance_car, additional_walk_distance_car = distances["drive"]
        transport_distance_walk, additional_walk_distance_walk = distances["walk"]
        transport_distance_eScooter, additional_walk_distance_eScooter = distances["bike"]
        transport_distance_bike, additional_walk_distance_bike = distances["bike"]

        # Dynamic adjustment functions based on distance
        def walking_probability(distance):
            # Walking becomes less likely as distance grows, near zero at >10 km
            return max(0, math.exp(-distance / 2))

        def bicycle_probability(distance):
            # Bicycling is more viable for mid distances, tapers off at longer distances
            return max(0, math.exp(-(distance - 5) ** 2 / 15))

        def electric_scooter_probability(distance):
            # Scooters are most viable for shorter distances, tapering off after ~8 km
            return max(0, math.exp(-(distance - 4) ** 2 / 8))

        def car_probability(distance):
            # Car becomes more likely as distance increases
            return min(1, distance / 10)

        dynamic_weights = {
            "car": car_probability(transport_distance_car + additional_walk_distance_car),
            "bike": bicycle_probability(transport_distance_bike + additional_walk_distance_bike),
            "electric_scooter": electric_scooter_probability(transport_distance_eScooter + additional_walk_distance_eScooter),
            "walk": walking_probability(transport_distance_walk + additional_walk_distance_walk)
        }

        # Normalize weights to form a proper probability distribution
        total_weight = sum(dynamic_weights.values())
        if total_weight > 0:
            normalized_weights = {key: value / total_weight for key, value in dynamic_weights.items()}
        else:
            normalized_weights = {key: 0 for key in dynamic_weights}

        transport_chosen = random.choices(
            list(normalized_weights.keys()),
            weights=list(normalized_weights.values()),
            k=1,
        )[0]

        return transport_chosen

    def finish_partial_path(self):
        # Includes the contribution of the walk distances from moving from location (latitude, longitude)
        # to the start node, as well as the end node.
        additional_walk_distance = self.distances[self.current_path_name][1]
        self.kms_walk = (self.kms_walk[0], self.kms_walk[1] + additional_walk_distance)

    def calculate_distance(self, start_node, end_node):
        edges = self.graph[start_node][end_node]
        return min(edge["length"] for edge in edges.values())

    def step(self):
        if self.partial_finish:
            # Do nothing while we wait for other agents to get to the desired locations
            # This flag is unset in self.switch_path()
            return

        company_policy = self.company.policy

        if self.node_index == len(self.current_path) - 1:
            # On the last node, just finished path
            self.finish_partial_path()
            self.partial_finish = True
            return

        self.node_index += 1
        previous_node = self.current_path[self.node_index - 1]
        current_node = self.current_path[self.node_index]
        distance_travelled = self.calculate_distance(previous_node, current_node)

        if self.transport_chosen == "walk":
            self.kms_walk = (self.kms_walk[0] + 1, self.kms_walk[1] + distance_travelled)
        elif self.transport_chosen == "bike":
            self.kms_bycicle = (self.kms_bycicle[0] + 1, self.kms_bycicle[1] + distance_travelled)
        elif self.transport_chosen == "electric_scooter":
            self.kms_electric_scooter = (self.kms_electric_scooter[0] + 1, self.kms_electric_scooter[1] + distance_travelled)
        elif self.transport_chosen == "car":
            self.kms_car = (self.kms_car[0] + 1, self.kms_car[1] + distance_travelled)
        else:
            raise ValueError(f"Invalid transport chosen '{self.transport_chosen}'")

        self.model.grid.move_agent(self, current_node)

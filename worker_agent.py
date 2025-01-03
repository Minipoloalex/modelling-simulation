from mesa import Agent
from enum import Enum
import random
import math
from mesa.space import NetworkGrid
import networkx as nx
from graph_utils import get_path_information, get_closest_node
from company_agent import CompanyAgent


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
        company: CompanyAgent,
        home_position: tuple[int, int],
    ):
        super().__init__(model=model)
        self.company = company
        
        self.sustainable_choice = False

        # tuples so we can know the kms and how many times he used each transport
        self.kms_car = (0, 0)
        self.kms_bycicle = (0, 0)
        self.kms_walk = (0, 0)
        self.kms_electric_scooter = (0, 0)
        self.activities_during_day = []
        self.home_position = home_position
        self.sustainability_factor = 0 if self.company.policy == "policy0" else 0.3

        self.information_to_work = {
            type: get_path_information(
                graph, self.home_position, company.location_position
            )
            for type, graph in self.model.graphs.items()
        }
        self.information_to_home = {
            type: get_path_information(
                graph, company.location_position, self.home_position
            )
            for type, graph in self.model.graphs.items()
        }
        self.distances_to_choose_transport = {
            type: (
                (self.information_to_home[type].transport_distance + self.information_to_work[type].transport_distance) / 2,
                (self.information_to_home[type].additional_distance + self.information_to_work[type].additional_distance) / 2,
            )
            for type in self.model.graphs.keys()
        }
        self.transport_chosen: str = self.choose_transport(self.distances_to_choose_transport)
        self.__setup_transport_chosen()

    def modify_sustainable_factor(self, raise_value) -> None:
        self.sustainability_factor *= raise_value

    def __setup_transport_chosen(self) -> None:
        # Allows choosing a different transport at a given step in the simulation

        self.chosen_graph_name: str = self.transport_graph[self.transport_chosen]
        self.graph: nx.MultiDiGraph = self.model.graphs[self.chosen_graph_name]

        chosen_information_to_work = self.information_to_work[self.chosen_graph_name]
        chosen_information_to_home = self.information_to_home[self.chosen_graph_name]
        self.distances = {
            "to_work": (chosen_information_to_work.transport_distance, chosen_information_to_work.additional_distance),
            "to_home": (chosen_information_to_home.transport_distance, chosen_information_to_home.additional_distance),
        }
        self.paths = {
            "to_work": self.information_to_work[self.chosen_graph_name].path,
            "to_home": self.information_to_home[self.chosen_graph_name].path,
        }
        self.current_path_name = "to_work"
        self.current_path: list[int] = self.paths[self.current_path_name]

        if self.pos is None:
            self.model.grid.place_agent(self, self.current_path[0])
        else:
            self.model.grid.move_agent(self, self.current_path[0])

        self.node_index = 0
        self.partial_finish = False

    def switch_path(self) -> None:
        self.partial_finish = False
        if self.current_path_name == "to_work":
            self.current_path_name = "to_home"
        else:
            self.current_path_name = "to_work"
            self.transport_chosen = self.choose_transport(self.distances_to_choose_transport)
            self.__setup_transport_chosen()

        self.current_path = self.paths[self.current_path_name]
        self.node_index = 0

    def choose_transport(self, distances) -> str:
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

        # Sustainability bias
        dynamic_weights["bike"] *= 1 + self.sustainability_factor*2
        dynamic_weights["walk"] *= 1 + self.sustainability_factor*2
        dynamic_weights["electric_scooter"] *= 1 + self.sustainability_factor

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

    def finish_partial_path(self) -> None:
        # Includes the contribution of the walk distances of moving from location (latitude, longitude)
        # to the start node, as well as the end node.
        additional_walk_distance = self.distances[self.current_path_name][1]
        self.kms_walk = (self.kms_walk[0], self.kms_walk[1] + additional_walk_distance)

    def calculate_distance(self, start_node, end_node) -> float:
        edges = self.graph[start_node][end_node]
        return min(edge["length"] for edge in edges.values())

    def step(self):
        if self.partial_finish:
            # Do nothing while we wait for other agents to get to the desired locations
            # This flag is unset in self.switch_path()
            return

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

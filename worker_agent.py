from mesa import Agent
from enum import Enum
import random
import math
from mesa.space import NetworkGrid
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
        
        # Should be modified on step()
        self.at_home = True
        self.transport_to_work = ""

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
        self.visualization_home_node = self.home_nodes[self.model.visualization_graph_type]
        self.visualization_company_node = self.company.visualization_node
        self.model.grid.place_agent(self, self.visualization_home_node)

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

        # print("Distances to work, home. Time to work, home")
        # print(self.distances_to_work)
        # print(self.distances_to_home)
        # print(self.time_to_work)
        # print(self.time_to_home)

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
            "bicycle": bicycle_probability(transport_distance_walk + additional_walk_distance_walk),
            "electric scooters": electric_scooter_probability(transport_distance_eScooter + additional_walk_distance_eScooter),
            "walking": walking_probability(transport_distance_bike + additional_walk_distance_bike)
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
                
    def step(self):
        company_policy = self.company.policy
        distances = self.distances_to_work if self.at_home else self.distances_to_home
        
        if(self.at_home): 
            transport_chosen = self.choose_transport(distances)
            self.at_home = False
        else:
            transport_chosen = self.transport_to_work
            self.at_home = True

        # TODO:
        # Get agents close to the agent (or from the same company)
        # They affect this agent's choices

        graph_type = self.transport_graph[transport_chosen]
        transport_distance, additional_walk_distance = distances[graph_type]

        if company_policy == "policy0":
            # different thresholds for each worker type
            # too many cars (traffic): may choose bicycle?
            # TODO: add randomness
            if transport_chosen == "walk":
                self.kms_walk = (self.kms_walk[0] + 1, self.kms_walk[1] + transport_distance)
            elif transport_chosen == "bike":
                self.kms_bycicle = (self.kms_bycicle[0] + 1, self.kms_bycicle[1] + transport_distance)
            elif transport_chosen == "electric_scooter":
                self.kms_electric_scooter = (self.kms_electric_scooter[0] + 1, self.kms_electric_scooter[1] + transport_distance)
            elif transport_chosen == "car":
                self.kms_car = (self.kms_car[0] + 1, self.kms_car[1] + transport_distance)
            else:
                raise ValueError(f"Invalid transport chosen '{transport_chosen}'")

            self.kms_walk = (self.kms_walk[0], self.kms_walk[1] + additional_walk_distance)
        else:
            raise ValueError(f"Invalid company policy '{company_policy}'")

        self.at_home = not self.at_home

        if self.at_home:
            self.model.grid.move_agent(self, self.visualization_home_node)
        else:
            self.model.grid.move_agent(self, self.visualization_company_node)

        # self.sustainable_choice: Depend on company policy and worker type (and other factors)

from mesa import Agent
from enum import Enum
import random
import math


class WorkerType(Enum):
    ENVIROMENTALLY_CONSCIOUS = 1
    COST_SENSITIVE = 2
    CONSERVATIVE = 3


class WorkerAgent(Agent):
    def __init__(
        self, model, worker_type, preferred_transport, company, home_node: int
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
        self.home_node = home_node

        self.distance_to_work = self.model.get_total_distance(
            self.model.graph,
            self.model.get_shortest_path(
                self.model.graph, source_id=self.home_node, target_id=self.company.pos
            ),
        )
        transport_speed_kmh = {"bike": 10, "car": 60, "walk": 3, "electric_scooter": 15}
        self.time_to_work = {
            transport: self.distance_to_work / speed
            for transport, speed in transport_speed_kmh.items()
        }

        # Define here limits for the choices of person (choices of transports given distance to work)

    def choose_transport(distance_to_work):

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
            "car": car_probability(distance_to_work),
            "bicycle": bicycle_probability(distance_to_work),
            "electric scooters": electric_scooter_probability(distance_to_work),
            "walking": walking_probability(distance_to_work)
        }

        # Normalize weights to form a proper probability distribution
        total_weight = sum(dynamic_weights.values())
        if total_weight > 0:
            normalized_weights = {key: value / total_weight for key, value in dynamic_weights.items()}
        else:
            normalized_weights = {key: 0 for key in dynamic_weights}

        return normalized_weights
            
    def step(self):
        company_policy = self.company.policy
        transport_chosen = self.choose_transport()
        # Get agents close to the agent (or from the same company)
        if company_policy == 0:
            # different thresholds for each worker type
            # too many cars (traffic): may choose bicycle?
            # TODO: add randomness
            if transport_chosen == "car":
                self.kms_car = (self.kms_car[0] + 1, self.kms_car[1] + self.distance_to_work)
            elif transport_chosen == "bicycle":
                self.kms_bycicle = (self.kms_bycicle[0] + 1, self.kms_bycicle[1] + self.distance_to_work)
            elif transport_chosen == "walking":
                self.kms_walk = (self.kms_walk[0] + 1, self.kms_walk[1] + self.distance_to_work)
            elif transport_chosen == "electric scooters":
                self.kms_electric_scooter = (self.kms_electric_scooter[0] + 1, self.kms_electric_scooter[1] + self.distance_to_work)
            many_cars = None

        # self.sustainable_choice: Depend on company policy and worker type (and other factors)

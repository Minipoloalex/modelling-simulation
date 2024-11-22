from mesa import Agent
from enum import Enum
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

    def step(self):
        company_policy = self.company.policy
        # Get agents close to the agent (or from the same company)
        if company_policy == 0:
            # different thresholds for each worker type
            # too many cars (traffic): may choose bicycle?
            # TODO: add randomness
            many_cars = None

        # self.sustainable_choice: Depend on company policy and worker type (and other factors)

from mesa import Agent
from enum import Enum
import random
import math

class WorkerType(Enum):
    ENVIROMENTALLY_CONSCIOUS = 1
    COST_SENSITIVE = 2
    CONSERVATIVE = 3


class WorkerAgent(Agent):
    def __init__(self, unique_id, model, worker_type, preferred_transport, company, home_node: int, sustainable_gain_sum = 0, sustainable_score = 0):
        self.unique_id = unique_id  # Set unique ID
        self.model = model          # Set modelself.worker_type = worker_type
        self.worker_type = worker_type
        self.preferred_transport = preferred_transport
        self.company = company
        self.sustainable_choice = False
        self.kms_car = (0,0) #tuples so we can know the kms and how many times he used each transport
        self.kms_bycicle = (0,0)
        self.kms_walk = (0,0)
        self.kms_electric_scooter = (0,0)
        self.daily_sustainable_score = sustainable_score                      # daily value of good sustainable behavior
        self.total_sustainable_gain_sum = sustainable_gain_sum                # sum of all the rewards given by the company
        self.home_node = home_node
        self.pos = None  # Initialize position attribute

        source = self.model.graph.nodes[self.home_node]
        target = self.company.work_node
        self.distance_to_work = self.model.get_total_distance(
            self.model.get_shortest_path(self.model.graph, source, target)
        )

        # Define here limits for the choices of person (choices of transports given distance to work)

    def step(self):
        company_policy = self.company.policy
        possible_transports = ["car", "bicycle", "electric scooters", "walking"]
        transport_chosen = random.choice(possible_transports)
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

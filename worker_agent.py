from mesa import Agent
from enum import Enum


class WorkerType(Enum):
    ENVIROMENTALLY_CONSCIOUS = 1
    COST_SENSITIVE = 2
    CONSERVATIVE = 3


class WorkerAgent(Agent):
    def __init__(self, unique_id, model, worker_type, preferred_transport, company, home_node: int):
        super().__init__(unique_id, model)
        self.worker_type = worker_type
        self.preferred_transport = preferred_transport
        self.company = company
        self.sustainable_choice = False
        self.kms_car = (0,0) #tuples so we can know the kms and how many times he used each transport
        self.kms_bycicle = (0,0)
        self.kms_walk = (0,0)
        self.kms_electric_scooter = (0,0)
        self.activities_during_day = []
        self.home_node = home_node

        # Define here limits for the choices of person (choices of transports given distance to work)

    def step(self):
        company_policy = self.company.policy

        # Get agents close to the agent (or from the same company)
        if company_policy == 0:
            # if distance to work very small: choose walking
            # if distance to work small: choose bicycle
            # if distance to work large: choose car
            # different thresholds for each worker type
            # too many cars (traffic): may choose bicycle
            # TODO: add randomness
            distance_to_work = None
            many_cars = None
            walk, bike, bike_limit = 1, 5, 10
            if distance_to_work < walk:
                # Choose walk
                pass
            elif distance_to_work < bike or (distance_to_work < bike_limit and many_cars):
                # Choose bike
                pass
            else:
                # Choose car
                pass

        # self.sustainable_choice: Depend on company policy and worker type (and other factors)

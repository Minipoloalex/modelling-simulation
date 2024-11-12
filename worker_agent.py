from mesa import Agent
from enum import Enum

class WorkerType(Enum):
    ENVIROMENTALLY_CONSCIOUS = 1
    COST_SENSITIVE = 2
    CONSERVATIVE = 3

class WorkerAgent(Agent):
    def __init__(self, unique_id, model, worker_type, preferred_transport, company):
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

    def step(self):
        # Check if the worker is influenced by company's policy
        company_policy = self.company.policy
        # self.sustainable_choice: Depend on company policy and worker type (and other factors)

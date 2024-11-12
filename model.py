from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
import osmnx as ox

from worker_agent import WorkerAgent, WorkerType
from company_agent import CompanyAgent

from typing import Optional

class SustainabilityModel(Model):
    def __init__(
        self,
        num_workers: int,
        worker_types_distribution: list,  # e.g.: [0.2, environmentally_conscious], [0.5, cost_sensitive], [0.3, conservative]
        companies: list,  # e.g.: [(3, policy1), (2, policy2), (1, policy3)]
        graph: nx.Graph,
        seed: Optional[int] = None,
    ):
        """
        Initialize the sustainability model with workers and companies.
        """
        super().__init__(seed)
        self.num_companies = sum(company[0] for company in companies)
        self.num_agents = num_workers + self.num_companies

        self.G = graph
        self.grid = NetworkGrid(self.G)  # Mesa's NetworkGrid
        self.schedule = RandomActivation(self)

        self.data_collector = DataCollector(
            model_reporters={
                "SustainableChoices": self.calculate_sustainable_choices,
                "CO2Emissions": self.calculate_CO2_emissions, # think on how we can change these in order to have a good calculation
                "Time Spent in transports per agent": self.calculate_time_spent_in_transports,
                "Number of times each transport was used overall": self.calculate_times_each_transport_was_used,
                "Which transport was used per agent": self.calculate_times_each_transport_was_used_per_agent
            },
            agent_reporters={"SustainableChoice": "sustainable_choice"},
        )

        company_id = 0
        for company_count, company_type in companies:
            for _ in range(company_count):
                company = CompanyAgent(company_id, self, company_type)
                self.schedule.add(company)

                # TODO: find some space to place a company at
                # x, y = None, None
                # self.grid.place_agent(company, (x, y))
                company_id += 1

        transports = ["car", "bicycle", "electric scooters", "walking"] #electric scooters = trotinete elétrica

        company_agents = self.schedule.agents[:self.num_companies]
        probs, types = zip(*worker_types_distribution)

        for i in range(num_workers):
            worker_type = self.random.choices(types, weights=probs, k=1)[0]

            transport = self.random.choice(transports)
            company = self.random.choice(company_agents)
            worker = WorkerAgent(
                i + self.num_companies, self, worker_type, transport, company
            )

            self.schedule.add(worker)

            # TODO: x, y 
            # self.grid.place_agent(worker, (x, y))

    def calculate_sustainable_choices(self):
        sustainable_workers = sum(
            1
            for a in self.schedule.agents
            if isinstance(a, WorkerAgent) and a.sustainable_choice
        )
        return sustainable_workers / self.num_agents

    def calculate_times_each_transport_was_used(self):
        total_times_car = 0
        total_times_bycicle = 0
        total_times_electric_scooter = 0
        total_times_walk = 0
        return 0    
    
    def calculate_times_each_transport_was_used_per_agent(self):
        return 0

    def calculate_time_spent_in_transports(self):
        final_dict = {}
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                time_kms_Car = agent.kms_car[1] / 40 # kms / 40km/h = time in hours
                time_kms_e_scooter = agent.kms_electric_scooter[1] * 15 # kms / 15km/h = time in hours
                time_kms_walk = agent.kms_walk[1] /3.5 # kms / 3.5km/h = time in hours
                time_kms_bycicle = agent.kms_bycicle[1] / 15 # kms / 15km/h = time in hours
                final_dict[agent.unique_id] = {"Time spent driving car": time_kms_Car, "Time spent using an electrical scooter": time_kms_e_scooter, "Time spent walking:": time_kms_walk, "Time spent bycicling":  time_kms_bycicle}
        return final_dict
    
    def calculate_CO2_emissions(self):
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                CO2_kms_Car = agent.kms_car * 250 # value of reference that I found in here: https://nought.tech/blogs/journal/are-e-scooters-good-for-the-environment#blog
                CO2_kms_e_scooter = agent.kms_electric_scooter * 67 # value of reference that I found in here: https://nought.tech/blogs/journal/are-e-scooters-good-for-the-environment#blog
        return CO2_kms_Car + CO2_kms_e_scooter


    def step(self):
        self.data_collector.collect(self)
        self.schedule.step()


def load_graph(center_point, distance=5000):
    G = ox.graph_from_point(center_point=center_point, dist=distance)
    return G


# Running the model
if __name__ == "__main__":
    num_workers = 50

    center = 41.1664384, -8.6016
    graph = load_graph(center, distance=5000)
    workers_type_distribution = (
        [0.2, WorkerType.ENVIROMENTALLY_CONSCIOUS],
        [0.5, WorkerType.COST_SENSITIVE],
        [0.3, WorkerType.CONSERVATIVE],
    )
    companies = [(3, "policy1"), (2, "policy2"), (1, "policy3")]
    model = SustainabilityModel(num_workers, workers_type_distribution, companies, graph)

    for i in range(100):
        model.step()

    # Access the collected data for analysis
    results = model.data_collector.get_model_vars_dataframe()
    print(results)

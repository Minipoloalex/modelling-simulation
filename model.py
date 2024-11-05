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
        company_id = 0
        for company_count, company_type in companies:
            for _ in range(company_count):
                company = CompanyAgent(company_id, self, company_type)
                self.schedule.add(company)

                # TODO: find some space to place a company at
                # x, y = None, None
                # self.grid.place_agent(company, (x, y))
                company_id += 1

        transports = ["car", "bicycle", "public", "walking"]

        company_agents = self.schedule.agents[:self.num_companies]
        for i in range(num_workers):
            worker_type = self.random.choices(worker_types_distribution)    # TODO: Make this work
            print(worker_type)

            transport = self.random.choice(transports)
            company = self.random.choice(company_agents)
            worker = WorkerAgent(
                i + self.num_companies, self, worker_type, transport, company
            )

            self.schedule.add(worker)

            # TODO: x, y 
            # self.grid.place_agent(worker, (x, y))

    def step(self):
        pass
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

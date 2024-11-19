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
        worker_types_distribution: list,
        companies: list,
        graph: nx.Graph,
        center_node: int,
        company_radius: int = 1000,
        agent_home_radius: int = 5000,
        seed: Optional[int] = None,
    ):
        """
        Initialize the sustainability model with workers and companies.

        Args:
            worker_types_distribution: List of tuples with the distribution of worker types.
            
            For example:
            worker_types_distribution = [0.2, environmentally_conscious], [0.5, cost_sensitive], [0.3, conservative]
            companies = [(3, policy1), (2, policy2), (1, policy3)]
            
        """
        super().__init__(seed)
        self.num_companies = sum(company[0] for company in companies)
        self.num_workers = num_workers
        self.num_agents = self.num_workers + self.num_companies

        self.G = graph
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)

        self.data_collector = DataCollector(
            model_reporters={
                "SustainableChoices": self.calculate_sustainable_choices,
                "CO2Emissions": self.calculate_CO2_emissions,
            },
            agent_reporters={"SustainableChoice": "sustainable_choice"},
        )

        possible_company_nodes = self.grid.get_neighborhood(
            node_id=center_node, include_center=True, radius=company_radius
        )
        company_nodes = self.random.sample(possible_company_nodes, self.num_companies)

        company_id = 0
        for company_count, company_type in companies:
            for _ in range(company_count):
                # Get the node to place the company at
                node = company_nodes.pop()

                company = CompanyAgent(company_id, self, company_type)
                self.grid.place_agent(company, node)
                self.schedule.add(company)

                company_id += 1

        transports = ["car", "bicycle", "walking"]

        company_agents = self.schedule.agents[: self.num_companies]
        probs, types = zip(*worker_types_distribution)

        possible_agent_nodes = self.grid.get_neighborhood(
            node_id=center_node, include_center=True, radius=agent_home_radius
        )
        # Do not allow agents to live at company nodes
        possible_agent_nodes = set(possible_agent_nodes) - set(company_nodes)
        agent_nodes = self.random.sample(sorted(possible_agent_nodes), self.num_workers)

        for i in range(num_workers):
            worker_type = self.random.choices(types, weights=probs, k=1)[0] # Get worker type according to distribution
            home_node = agent_nodes.pop()   # Get living location of agent

            transport = self.random.choice(transports)      # Random preferred transport
            company = self.random.choice(company_agents)    # Random company

            worker = WorkerAgent(
                i + self.num_companies, self, worker_type, transport, company, home_node
            )

            self.schedule.add(worker)
            self.grid.place_agent(worker, home_node)

    def calculate_sustainable_choices(self):
        sustainable_workers = sum(
            1
            for a in self.schedule.agents
            if isinstance(a, WorkerAgent) and a.sustainable_choice
        )
        return sustainable_workers / self.num_agents

    def calculate_CO2_emissions(self):
        # Placeholder for CO2 emissions calculation
        return 0

    def step(self):
        self.data_collector.collect(self)
        self.schedule.step()


def load_graph(center_point, distance=5000):
    G = ox.graph_from_point(center_point=center_point, dist=distance)
    return G


def get_closest_node(G, point):
    # Get the node closest to the center point
    closest_node = ox.distance.nearest_nodes(G, X=[point[1]], Y=[point[0]])
    return closest_node[0]


# Running/Testing the model
if __name__ == "__main__":
    num_workers = 50

    center = 41.1664384, -8.6016
    graph = load_graph(center, distance=5000)
    center_node = get_closest_node(graph, center)
    workers_type_distribution = (
        [0.2, WorkerType.ENVIROMENTALLY_CONSCIOUS],
        [0.5, WorkerType.COST_SENSITIVE],
        [0.3, WorkerType.CONSERVATIVE],
    )
    companies = [(3, "policy1"), (2, "policy2"), (1, "policy3")]
    model = SustainabilityModel(
        num_workers,
        workers_type_distribution,
        companies,
        graph,
        center_node,
        company_radius=1000,
        agent_home_radius=5000,
        seed=42
    )

    for i in range(100):
        model.step()

    # Access the collected data for analysis
    results = model.data_collector.get_model_vars_dataframe()
    print(results)

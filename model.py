from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
import osmnx as ox
import osmnx.distance as distance
import osmnx.routing as routing
import osmnx.truncate
import matplotlib.pyplot as plt
from worker_agent import WorkerAgent, WorkerType
from company_agent import CompanyAgent

from graph_utils import load_graphs, random_position_within_radius
from typing import Optional



class SustainabilityModel(Model):
    def __init__(
        self,
        num_workers: int,
        worker_types_distribution: list,
        companies: list,
        graphs: dict[str, nx.Graph],
        center_position: tuple[float, float],
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
        super().__init__(seed=seed)
        self.num_companies = sum(company[0] for company in companies)
        self.num_workers = num_workers
        self.num_agents = self.num_workers + self.num_companies

        self.graphs = graphs
        self.grids = {
            type: NetworkGrid(graph)
            for type, graph in self.graphs.items()
        }
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

        self.company_agents = self.__init_companies(center_position, companies)
        self.worker_agents = self.__init_agents(center_position, worker_types_distribution)


    def __init_companies(self, center_position: tuple[float, float], companies):
        for company_count, company_type in companies:
            for _ in range(company_count):
                position = random_position_within_radius(self.random, center_position, 1000)
                company = CompanyAgent(self, company_type, position)
                for type in self.grids.keys():
                    agent = Agent(self)
                    self.grids[type].place_agent(agent, company.location_nodes[type])   # Different agent to represent the company in each grid
                    # self.grids[type].place_agent(company, company.location_nodes[type])
                self.schedule.add(company)
        return self.schedule.agents[: self.num_companies]

    def __init_agents(self, center_position: tuple[float, float], worker_types_distribution):
        probs, types = zip(*worker_types_distribution)
        transports = ["car", "bicycle", "electric scooters", "walking"] #electric scooters = trotinete elétrica

        for _ in range(self.num_workers):
            worker_type = self.random.choices(types, weights=probs, k=1)[0] # Get worker type according to distribution
            position = random_position_within_radius(self.random, center_position, 5000)
            transport = self.random.choice(transports)      # Random preferred transport
            company = self.random.choice(self.company_agents)    # Random company works in

            worker = WorkerAgent(self, worker_type, transport, company, position)   # Should be place in grids later
            self.schedule.add(worker)

        return self.agents[self.num_companies :]


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



# Running/Testing the model
if __name__ == "__main__":
    num_workers = 50

    center = 41.1664384, -8.6016
    graphs = load_graphs(center, distance=5000)
    # ox.plot_graph(drive)
    # plt.show()

    # center_node = get_closest_node(graph, center)
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
        graphs,
        center_position=center,
        company_radius=1000,
        agent_home_radius=5000,
        seed=42
    )

    for i in range(100):
        model.step()

    # random_nodes = random.sample(sorted(graph.nodes.keys()), 2)
    # print(f"Random nodes: {random_nodes}")
    # shortest_path = model.get_shortest_path(graph, random_nodes[0], random_nodes[1])
    # print(len(shortest_path))
    # total_distance = model.get_total_distance(graph, shortest_path)
    # print(total_distance)

    # Access the collected data for analysis
    results = model.data_collector.get_model_vars_dataframe()
    print(results)

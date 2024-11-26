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

from typing import Optional
import random

import matplotlib.pyplot as plt
import seaborn as sns
ox.settings.log_console = True

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
        super().__init__(seed=seed)
        self.num_companies = sum(company[0] for company in companies)
        self.num_workers = num_workers
        self.num_agents = self.num_workers + self.num_companies

        self.graph = graph
        self.grid = NetworkGrid(self.graph)
        self.schedule = RandomActivation(self)

        self.data_collector = DataCollector(
            model_reporters={
                "SustainableChoices": self.calculate_sustainable_choices,
                "CO2Emissions": self.calculate_CO2_emissions, # think on how we can change these in order to have a good calculation
                "Time Spent in transports per agent": self.calculate_time_spent_in_transports,
                "Number of times each transport was used overall": self.calculate_times_each_transport_was_used,
                "How many times each transport was used per agent": self.calculate_times_each_transport_was_used_per_agent
            },
            agent_reporters={"SustainableChoice": "sustainable_choice"},
        ) # Now we need to plot all these information at the end of the simulation for better visualization

        possible_company_nodes = self.grid.get_neighborhood(
            node_id=center_node, include_center=True, radius=company_radius
        )
        company_nodes = self.random.sample(possible_company_nodes, self.num_companies)

        for company_count, company_type in companies:
            for _ in range(company_count):
                # Get the node to place the company at
                node = company_nodes.pop()

                company = CompanyAgent(self, company_type)
                self.grid.place_agent(company, node)
                self.schedule.add(company)

        transports = ["car", "bicycle", "electric scooters", "walking"] #electric scooters = trotinete elétrica

        company_agents = self.schedule.agents[: self.num_companies]
        probs, types = zip(*worker_types_distribution)

        possible_agent_nodes = self.grid.get_neighborhood(
            node_id=center_node, include_center=True, radius=agent_home_radius
        )
        # Do not allow agents to live at company nodes
        possible_agent_nodes = set(possible_agent_nodes) - set(company_nodes)
        agent_nodes = self.random.sample(sorted(possible_agent_nodes), self.num_workers)

        for _ in range(num_workers):
            worker_type = self.random.choices(types, weights=probs, k=1)[0] # Get worker type according to distribution
            home_node = agent_nodes.pop()   # Get living location of agent

            transport = self.random.choice(transports)      # Random preferred transport
            company = self.random.choice(company_agents)    # Random company

            worker = WorkerAgent(self, worker_type, transport, company, home_node)

            self.schedule.add(worker)
            self.grid.place_agent(worker, home_node)

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
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                total_times_car += agent.kms_car[0]
                total_times_bycicle += agent.kms_bycicle[0]
                total_times_electric_scooter += agent.kms_electric_scooter[0]
                total_times_walk += agent.kms_walk[0]
        final_dict = {"Total times car was used": total_times_car, "Total times bycicle was used": total_times_bycicle, "Total times electric scooter was used": total_times_electric_scooter, "Total times walk was used": total_times_walk}
        return final_dict    
    
    def calculate_times_each_transport_was_used_per_agent(self):
        final_dict = {}
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                total_times_car = agent.kms_car[0]
                total_times_bycicle = agent.kms_bycicle[0]
                total_times_electric_scooter = agent.kms_electric_scooter[0]
                total_times_walk = agent.kms_walk[0]
                final_dict[agent.unique_id] = {"Total times car was used": total_times_car, "Total times bycicle was used": total_times_bycicle, "Total times electric scooter was used": total_times_electric_scooter, "Total times walk was used": total_times_walk}
        return final_dict  
    
    def calculate_time_spent_in_transports(self):
        final_dict = {}
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                time_kms_Car = agent.kms_car[1] / 40 # kms / 40km/h = time in hours
                time_kms_e_scooter = agent.kms_electric_scooter[1] * 12 # kms / 12km/h = time in hours
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

    def get_shortest_path(self, graph: nx.Graph, source_id: int, target_id: int) -> list[int]:
        return routing.shortest_path(graph, source_id, target_id, weight="length")

    def get_total_distance(self, graph: nx.Graph, path: list[int]) -> float:
        total_distance = 0.0

        # Iterate over consecutive pairs in the path
        for u, v in zip(path[:-1], path[1:]):
            mn_edge = min(graph[u][v].values(), key=lambda edge: edge["length"])
            total_distance += mn_edge["length"]
        return total_distance


    def step(self):
        self.data_collector.collect(self)
        self.schedule.step()


def load_graph(center_point, distance=5000) -> nx.Graph:
    G = ox.graph_from_point(center_point=center_point, dist=distance)
    G = osmnx.truncate.largest_component(G, strongly=True)
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
    ox.plot_graph(graph)
    plt.show()

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

    random_nodes = random.sample(sorted(graph.nodes.keys()), 2)
    print(f"Random nodes: {random_nodes}")
    shortest_path = model.get_shortest_path(graph, random_nodes[0], random_nodes[1])
    print(len(shortest_path))
    total_distance = model.get_total_distance(graph, shortest_path)
    print(total_distance)

    # Access the collected data for analysis
    results = model.data_collector.get_model_vars_dataframe()
    #print(results)
    print(results.head()) #need to understand what the columns refer to
    
    # Start plotting statistics
    # SustainableChoices --> How many sustainable choices were made per day
    g = sns.lineplot(data=results["SustainableChoices"])
    g.set(title="Sustainable Choices over Time", ylabel="Sustainable Choices", xlabel="Iterations")
    
    # CO2Emissions --> How CO2 emissions changed over time 
    # Time Spent in transports per agent --> Table to display this information where each row represents an agent
    # Number of times each transport was used overall --> the number of times each transport was used during the iterations
    # Which transport was used per agent --> Table to display this information where each row represents an agent
    


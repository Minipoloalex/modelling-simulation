from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from worker_agent import WorkerAgent, WorkerType
from company_agent import CompanyAgent

from graph_utils import load_graphs, random_position_within_radius, merge_graphs, create_subgraph_within_radius
from typing import Optional


import matplotlib.pyplot as plt
import seaborn as sns

CAR_CO2_VALUE = 250
ESCOOTER_CO2_VALUE = 67
DEFAULT_CO2_BUDGET = int(1e5)

class SustainabilityModel(Model):
    def __init__(
        self,
        num_workers: int = 10,
        worker_types_distribution: list = None,
        companies: list = None,
        graphs: dict[str, nx.Graph] = None,
        center_position: tuple[float, float] = None,
        company_location_radius: int = 1000,
        agent_home_radius: int = 5000,
        company_budget: int = DEFAULT_CO2_BUDGET,
        seed: Optional[int] = None,
    ):
        print("Init model", num_workers)
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
        self.company_budget = company_budget

        self.graphs = graphs
        self.grid = NetworkGrid(
            merge_graphs(
                graph_names=sorted(self.graphs.keys()),
                graphs=self.graphs
            )
        )

        # Use one of the graphs for company location visualization
        self.visualization_graph_type = sorted(self.graphs.keys())[0]

        self.schedule = RandomActivation(self)
        self.data_collector = DataCollector(
            model_reporters={
                # "SustainableChoices": self.calculate_sustainable_choices,
                "CO2_emissions": self.calculate_CO2_emissions, 
                "Time Spent in transports per agent": self.calculate_time_spent_in_transports,
                "CO2_avg_per_company": self.calculate_CO2_avg_per_company,
                # Travelled distance ?
                # "How many times each transport was used per agent": self.calculate_times_each_transport_was_used_per_agent
            },
            agent_reporters={"SustainableChoice": "sustainable_choice"},
        ) # Now we need to plot all these information at the end of the simulation for better visualization

        self.company_agents: list[CompanyAgent] = self.__init_companies(center_position, companies, company_location_radius)
        self.worker_agents: list[WorkerAgent] = self.__init_agents(center_position, worker_types_distribution, agent_home_radius)

        self.path_switches = 0
        self.finished = False

        self.visualization_graph = (
            self.grid.G
            if agent_home_radius <= 1000
            else create_subgraph_within_radius(self.grid.G, center_position, company_location_radius)
        )

    def __init_companies(self, center_position: tuple[float, float], companies, possible_radius):
        for company_count, company_policy in companies:
            for _ in range(company_count):
                position = random_position_within_radius(self.random, center_position, possible_radius)
                company = CompanyAgent(self, company_policy, position)
                self.schedule.add(company)
        return self.schedule.agents[: self.num_companies]

    def __init_agents(self, center_position: tuple[float, float], worker_types_distribution, possible_radius):
        probs, types = zip(*worker_types_distribution)
        transports = ["car", "bicycle", "electric scooters", "walking"] #electric scooters = trotinete elétrica

        for _ in range(self.num_workers):
            worker_type = self.random.choices(types, weights=probs, k=1)[0] # Get worker type according to distribution
            position = random_position_within_radius(self.random, center_position, possible_radius)
            transport = self.random.choice(transports)      # Random preferred transport
            company = self.random.choice(self.company_agents)    # Random company works in

            # Places itself on the grid at correct node
            worker = WorkerAgent(self, worker_type, transport, company, position)
            company.add_worker(worker)
            self.schedule.add(worker)

        return self.agents[self.num_companies :]

    def get_worker_positions(self):
        return {
            agent.unique_id: agent.pos for agent in self.worker_agents
        }

    def calculate_sustainable_choices(self):
        return sum(agent.kms_bycicle[0]+agent.kms_walk[0] for agent in self.schedule.agents if isinstance(agent, WorkerAgent))

    def calculate_times_each_transport_was_used(self):
        transports = ["car", "bike", "electric_scooter", "walk"]
        final_dict = {
            transport: 0
            for transport in transports
        }
        for agent in self.worker_agents:
            final_dict[agent.transport_chosen] += 1
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

    def get_total_co2(self, agent: WorkerAgent) -> float:
        return agent.kms_car[1] * CAR_CO2_VALUE + agent.kms_electric_scooter[1] * ESCOOTER_CO2_VALUE

    def calculate_CO2_emissions(self):
        CO2_kms_car = 0
        CO2_kms_e_scooter = 0
        for agent in self.worker_agents:
            CO2_kms_car += agent.kms_car[1] * CAR_CO2_VALUE # value of reference that I found in here: https://nought.tech/blogs/journal/are-e-scooters-good-for-the-environment#blog
            CO2_kms_e_scooter += agent.kms_electric_scooter[1] * ESCOOTER_CO2_VALUE # value of reference that I found in here: https://nought.tech/blogs/journal/are-e-scooters-good-for-the-environment#blog

        return {
            "car": CO2_kms_car,
            "eletric_scooter": CO2_kms_e_scooter,
        }

    def calculate_CO2_avg_per_company(self):
        companies_co2 = []
        for company in self.company_agents:
            company_co2 = 0
            for agent in company.workers:
                company_co2 += self.get_total_co2(agent)
            
            company_co2_avg = company_co2 / len(company.workers) if len(company.workers) != 0 else 0
            companies_co2.append(company_co2_avg)
        return companies_co2

    def step(self):
        self.schedule.step()
        self.data_collector.collect(self)

        partial_finish = all(agent.partial_finish for agent in self.worker_agents)
        if partial_finish:
            self.path_switches += 1
            for agent in self.worker_agents:
                agent.switch_path()

            if self.path_switches == 2:
                self.finished = True


# Running/Testing the model
if __name__ == "__main__":
    num_workers = 50

    center = 41.1664384, -8.6016
    graphs = load_graphs(center, distance=5000)
    # ox.plot_graph(drive)
    # plt.show()

    # center_node = get_closest_node(graph, center)
    worker_types_distribution = (
        [0.2, WorkerType.ENVIROMENTALLY_CONSCIOUS],
        [0.5, WorkerType.COST_SENSITIVE],
        [0.3, WorkerType.CONSERVATIVE],
    )
    companies = [(3, "policy0"), (2, "policy0"), (1, "policy0")]
    model = SustainabilityModel(
        num_workers,
        worker_types_distribution,
        companies,
        graphs,
        center_position=center,
        company_location_radius=1000,
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
    #print(results)
    #print(results) #need to understand what the columns refer to
    #results.to_csv("results.csv")
    # Start plotting statistics
    # Outdated plots were removed (plots can be found on app.py, probably should be moved to Model)
    # Time Spent in transports per agent --> Table to display this information where each row represents an agent
    # Number of times each transport was used overall --> the number of times each transport was used during the iterations
    # Which transport was used per agent --> Table to display this information where each row represents an agent
    


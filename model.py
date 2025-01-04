from mesa import Model
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from worker_agent import WorkerAgent
from company_agent import CompanyAgent, obtain_budget

from graph_utils import (
    load_graphs,
    random_position_within_radius,
    merge_graphs,
    create_subgraph_within_radius,
)
from typing import Optional
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

# CO2 is in grams
CAR_CO2_VALUE = 250
ESCOOTER_CO2_VALUE = 67
DEFAULT_CO2_BUDGET_PER_EMPLOYEE = int(5e2)   # Per employee

class SustainabilityModel(Model):
    def __init__(
        self,
        num_workers_per_company: int = 10,
        companies: dict[str, int] = None,
        graphs: dict[str, nx.Graph] = None,
        center_position: tuple[float, float] = None,
        company_location_radius: int = 1000,
        agent_home_radius: int = 5000,
        company_budget_per_employee: int = DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
        seed: Optional[int] = None,
    ):
        """
        Initialize the sustainability model with workers and companies.
        """
        super().__init__(seed=seed)
        self.num_companies = sum(company_cnt for company_cnt in companies.values())
        if self.num_companies == 0:
            raise ValueError("There must be at least one company")
        print(f"Init model with {num_workers_per_company} workers per company, with a total of {self.num_companies} companies")

        self.num_workers_per_company = num_workers_per_company
        self.num_agents = self.num_workers_per_company * self.num_companies + self.num_companies

        self.company_budget_per_employee = company_budget_per_employee
        self.base_company_budget = self.company_budget_per_employee * self.num_workers_per_company

        # TODO: merge graphs before passing to model
        # so the interface does not have to wait in reload for this
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
                "CO2_emissions": self.calculate_CO2_emissions, 
                "Time Spent in transports per agent": self.calculate_time_spent_in_transports,  # not plotted yet (should it be plotted?)
                "CO2_avg_per_company": self.calculate_CO2_avg_per_company,
                "CO2_avg_per_company_type": self.calculate_CO2_avg_per_company_type,
                # Travelled distance ?
            },
        )

        self.company_agents: list[CompanyAgent] = self.__init_companies(center_position, companies, company_location_radius)
        self.worker_agents: list[WorkerAgent] = self.__init_agents(center_position, agent_home_radius)

        self.path_switches = 0
        self.finished = False

        self.visualization_graph = (
            self.grid.G
            if agent_home_radius <= 1000
            else create_subgraph_within_radius(
                self.grid.G, center_position, distance_meters=company_location_radius
            )
        )

    def __init_companies(self, center_position: tuple[float, float], companies: dict[str, int], possible_radius: int):
        for company_policy, company_count in companies.items():
            for _ in range(company_count):
                position = random_position_within_radius(self.random, center_position, possible_radius)
                company = CompanyAgent(self, company_policy, position, self.base_company_budget)
                self.schedule.add(company)
        return self.schedule.agents[: self.num_companies]

    def __init_agents(self, center_position: tuple[float, float], possible_radius):
        for company in self.company_agents:
            for _ in range(self.num_workers_per_company):
                position = random_position_within_radius(self.random, center_position, possible_radius)
                worker = WorkerAgent(self, company, position)
                company.add_worker(worker)
                self.schedule.add(worker)

        return self.agents[self.num_companies :]

    def get_worker_positions(self):
        return {
            agent.unique_id: agent.pos for agent in self.worker_agents
        }

    # def calculate_sustainable_choices(self):
    #     return sum(agent.kms_bycicle[0]+agent.kms_walk[0] for agent in self.schedule.agents if isinstance(agent, WorkerAgent))

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
                time_kms_walk = agent.kms_walk[1] / 3.5 # kms / 3.5km/h = time in hours
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
            "electric_scooter": CO2_kms_e_scooter,
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

    def calculate_CO2_avg_per_company_type(self):
        companies_co2 = {}
        for company in self.company_agents:
            policy = company.policy
            company_co2 = 0
            for agent in company.workers:
                company_co2 += self.get_total_co2(agent)

            curr_sum, curr_cnt = companies_co2.get(policy, (0, 0))
            companies_co2[policy] = (curr_sum + company_co2, curr_cnt + 1)

        for policy, (co2_sum, cnt_companies) in companies_co2.items():
            companies_co2[policy] = co2_sum / cnt_companies
        return companies_co2

    def step(self):
        self.schedule.step()
        self.data_collector.collect(self)

        partial_finish = all(agent.partial_finish for agent in self.worker_agents)
        if partial_finish:
            # Wait until all agents have arrived at their destination before
            # making them go somewhere else (go back)
            self.path_switches += 1
            for agent in self.worker_agents:
                agent.switch_path()

            if self.path_switches == 2:
                self.finished = True

            if self.path_switches % 2 == 0:
                for company in self.company_agents:
                    if company.policy != "policy0" and company.policy != "policy1":
                        company.check_policies()

def get_transport_usage_plot(model: SustainabilityModel) -> Figure:
    """
    Generates a bar plot to visualize the times each transport method was used.

    Args:
        model: The simulation model instance.
    """
    results = model.calculate_times_each_transport_was_used()

    # Create a bar plot
    fig, ax = plt.subplots()
    ax.bar(results.keys(), results.values())
    ax.set_title("Transport Usage Frequency")
    ax.set_xlabel("Transport Method")
    ax.set_ylabel("Number of People")
    fig.tight_layout()
    return fig

def get_co2_emissions_plot(model: SustainabilityModel) -> Figure:
    transports = ["car", "bike", "walk", "electric_scooter"]
    co2_emissions = model.data_collector.get_model_vars_dataframe()["CO2_emissions"]
    timesteps = co2_emissions.index

    total_co2_emissions = co2_emissions.apply(lambda co2: sum(co2.values()))

    fig, ax = plt.subplots()

    for transport in transports:
        ax.plot(
            timesteps,
            co2_emissions.apply(lambda co2: co2.get(transport, 0)),
            label=transport,
            linestyle="dashed",
        )
    ax.plot(timesteps, total_co2_emissions, label="Total")

    ax.set_title("Total CO2 Emissions over time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("CO2 Emissions")
    ax.legend()
    fig.tight_layout()
    return fig

def get_co2_budget_per_company_type_plot(model: SustainabilityModel) -> Figure:
    co2_emissions_per_company_type = model.data_collector \
        .get_model_vars_dataframe()["CO2_avg_per_company_type"]

    timesteps = co2_emissions_per_company_type.index
    policies = (
        list(co2_emissions_per_company_type.iat[0].keys())
        if not co2_emissions_per_company_type.empty
        else []
    )

    # https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html
    linestyles = ['-', '--', '-.', ':', (0, (5, 10))]
    colors = ["green", "red", "blue", "purple", "orange"]
    if len(policies) > len(colors):
        raise NotImplementedError(
            "Add a new color for the additional policy (company type)"
        )

    fig, ax = plt.subplots()
    for i, policy in enumerate(policies):
        budget = obtain_budget(policy, model.base_company_budget)
        policy_co2_emissions = co2_emissions_per_company_type.apply(
            lambda co2: co2[policy]
        )
        ax.plot(
            timesteps,
            policy_co2_emissions,
            label=policy,
            color=colors[i],
        )
        
        largest_co2 = (
            policy_co2_emissions.iat[-1]
            if not policy_co2_emissions.empty
            else 0
        )
        plotted_budget = budget
        label = f"Budget for {policy}"
        # Plot up until the budget bigger than last CO2 emissions
        # for this company type
        while plotted_budget <= largest_co2 + budget:
            ax.axhline(
                y=plotted_budget,
                color=colors[i],
                linestyle=linestyles[i % len(linestyles)],
                label=label,
            )
            plotted_budget += budget
            label = None    # Only label the first horizontal line

    ax.set_title("Average CO2 emissions per company type (policy)")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("CO2 Emissions")
    ax.legend()
    fig.tight_layout()
    return fig

def get_co2_budget_plot(model: SustainabilityModel) -> Figure:
    budget = model.company_budget_per_employee
    co2_avgs = model.data_collector.get_model_vars_dataframe()["CO2_avg_per_company"]
    timesteps = co2_avgs.index
    co2_mean = co2_avgs.apply(np.mean)
    co2_std = co2_avgs.apply(np.std)

    fig, ax = plt.subplots()
    ax.plot(timesteps, co2_mean, label="Mean CO2 Emissions", color="blue")
    ax.fill_between(timesteps, co2_mean - co2_std, co2_mean + co2_std, color="blue", alpha=0.2, label="Std Dev")

    largest_co2_mean = (
        co2_mean.iat[-1]
        if not co2_avgs.empty
        else 0
    )
    plotted_budget = budget
    label = "Base Budget Per Employee"
    while plotted_budget <= largest_co2_mean + budget:
        ax.axhline(y=plotted_budget, color="red", linestyle="--", label=label)
        plotted_budget += budget
        label = None    # Only label the first horizontal line

    ax.set_title("CO2 Emissions Per Employee Over Time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("CO2 Emissions")
    ax.legend()
    fig.tight_layout()
    return fig


# Running/Testing the model
if __name__ == "__main__":
    num_workers_per_company = 10

    GRAPH_DISTANCE = 1000
    center = 41.1664384, -8.6016
    graphs = load_graphs(center, distance_meters=GRAPH_DISTANCE)

    companies = {
        "policy0": 3,
        "policy1": 2,
        "policy2": 4,
        "policy3": 2,
        "policy4": 1,
    }
    model = SustainabilityModel(
        num_workers_per_company,
        companies,
        graphs,
        center_position=center,
        company_location_radius=GRAPH_DISTANCE // 5,
        agent_home_radius=GRAPH_DISTANCE,
        seed=42
    )

    while not model.finished:
        model.step()
    print(f"Total number of model steps before finishing (one day): {model.steps}")

    # Access the collected data for analysis
    results = model.data_collector.get_model_vars_dataframe()
    print(results)
    print(results["CO2_avg_per_company_type"])

    transport_usage_plot = get_transport_usage_plot(model)
    transport_usage_plot.savefig("transport_usage.png")

    co2_emissions_plot = get_co2_emissions_plot(model)
    co2_emissions_plot.savefig("co2_emissions.png")

    co2_budget_plot = get_co2_budget_plot(model)
    co2_budget_plot.savefig("co2_budget.png")

    co2_budget_policy_type_plot = get_co2_budget_per_company_type_plot(model)
    co2_budget_policy_type_plot.savefig("co2_budget_policy_type.png")

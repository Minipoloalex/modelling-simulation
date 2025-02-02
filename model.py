from mesa import Model
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import networkx as nx
import numpy as np

from typing import Optional

from worker_agent import WorkerAgent
from company_agent import CompanyAgent, obtain_budget
from graph_utils import random_position_within_bouding_box

# Values are in grams per kms
CAR_CO2_G_KM = 250     # Value of reference found here: https://nought.tech/blogs/journal/are-e-scooters-good-for-the-environment#blog
ESCOOTER_CO2_G_KM = 67 # Value of reference found here: https://nought.tech/blogs/journal/are-e-scooters-good-for-the-environment#blog

# Values are in Euros (€) per kms
CAR_EURO_KM = 0.09          # cars with a consume cost of -> 5.0L/100km; 1L of gasoline -> 1.70
ESCOOTER_EURO_KM = 0.003     # 25km -> 225Wh ; 1 KWh -> 0.312
DEFAULT_CO2_BUDGET_PER_EMPLOYEE = int(1e3)   # Per employee

class SustainabilityModel(Model):
    def __init__(
        self,
        num_workers_per_company: int = 10,
        companies: dict[str, int] = None,
        graphs: dict[str, nx.Graph] = None,
        merged_graph: nx.Graph = None,
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

        self.graphs = graphs
        self.grid = NetworkGrid(merged_graph)

        # Use one of the graphs for company location visualization
        self.visualization_graph_type = sorted(self.graphs.keys())[0]

        self.schedule = RandomActivation(self)
        self.data_collector = DataCollector(
            model_reporters={
                "CO2_emissions": self.calculate_CO2_emissions, 
                "CO2_avg_per_company": self.calculate_CO2_avg_per_company,
                "CO2_avg_per_company_type": self.calculate_CO2_avg_per_company_type,
                "transport_costs": self.calculate_transport_costs,
            },
        )
        self.new_day_steps: list[int] = []

        self.company_agents: list[CompanyAgent] = self.__init_companies(center_position, companies, company_location_radius)
        self.worker_agents: list[WorkerAgent] = self.__init_agents(center_position, agent_home_radius)

        self.path_switches = 0
        self.finished = False

    def __init_companies(self, center_position: tuple[float, float], companies: dict[str, int], possible_radius: int):
        for company_policy, company_count in companies.items():
            for _ in range(company_count):
                position = random_position_within_bouding_box(self.random, center_position, bbox_distance_meters=possible_radius)
                company = CompanyAgent(self, company_policy, position, self.base_company_budget)
                self.schedule.add(company)
        return self.schedule.agents[: self.num_companies]

    def __init_agents(self, center_position: tuple[float, float], possible_radius):
        for company in self.company_agents:
            for _ in range(self.num_workers_per_company):
                position = random_position_within_bouding_box(self.random, center_position, bbox_distance_meters=possible_radius)
                worker = WorkerAgent(self, company, position)
                company.add_worker(worker)
                self.schedule.add(worker)

        return self.agents[self.num_companies :]

    def get_worker_positions(self):
        return {
            agent.unique_id: agent.pos for agent in self.worker_agents
        }

    def calculate_times_each_transport_was_used(self):
        transports = ["car", "bike", "electric_scooter", "walk"]
        final_dict = {
            transport: 0
            for transport in transports
        }
        for agent in self.worker_agents:
            final_dict[agent.transport_chosen] += 1
        return final_dict

    def calculate_times_each_transport_was_used_total(self):
        final_dict = {"car": 0, "bike": 0, "eletric_scooter": 0, "walk": 0}       
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                final_dict["car"] += agent.kms_car[0]
                final_dict["bike"] += agent.kms_bycicle[0]
                final_dict["eletric_scooter"] += agent.kms_electric_scooter[0]
                final_dict["walk"] += agent.kms_walk[0]
        return final_dict

    def calculate_times_each_transport_was_used_per_company_type(self):
        final_dict = {}
        for company in self.company_agents:
            policy = company.policy
            final_dict[policy] = final_dict.get(policy, {})
            final_dict[policy]["car"] = final_dict[policy].get("car", 0)
            final_dict[policy]["bike"] = final_dict[policy].get("bike", 0)
            final_dict[policy]["electric_scooter"] = final_dict[policy].get("electric_scooter", 0)
            final_dict[policy]["walk"] = final_dict[policy].get("walk", 0)
            for worker in company.workers:
                final_dict[policy]["car"] += worker.kms_car[0]
                final_dict[policy]["bike"] += worker.kms_bycicle[0]
                final_dict[policy]["electric_scooter"] += worker.kms_electric_scooter[0]
                final_dict[policy]["walk"] += worker.kms_walk[0]
        return final_dict

    def get_total_co2(self, agent: WorkerAgent) -> float:
        return agent.kms_car[1] * CAR_CO2_G_KM + agent.kms_electric_scooter[1] * ESCOOTER_CO2_G_KM

    def calculate_CO2_emissions(self):
        CO2_kms_car = 0
        CO2_kms_e_scooter = 0
        for agent in self.worker_agents:
            CO2_kms_car += agent.kms_car[1] * CAR_CO2_G_KM
            CO2_kms_e_scooter += agent.kms_electric_scooter[1] * ESCOOTER_CO2_G_KM

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

    def calculate_transport_costs(self):
        transport_costs = []
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent):
                cost_car = agent.kms_car[1] * CAR_EURO_KM
                cost_electric_scooter = agent.kms_electric_scooter[1] * ESCOOTER_EURO_KM
                total_cost = cost_car + cost_electric_scooter 
                transport_costs.append(total_cost)
        return transport_costs
    
    def calculate_transport_costs_for_company(self,company):
        cost_per_km_car = 0.09  # cars with a consume cost of -> 5.0L/100km; 1L of gasoline -> 1.70; VALOR EM EUROS
        cost_per_km_electric_scooter = 0.003 # 25km -> 225Wh ; 1 KWh -> 0.312 ; VALOR EM EUROS  

        transport_costs = []
        for agent in self.schedule.agents:
            if isinstance(agent, WorkerAgent) and agent.company == company:
                cost_car = agent.kms_car[1] * cost_per_km_car
                cost_electric_scooter = agent.kms_electric_scooter[1] * cost_per_km_electric_scooter
                total_cost = cost_car + cost_electric_scooter 
                transport_costs.append(total_cost)
        return transport_costs

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

            if self.path_switches % 2 == 0:
                self.new_day_steps.append(self.steps)
                for company in self.company_agents:
                    if company.policy != "policy0" and company.policy != "policy1":
                        company.check_policies()

                if len(self.new_day_steps) == 30:
                    self.finished = True

def get_current_transport_usage_plot(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    """
    Generates a bar plot to visualize the times each transport method was used.

    Args:
        model: The simulation model instance.
    """
    results = model.calculate_times_each_transport_was_used()

    # Create a bar plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(results.keys(), results.values())
    if set_title:
        ax.set_title("Current Transport Usage")
    ax.set_xlabel("Transport Method")
    ax.set_ylabel("Number of People")
    fig.tight_layout()
    return fig

def get_total_transport_usage_plot(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    """
    Generates a bar plot to visualize the times each transport method was used.

    Args:
        model: The simulation model instance.
    """
    results = model.calculate_times_each_transport_was_used_total()

    # Create a bar plot
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(results.keys(), results.values())
    if set_title:
        ax.set_title("Total Transport Usage")
    ax.set_xlabel("Transport Method")
    ax.set_ylabel("Number of Choices")
    fig.tight_layout()
    return fig

def get_total_transport_usage_plot_per_company_type(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    results = model.calculate_times_each_transport_was_used_per_company_type()
    policies = list(results.keys())  # First-level keys (policies)
    transports = list(next(iter(results.values())).keys())  # Second-level keys (transports)
    values = np.array([[results[policy].get(transport, 0) for transport in transports] for policy in policies])

    x = np.arange(len(transports))  # Position for each transport group
    width = 0.2  # Width of each smaller bar

    fig, ax = plt.subplots(figsize=figsize)

    for i, policy in enumerate(policies):
        ax.bar(x + i * width, values[i], width, label=policy)

    if set_title:
        ax.set_title("Transport usage by company policy")
    ax.set_xlabel("Transport Method")
    ax.set_ylabel("Number of Choices")
    ax.set_xticks(x + width * (len(policies) - 1) / 2)
    ax.set_xticklabels(transports)
    ax.legend(title="Policies")

    # Adjust layout and return figure
    fig.tight_layout()
    return fig


def get_co2_emissions_plot(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    transports = ["car", "bike", "walk", "electric_scooter"]
    co2_emissions = model.data_collector.get_model_vars_dataframe()["CO2_emissions"]
    timesteps = co2_emissions.index

    total_co2_emissions = co2_emissions.apply(lambda co2: sum(co2.values()))

    fig, ax = plt.subplots(figsize=figsize)

    for transport in transports:
        ax.plot(
            timesteps,
            co2_emissions.apply(lambda co2: co2.get(transport, 0)),
            label=transport,
            linestyle="dashed",
        )
    ax.plot(timesteps, total_co2_emissions, label="Total")

    if set_title:
        ax.set_title("Total Carbon Dioxide emissions over time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Carbon Dioxide emissions (g)")
    ax.legend()
    fig.tight_layout()
    return fig

def _get_budget_plot_line_points(
    new_day_steps: list[int], curr_day_step, budget_per_day: float,
) -> tuple[list[int], list[float]]:
    """
    Helper to plot budget lines that increase upon each day completed.
    Returns the list of X and Y coordinates for the points of the budget lines.
    """
    curr_budget = budget_per_day
    xl = [0]
    yl = [budget_per_day]
    for day in new_day_steps:
        xl += [day, day]
        yl += [curr_budget, curr_budget + budget_per_day]
        curr_budget += budget_per_day

    xl.append(curr_day_step)
    yl.append(curr_budget)
    return xl, yl


def get_co2_budget_per_company_type_plot(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    plot_budget_lines: bool = True,
    set_title: bool = True,
) -> Figure:
    co2_emissions_per_company_type = model.data_collector \
        .get_model_vars_dataframe()["CO2_avg_per_company_type"]

    timesteps = co2_emissions_per_company_type.index
    all_policies = (
        list(co2_emissions_per_company_type.iat[0].keys())
        if not co2_emissions_per_company_type.empty
        else []
    )

    colors = ["green", "red", "blue", "purple", "orange"]
    if len(all_policies) > len(colors):
        raise NotImplementedError(
            "Add a new color for the additional policy (company type)"
        )

    budgets = {}
    for policy in all_policies:
        budget = obtain_budget(policy, model.base_company_budget)
        budgets[budget] = budgets.get(budget, [])
        budgets[budget].append(policy)

    fig, ax = plt.subplots(figsize=figsize)
    policy_nr = 0
    for budget, policies in budgets.items():
        if plot_budget_lines:
            budget_xs, budget_ys = _get_budget_plot_line_points(model.new_day_steps, model.steps, budget)
            ax.plot(
                budget_xs, budget_ys,
                linestyle="--", color=colors[policy_nr], drawstyle='steps-post',
                label=f"Budget for " + ", ".join(policies),
            )

        for policy in policies:
            policy_co2_emissions = co2_emissions_per_company_type.apply(
                lambda co2: co2[policy]
            )
            ax.plot(
                timesteps,
                policy_co2_emissions,
                label=policy,
                color=colors[policy_nr],
            )
            policy_nr += 1

    if set_title:
        ax.set_title("Carbon Dioxide emissions per company type over time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Carbon Dioxide emissions per company type (g)")
    ax.legend()
    fig.tight_layout()
    return fig


def get_co2_budget_plot(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    budget = model.company_budget_per_employee
    co2_avgs = model.data_collector.get_model_vars_dataframe()["CO2_avg_per_company"]
    timesteps = co2_avgs.index
    co2_mean = co2_avgs.apply(np.mean)
    co2_std = co2_avgs.apply(np.std)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(timesteps, co2_mean, label="Mean of CO2 emissions", color="blue")
    ax.fill_between(timesteps, co2_mean - co2_std, co2_mean + co2_std, color="blue", alpha=0.2, label="Standard deviation of CO2 emissions")

    budget_xs, budget_ys = _get_budget_plot_line_points(model.new_day_steps, model.steps, budget)
    ax.plot(
        budget_xs, budget_ys,
        linestyle="--", color="red", drawstyle='steps-post',
        label="Base Budget Per Employee",
    )

    if set_title:
        ax.set_title("Carbon Dioxide emissions per employee over time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Carbon Dioxide emissions per employee (g)")
    ax.legend()
    fig.tight_layout()
    return fig

def get_transport_costs_plot(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    transport_costs = model.data_collector.get_model_vars_dataframe()["transport_costs"]
    timesteps = transport_costs.index
    cost_mean = transport_costs.apply(np.mean)
    cost_std = transport_costs.apply(np.std)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(timesteps, cost_mean, label="Mean of transport costs", color="blue")
    ax.fill_between(timesteps, cost_mean - cost_std, cost_mean + cost_std, color="blue", alpha=0.2, label="Standard deviation of transport costs")

    if set_title:
        ax.set_title("Transport costs per employee over time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("Transport costs per employee (€)")
    ax.legend()
    fig.tight_layout()
    return fig

def get_emissions_plot_company_comparison(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    sustainable_companies = [company for company in model.company_agents if company.policy in ["policy1"]]
    non_sustainable_companies = [company for company in model.company_agents if company.policy in ["policy0"]]

    sustainable_emissions = np.mean([model.get_total_co2(agent) for company in sustainable_companies for agent in company.workers])
    non_sustainable_emissions = np.mean([model.get_total_co2(agent) for company in non_sustainable_companies for agent in company.workers])

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(["Sustainable", "Non-Sustainable"], [sustainable_emissions, non_sustainable_emissions])

    if set_title:
        ax.set_title("Carbon Dioxide emissions in Sustainable vs Nonsustainable companies")
    ax.set_ylabel("Carbon Dioxide Emissions per employee (g)")
    fig.tight_layout()
    return fig

def get_costs_plot_company_comparison(
    model: SustainabilityModel,
    figsize: Optional[tuple[float, float]] = None,
    set_title: bool = True,
) -> Figure:
    sustainable_companies = [company for company in model.company_agents if company.policy in ["policy1"]]
    non_sustainable_companies = [company for company in model.company_agents if company.policy in ["policy0"]]

    sustainable_costs = np.mean([model.calculate_transport_costs_for_company(company) for company in sustainable_companies])
    non_sustainable_costs = np.mean([model.calculate_transport_costs_for_company(company) for company in non_sustainable_companies])

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(["Sustainable", "Non-Sustainable"], [sustainable_costs, non_sustainable_costs])

    if set_title:
        ax.set_title("Monetary Costs in Sustainable vs Nonsustainable companies")
    ax.set_ylabel("Monetary Costs per employee (€)")
    fig.tight_layout()
    return fig

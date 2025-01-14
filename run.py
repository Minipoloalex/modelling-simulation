from graph_utils import (
    load_graphs,
    merge_graphs,
)
import time

import matplotlib.pyplot as plt
import seaborn as sns
from model import *

# Modifiable parameters
num_workers_per_company = 50
companies = {
    "policy2": 3,
    "policy3": 3,
    "policy4": 3,
}
# Default CO2: DEFAULT_CO2_BUDGET_PER_EMPLOYEE
company_budget_per_employee = DEFAULT_CO2_BUDGET_PER_EMPLOYEE

# Non-modifiable parameters
GRAPH_DISTANCE = 5000
center = 41.1664384, -8.6016

# Print time taken to complete a task
def print_time_taken(before: float, after: float, task: str) -> None:
    print(f"Time taken to complete '{task}': {after - before:.3f} seconds")


before = time.time()

graphs = load_graphs(center, distance_meters=GRAPH_DISTANCE)
merged_graph = merge_graphs(graphs)

after = time.time()
print_time_taken(before, after, "load and merge graphs")


before = time.time()

model = SustainabilityModel(
    num_workers_per_company,
    companies,
    graphs,
    merged_graph,
    center_position=center,
    company_location_radius=GRAPH_DISTANCE // 5,
    agent_home_radius=GRAPH_DISTANCE,
    company_budget_per_employee=DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
    seed=42
)

after = time.time()
print_time_taken(before, after, "create the model")

before = time.time()
while not model.days_complete == 31:
    model.step()
after = time.time()
print_time_taken(before, after, "simulation")

print(f"Total number of model steps before finishing (one day): {model.steps}")

transport_usage_plot = get_transport_usage_plot(model)
transport_usage_plot.savefig("transport_usage.png")

transport_total_usage_plot = get_total_transport_usage_plot(model)
transport_total_usage_plot.savefig("total_transport_usage.png")

co2_emissions_plot = get_co2_emissions_plot(model)
co2_emissions_plot.savefig("co2_emissions.png")

co2_budget_plot = get_co2_budget_plot(model)
co2_budget_plot.savefig("co2_budget.png")

co2_budget_policy_type_plot = get_co2_budget_per_company_type_plot(model)
co2_budget_policy_type_plot.savefig("co2_budget_policy_type.png")

cost_benefit_per_employee_plot = get_transport_costs_plot(model)
cost_benefit_per_employee_plot.savefig("cost_benefit_per_employee.png")

transport_usage_per_type_plot = get_total_transport_usage_plot_per_company_type(model)
transport_usage_per_type_plot.savefig("transport_usage_per_type_plot.png")

import time

from graph_utils import (
    load_graphs,
    merge_graphs,
)
from model import *

# Modifiable parameters
num_workers_per_company = 20
companies = {
    "policy0": 6,
    # "policy1": 3,
    # "policy2": 3,
    # "policy3": 3,
    # "policy4": 3,
}
# Default CO2 budget: DEFAULT_CO2_BUDGET_PER_EMPLOYEE
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
    seed=5,
)

after = time.time()
print_time_taken(before, after, "create the model")

before = time.time()
while not model.finished:
    model.step()
after = time.time()
print_time_taken(before, after, "simulation")

print(f"Total number of model steps before finishing (one month): {model.steps}")

transport_total_usage_plot = get_total_transport_usage_plot(model, set_title=False)
transport_total_usage_plot.savefig("total_transport_usage.png")

co2_emissions_plot = get_co2_emissions_plot(model, set_title=False)
co2_emissions_plot.savefig("co2_emissions.png")

co2_budget_plot = get_co2_budget_plot(model, set_title=False)
co2_budget_plot.savefig("co2_budget.png")

co2_budget_policy_type_plot = get_co2_budget_per_company_type_plot(model, set_title=False)
co2_budget_policy_type_plot.savefig("co2_budget_policy_type.png")

co2_policy_type_plot = get_co2_budget_per_company_type_plot(model, plot_budget_lines=False, set_title=False)
co2_policy_type_plot.savefig("co2_policy_type.png")

cost_benefit_per_employee_plot = get_transport_costs_plot(model, set_title=False)
cost_benefit_per_employee_plot.savefig("cost_benefit_per_employee.png")

transport_usage_per_type_plot = get_total_transport_usage_plot_per_company_type(model, set_title=False)
transport_usage_per_type_plot.savefig("transport_usage_per_type_plot.png")

comparison_emissions_plot = get_emissions_plot_company_comparison(model, set_title=False)
comparison_emissions_plot.savefig("emissions_comparison.png")

comparison_costs_plot = get_costs_plot_company_comparison(model, set_title=False)
comparison_costs_plot.savefig("costs_comparison.png")

import mesa
print(f"Mesa version: {mesa.__version__}")

import networkx as nx
from mesa.visualization import SolaraViz
from graph_utils import load_graphs
import solara
from matplotlib.figure import Figure

from model import SustainabilityModel, get_transport_usage_plot, get_co2_emissions_plot, get_co2_budget_plot
import matplotlib.pyplot as plt
import seaborn as sns

import networkx as nx
import matplotlib.pyplot as plt
import solara
import numpy as np
from model import DEFAULT_CO2_BUDGET_PER_EMPLOYEE

total_radius = 5000 # 1000m for developing, 5000m for actual simulations
company_location_radius = total_radius // 5
center = 41.1664384, -8.6016
graphs = load_graphs(center, distance=total_radius)
companies = [(3, "policy0"), (2, "policy1"), (1, "policy2"), (1, "policy3"), (1, "policy4")]
num_workers_per_company = 10

model_params = {
    "num_workers_per_company": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of workers per Company",
        "min": 2,
        "max": 20,
        "step": 1,
    },
    "companies": companies,
    "graphs": graphs,
    "center_position": center,
    "company_location_radius": company_location_radius,
    "agent_home_radius": total_radius,
    "base_company_budget": DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
    "seed": 42,
}

model = SustainabilityModel(
    num_workers_per_company=num_workers_per_company,
    companies=companies,
    graphs=graphs,
    center_position=center,
    company_location_radius=company_location_radius,
    agent_home_radius=total_radius,
    base_company_budget=DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
    seed=42,
)

class Debugger:
    ig = 1
    ip = 1
    @staticmethod
    def debug_graph_rendering(model):
        print(f"{Debugger.ig}: Rendering graph")
        Debugger.ig += 1
    @staticmethod
    def debug_plot(model):
        print(f"{Debugger.ip}: Rendering plot")
        Debugger.ip += 1

def make_graph(model: SustainabilityModel):
    Debugger.debug_graph_rendering(model)
    worker_agent_positions_state = model.get_worker_positions()
    visualization_graph = model.visualization_graph

    pos = {
        node: (data["x"], data["y"])
        for node, data in visualization_graph.nodes(data=True)
    }

    company_nodes = [
        company.pos
        for company in model.company_agents
        if company.pos in visualization_graph.nodes
    ]

    worker_nodes = {}
    for worker_node in worker_agent_positions_state.values():
        if worker_node in visualization_graph.nodes:
            worker_nodes[worker_node] = worker_nodes.get(worker_node, 0) + 1

    fig, ax = plt.subplots()
    nx.draw(
        visualization_graph,
        pos=pos,
        ax=ax,
        node_size=1,
        node_color="black",
        edge_color="black",
        with_labels=False,
        arrows=False,
    )
    min_size = 100
    max_size = 300
    max_count = len(worker_agent_positions_state)
    sizes = [min_size + (max_size - min_size) * (count / max_count) for count in worker_nodes.values()]

    ax.scatter(
        [visualization_graph.nodes[worker_node]["x"] for worker_node in worker_nodes.keys()],
        [visualization_graph.nodes[worker_node]["y"] for worker_node in worker_nodes.keys()],
        s=sizes,
        cmap=None,
        facecolors="none",  # not filled
        edgecolors="green",
        linewidths=2
    )

    ax.scatter(
        [visualization_graph.nodes[company_node]["x"] for company_node in company_nodes],
        [visualization_graph.nodes[company_node]["y"] for company_node in company_nodes],
        s=30,
        c="blue",
    )
    solara_figure = solara.FigureMatplotlib(fig)

    # Close the matplotlib figure explicitly (otherwise unused figures would still be open)
    plt.close(fig)

    return solara_figure

def make_transport_usage_plot(model: SustainabilityModel):
    fig = get_transport_usage_plot(model)

    solara_figure = solara.FigureMatplotlib(fig)
    plt.close(fig)

    return solara_figure

def make_co2_emissions_plot(model: SustainabilityModel):
    Debugger.debug_plot(model)
    fig = get_co2_emissions_plot(model)

    solara_figure = solara.FigureMatplotlib(fig)
    plt.close(fig)

    return solara_figure

def make_co2_budget_plot(model: SustainabilityModel):
    fig = get_co2_budget_plot(model)

    solara_figure = solara.FigureMatplotlib(fig)
    plt.close(fig)

    return solara_figure

@solara.component
def Page():
    solara.Title("Sustainability Model")    
    SolaraViz(
        model,
        components=[
            make_graph,
            make_co2_emissions_plot,
            make_transport_usage_plot,
            make_co2_budget_plot,
        ],
        model_params=model_params,
        name="Sustainability Model",
    )

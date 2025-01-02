import mesa
print(f"Mesa version: {mesa.__version__}")

import networkx as nx
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from graph_utils import load_graphs
import solara
from matplotlib.figure import Figure

from model import SustainabilityModel, WorkerType
import matplotlib.pyplot as plt
import seaborn as sns

import networkx as nx
import matplotlib.pyplot as plt
import solara
import numpy as np

total_radius = 1000
company_location_radius = total_radius // 5
center = 41.1664384, -8.6016
graphs = load_graphs(center, distance=total_radius)
worker_types_distribution = (
    [0.2, WorkerType.ENVIROMENTALLY_CONSCIOUS],
    [0.5, WorkerType.COST_SENSITIVE],
    [0.3, WorkerType.CONSERVATIVE],
)
companies = [(3, "policy0"), (2, "policy0"), (1, "policy0")]
num_workers = 50

model_params = {
    "num_workers": {
        "type": "SliderInt",
        "value": 50,
        "label": "Number of workers",
        "min": 5,
        "max": 60,
        "step": 1,
    },
    "worker_types_distribution": worker_types_distribution,
    "companies": companies,
    "graphs": graphs,
    "center_position": center,
    "company_location_radius": company_location_radius,
    "agent_home_radius": total_radius,
    "seed": 42,
}

model = SustainabilityModel(
    num_workers=num_workers,
    worker_types_distribution=worker_types_distribution,
    companies=companies,
    graphs=graphs,
    center_position=center,
    company_location_radius=company_location_radius,
    agent_home_radius=total_radius,
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
    merged_graph = model.grid.G

    pos = {
        node: (data["x"], data["y"])
        for node, data in merged_graph.nodes(data=True)
    }

    company_nodes = [company.pos for company in model.company_agents]
    # company_color = "black"
    # for company_node in company_nodes:
    #     pos[company_node] = (
    #         merged_graph.nodes[company_node]["x"],
    #         merged_graph.nodes[company_node]["y"],
    #     )

    # node_colors = [
    #     company_color if node in company_nodes else data.get("color", "#FFFFFF")
    #     for node, data in merged_graph.nodes(data=True)
    # ]
    # edge_colors = [data.get("color", "gray") for _, _, data in merged_graph.edges(data=True)]
    # node_sizes = [
    #     20 if node in company_nodes else 1
    #     for node in merged_graph.nodes
    # ]

    worker_nodes = {}
    for worker_node in worker_agent_positions_state.values():
        worker_nodes[worker_node] = worker_nodes.get(worker_node, 0) + 1

    fig, ax = plt.subplots()
    nx.draw(
        merged_graph,
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
        [merged_graph.nodes[worker_node]["x"] for worker_node in worker_nodes.keys()],
        [merged_graph.nodes[worker_node]["y"] for worker_node in worker_nodes.keys()],
        s=sizes,
        c=None,
        cmap=None,
        facecolors="none",  # not filled
        edgecolors="black",
    )

    ax.scatter(
        [merged_graph.nodes[company_node]["x"] for company_node in company_nodes],
        [merged_graph.nodes[company_node]["y"] for company_node in company_nodes],
        s=30,
        c="black",
    )
    solara_figure = solara.FigureMatplotlib(fig)

    # Close the matplotlib figure explicitly (otherwise unused figures would still be open)
    plt.close(fig)

    return solara_figure

def make_transport_usage_plot(model: SustainabilityModel):
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

    # Render the plot in Solara
    solara_figure = solara.FigureMatplotlib(fig)

    plt.close(fig)

    return solara_figure

def make_co2_emissions_plot(model: SustainabilityModel):
    Debugger.debug_plot(model)
    transports = ["car", "bike", "walk", "eletric_scooter"]
    co2_emissions = model.data_collector.get_model_vars_dataframe()["CO2_emissions"]
    timesteps = co2_emissions.index
    # co2_emissions_car = co2_emissions.apply(lambda co2: co2["car"])
    
    total_co2_emissions = co2_emissions.apply(lambda co2: sum(co2.values()))

    fig, ax = plt.subplots()

    for transport in transports:
        ax.plot(timesteps, co2_emissions.apply(lambda co2: co2.get(transport, 0)), label=transport, linestyle="dashed")
    ax.plot(timesteps, total_co2_emissions, label="Total")

    ax.set_title("CO2 Emissions over time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("CO2 Emissions")
    ax.legend()
    fig.tight_layout()

    # Render the plot in Solara
    solara_figure = solara.FigureMatplotlib(fig)
    plt.close(fig)

    return solara_figure

def make_co2_budget_plot(model: SustainabilityModel):
    budget = model.company_budget
    co2_avgs = model.data_collector.get_model_vars_dataframe()["CO2_avg_per_company"]
    timesteps = co2_avgs.index
    co2_mean = co2_avgs.apply(np.mean)
    co2_std = co2_avgs.apply(np.std)

    fig, ax = plt.subplots()
    ax.plot(timesteps, co2_mean, label="Mean CO2 Emissions", color="blue")
    ax.fill_between(timesteps, co2_mean - co2_std, co2_mean + co2_std, color="blue", alpha=0.2, label="Std Dev")
    ax.axhline(y=budget, color="red", linestyle="--", label="Budget Per Day")
    ax.set_title("CO2 Emissions Per Employee Over Time")
    ax.set_xlabel("Time Step")
    ax.set_ylabel("CO2 Emissions")
    ax.legend()

    # Render the plot in Solara
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

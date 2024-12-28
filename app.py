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

DISTANCE_FACTOR = 10

class Debugger:
    i = 1
    @staticmethod
    def debug_graph_rendering(model):
        print(f"{Debugger.i}: Rendering graph")
        Debugger.i += 1

def make_graph(model):
    Debugger.debug_graph_rendering(model)
    worker_agent_positions_state = model.get_worker_positions()
    merged_graph = model.grid.G

    pos = {
        node: (data["x"] * DISTANCE_FACTOR, data["y"] * DISTANCE_FACTOR)
        for node, data in merged_graph.nodes(data=True)
    }

    company_nodes = [company.pos for company in model.company_agents]
    company_color = "black"
    for company_node in company_nodes:
        pos[company_node] = (
            merged_graph.nodes[company_node]["x"] * DISTANCE_FACTOR,
            merged_graph.nodes[company_node]["y"] * DISTANCE_FACTOR,
        )

    node_colors = [
        company_color if node in company_nodes else data.get("color", "#FFFFFF")
        for node, data in merged_graph.nodes(data=True)
    ]
    edge_colors = [data.get("color", "gray") for _, _, data in merged_graph.edges(data=True)]
    node_sizes = [
        20 if node in company_nodes else 1
        for node in merged_graph.nodes
    ]

    fig, ax = plt.subplots(figsize=(10, 10))
    worker_nodes = {}
    for worker_node in worker_agent_positions_state.values():
        worker_nodes[worker_node] = worker_nodes.get(worker_node, 0) + 1

    nx.draw(
        merged_graph,
        pos=pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        edge_color=edge_colors,
        with_labels=False,
        arrows=False,
    )
    min_size = 100
    max_size = 300
    max_count = len(worker_agent_positions_state)
    sizes = [min_size + (max_size - min_size) * (count / max_count) for count in worker_nodes.values()]

    ax.scatter(
        [merged_graph.nodes[worker_node]["x"] * DISTANCE_FACTOR for worker_node in worker_nodes.keys()],
        [merged_graph.nodes[worker_node]["y"] * DISTANCE_FACTOR for worker_node in worker_nodes.keys()],
        s=sizes,
        c=None,
        cmap=None,
        facecolors="none",  # not filled
        edgecolors="black",
    )

    ax.scatter(
        [merged_graph.nodes[company_node]["x"] * DISTANCE_FACTOR for company_node in company_nodes],
        [merged_graph.nodes[company_node]["y"] * DISTANCE_FACTOR for company_node in company_nodes],
        s=30,
        c="black",
    )
    solara_figure = solara.FigureMatplotlib(fig)

    # Close the matplotlib figure explicitly (otherwise unused figures would still be open)
    plt.close(fig)

    return solara_figure


@solara.component
def Page():
    solara.Title("Sustainability Model")    
    SolaraViz(
        model,
        components=[
            make_graph,
        ],
        model_params=model_params,
        name="Sustainability Model",
    )

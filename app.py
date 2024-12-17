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
num_workers = 5

import networkx as nx
import matplotlib.pyplot as plt
import solara
import numpy as np

@solara.component
def ShowGraph(num_workers):
    # Initialize the model
    model = SustainabilityModel(
        num_workers=num_workers,
        worker_types_distribution=worker_types_distribution,
        companies=companies,
        graphs=graphs,
        center_position=center,
        company_location_radius=company_location_radius,
        agent_home_radius=total_radius,
        seed=42
    )

    # Define colors for each graph
    graph_colors = ["#FF0000", "#00FF00", "#0000FF"]  # RGB
    grid_names = sorted(model.grids.keys())  # Sort grid names

    # Initialize a merged graph
    merged_graph = nx.MultiDiGraph()

    # Step 1: Add nodes and edges to the merged graph with attributes
    for i, grid_name in enumerate(grid_names):
        color = graph_colors[i]
        graph = model.grids[grid_name].G

        # Add nodes with color attribute
        for node, data in graph.nodes(data=True):
            if merged_graph.has_node(node):
                # If the node exists, combine the color
                existing_color = merged_graph.nodes[node].get("color", "#FFFFFF")  # Default to white
                merged_graph.nodes[node]["color"] = mix_colors(existing_color, color)
            else:
                merged_graph.add_node(node, **data, color=color)

        # Add edges with color attribute
        for u, v, data in graph.edges(data=True):
            # Check if edge exists already, merge the color
            if merged_graph.has_edge(u, v):
                # Combine the color for existing edges
                for edge_key in merged_graph[u][v]:
                    existing_color = merged_graph[u][v][edge_key].get("color", "#FFFFFF")
                    merged_graph[u][v][edge_key]["color"] = mix_colors(existing_color, color)
            else:
                merged_graph.add_edge(u, v, color=color, **data)


    # Step 2: Define positions for the nodes
    DISTANCE_FACTOR = 10
    pos = {
        node: (data["x"] * DISTANCE_FACTOR, data["y"] * DISTANCE_FACTOR)
        for node, data in merged_graph.nodes(data=True)
        if "x" in data and "y" in data
    }

    # Step 3: Draw the merged graph
    fig, ax = plt.subplots(figsize=(10, 10))

    # Draw nodes with colors
    node_colors = [data.get("color", "#FFFFFF") for _, data in merged_graph.nodes(data=True)]
    edge_colors = [data.get("color", "gray") for _, _, data in merged_graph.edges(data=True)]
    nx.draw(
        merged_graph,
        pos=pos,
        ax=ax,
        node_size=1,
        node_color=node_colors,
        edge_color=edge_colors,
        with_labels=False,
        arrows=False
    )

    # Display the figure in Solara
    solara.FigureMatplotlib(fig)


def mix_colors(color1, color2):
    """
    Mix two hex colors by adding their RGB components.
    """
    rgb1 = np.array([int(color1[i:i+2], 16) for i in (1, 3, 5)])
    rgb2 = np.array([int(color2[i:i+2], 16) for i in (1, 3, 5)])
    mixed_rgb = np.minimum(255, (rgb1 + rgb2).astype(int))
    return f"#{mixed_rgb[0]:02x}{mixed_rgb[1]:02x}{mixed_rgb[2]:02x}"


# Run the Solara app
@solara.component
def Page():
    num_workers, set_num_workers = solara.use_state(10)
    solara.Title("Sustainability Model Graph")
    with solara.Row():
        solara.Text("Number of Workers:")
        solara.SliderInt(label="Workers", value=num_workers, min=1, max=100, on_value=set_num_workers)
    ShowGraph(num_workers=num_workers)

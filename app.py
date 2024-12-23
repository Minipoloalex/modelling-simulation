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
num_workers = 5

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

    # # Reactive state for agent positions
    # worker_agent_positions_state, set_worker_agent_positions_state = solara.use_state(model.get_worker_positions())

    # Step function to update the model and agent positions
    def update():
        model.step()

    #     # Update agent positions in reactive state
    #     set_worker_agent_positions_state(model.get_worker_positions())

    merged_graph = model.grid.G

    # Step 2: Define positions for the nodes
    DISTANCE_FACTOR = 10
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
    nx.draw(
        merged_graph,
        pos=pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        edge_color=edge_colors,
        with_labels=False,
        arrows=False
    )

    # Draw agent nodes on top with larger size and specific colors
    # agent_colors = {
    #     agent_id: "#FFA500"  # Default orange color for agents
    #     for agent_id in agent_positions_state.keys()
    # }
    # nx.draw_networkx_nodes(
    #     merged_graph,
    #     pos=pos,
    #     ax=ax,
    #     nodelist=list(agent_positions_state.keys()),
    #     node_color=list(agent_colors.values()),
    #     node_size=100,  # Bigger size for agents
    # )
    # Step 3: Get company positions
    # company_positions = {
    #     company.pos: (merged_graph[company.pos]['x'], merged_graph[company.pos]['x'])
    #     for company in model.company_agents
    # }
    company_positions = {
        company.pos: (
            merged_graph.nodes[company.pos]["x"],
            merged_graph.nodes[company.pos]["y"]
        )
        for company in model.company_agents
    }
    print(company_positions)
    
    # Add company positions to pos
    # for company_id, company_pos in company_positions.items():
    #     pos[company_id] = (
    #         company_pos[0] * DISTANCE_FACTOR,
    #         company_pos[1] * DISTANCE_FACTOR,
    #     )
    # Draw company nodes on top with larger size and distinct colors
    # nx.draw_networkx_nodes(
    #     merged_graph,
    #     pos=company_positions,
    #     ax=ax,
    #     nodelist=list(company_positions.keys()),
    #     node_color="#FFD700",  # Gold color for companies
    #     node_size=20,  # Larger size for companies
    # )

    # Display the figure in Solara
    solara.FigureMatplotlib(fig)

    # Add a button to step through the simulation
    solara.Button("Next Step", on_click=update)


# Run the Solara app
@solara.component
def Page():
    num_workers, set_num_workers = solara.use_state(10)
    solara.Title("Sustainability Model Graph")
    with solara.Row():
        solara.Text("Number of Workers:")
        solara.SliderInt(label="Workers", value=num_workers, min=1, max=100, on_value=set_num_workers)
    ShowGraph(num_workers=num_workers)

import solara
from mesa.visualization import SolaraViz
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import networkx as nx

from graph_utils import load_graphs, merge_graphs, create_subgraph_within_radius
from model import (
    SustainabilityModel,
    get_current_transport_usage_plot,
    get_co2_emissions_plot,
    get_co2_budget_plot,
    get_co2_budget_per_company_type_plot,
    DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
)
from company_agent import POSSIBLE_COMPANY_POLICIES

total_radius = 5000     # 1000m for developing, 5000m for actual simulations
company_location_radius = total_radius // 5
center = 41.1664384, -8.6016
graphs = load_graphs(center, distance_meters=total_radius)
merged_graph = merge_graphs(graphs)
companies = {
    "policy0": 3,
    "policy1": 2,
    "policy2": 1,
    "policy3": 1,
    "policy4": 1,
}
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
    "graphs": graphs,
    "merged_graph": merged_graph,
    "center_position": center,
    "company_location_radius": company_location_radius,
    "agent_home_radius": total_radius,
    "company_budget_per_employee": {
        "type": "SliderInt",
        "value": DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
        "label": "Base CO2(g) Budget Per Employee",
        "min": 500,
        "max": 5000,
        "step": 100,
    },
    "seed": 42,
}

for policy in POSSIBLE_COMPANY_POLICIES:
    model_params.update(
        {
            policy: {
                "type": "SliderInt",
                "value": companies[policy],
                "label": f"Number of companies with {policy}",
                "min": 0,
                "max": 5,
                "step": 1,
            }
        }
    )

class InterfaceSustainabilityModel(SustainabilityModel):
    def __init__(
        self,
        num_workers_per_company: int = 10,
        graphs: dict[str, nx.Graph] = None,
        merged_graph: nx.Graph = None,
        center_position: tuple[float, float] = None,
        company_location_radius: int = 1000,
        agent_home_radius: int = 5000,
        company_budget_per_employee: int = DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
        **kwargs,
    ):
        """This class is just used to make a constructor suitable for the interface sliders."""
        for policy in POSSIBLE_COMPANY_POLICIES:
            companies[policy] = kwargs.get(policy, companies[policy])
        super().__init__(
            num_workers_per_company,
            companies,
            graphs,
            merged_graph,
            center_position,
            company_location_radius,
            agent_home_radius,
            company_budget_per_employee,
        )
        self.visualization_graph = (
            self.grid.G
            if agent_home_radius <= 1000
            else create_subgraph_within_radius(
                self.grid.G, center_position, distance_meters=company_location_radius
            )
        )

model = InterfaceSustainabilityModel(
    num_workers_per_company=num_workers_per_company,
    graphs=graphs,
    merged_graph=merged_graph,
    center_position=center,
    company_location_radius=company_location_radius,
    agent_home_radius=total_radius,
    company_budget_per_employee=DEFAULT_CO2_BUDGET_PER_EMPLOYEE,
)

def convert_to_solara_figure(mpl_fig: Figure):
    solara_figure = solara.FigureMatplotlib(mpl_fig)

    # Close the matplotlib figure explicitly (otherwise unused figures would still be open)
    plt.close(mpl_fig)

    return solara_figure

def make_graph_plot(model: SustainabilityModel):
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
    return convert_to_solara_figure(fig)

def make_transport_usage_plot(model: SustainabilityModel):
    return convert_to_solara_figure(
        get_current_transport_usage_plot(model, figsize=(6, 4))
    )

def make_co2_emissions_plot(model: SustainabilityModel):
    return convert_to_solara_figure(
        get_co2_emissions_plot(model, figsize=(6, 4))
    )

def make_co2_budget_plot(model: SustainabilityModel):
    return convert_to_solara_figure(
        get_co2_budget_plot(model, figsize=(6, 4))
    )

def make_co2_budget_per_company_type_plot(model: SustainabilityModel):
    return convert_to_solara_figure(
        get_co2_budget_per_company_type_plot(model, figsize=(6, 4))
    )

@solara.component
def Page():
    solara.Title("Sustainability Model")    
    SolaraViz(
        model,
        components=[
            make_graph_plot,
            make_co2_emissions_plot,
            make_transport_usage_plot,
            make_co2_budget_per_company_type_plot,
            make_co2_budget_plot,
        ],
        model_params=model_params,
        name="Sustainability Model",
    )

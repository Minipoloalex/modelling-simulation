import osmnx as ox
import networkx as nx
import osmnx.distance as distance
import osmnx.routing as routing
import osmnx.truncate
import math
import numpy as np
from mesa.space import NetworkGrid
import random

# ox.settings.log_console = True

def load_graphs(center_point, distance=5000) -> dict[str, nx.Graph]:
    drive_graph = ox.graph_from_point(
        center_point=center_point, dist=distance, network_type="drive"
    )
    drive_graph = osmnx.truncate.largest_component(drive_graph, strongly=True)

    bike_graph = ox.graph_from_point(
        center_point=center_point, dist=distance, network_type="bike"
    )
    bike_graph = osmnx.truncate.largest_component(bike_graph, strongly=True)

    walk_graph = ox.graph_from_point(
        center_point=center_point, dist=distance, network_type="walk"
    )
    walk_graph = osmnx.truncate.largest_component(walk_graph, strongly=True)

    return {
        "drive": drive_graph,
        "bike": bike_graph,
        "walk": walk_graph,
    }


def get_closest_node(G, point) -> tuple[any, float]:
    """Get the node closest to the given point"""
    closest_node, dist = distance.nearest_nodes(
        G, X=point[1], Y=point[0], return_dist=True
    )
    return closest_node, dist


def get_shortest_path(graph: nx.Graph, source_id: int, target_id: int) -> list[int]:
    return routing.shortest_path(graph, source_id, target_id, weight="length")


def _get_total_distance(graph: nx.Graph, path: list[int]) -> float:
    total_distance = 0.0

    # Iterate over consecutive pairs in the path
    for u, v in zip(path[:-1], path[1:]):
        mn_edge = min(graph[u][v].values(), key=lambda edge: edge["length"])
        total_distance += mn_edge["length"]
    return total_distance


def get_total_distance(
    graph: nx.Graph,
    source_position: tuple[float, float],
    target_pos: tuple[float, float],
) -> tuple[float, float]:
    source_node, source_distance = get_closest_node(graph, source_position)
    target_node, target_distance = get_closest_node(graph, target_pos)
    path = get_shortest_path(graph, source_node, target_node)

    return _get_total_distance(graph, path), source_distance + target_distance

def random_position_within_radius(rng, center_position, radius):
    """
    Generate a random latitude and longitude within a specified radius from a center position.

    Parameters:
    - center_position: tuple[float, float], the center latitude and longitude (lat, lon)
    - radius: float, the radius in meters within which to generate the random position

    Returns:
    - tuple[float, float]: the random latitude and longitude
    """
    # Earth's radius in meters
    EARTH_RADIUS = 6378137

    # Convert radius from meters to degrees
    radius_in_degrees = radius / EARTH_RADIUS * (180 / math.pi)

    # Generate a random distance within the radius
    distance = rng.uniform(0, radius_in_degrees)

    # Generate a random angle
    angle = rng.uniform(0, 2 * math.pi)

    # Calculate new latitude and longitude
    delta_lat = distance * math.cos(angle)
    delta_lon = distance * math.sin(angle) / math.cos(math.radians(center_position[0]))
    
    new_lat = center_position[0] + delta_lat
    new_lon = center_position[1] + delta_lon
    
    return new_lat, new_lon



def mix_colors(color1, color2):
    """
    Mix two hex colors by adding their RGB components.
    """
    rgb1 = np.array([int(color1[i:i+2], 16) for i in (1, 3, 5)])
    rgb2 = np.array([int(color2[i:i+2], 16) for i in (1, 3, 5)])
    mixed_rgb = np.minimum(255, (rgb1 + rgb2).astype(int))
    return f"#{mixed_rgb[0]:02x}{mixed_rgb[1]:02x}{mixed_rgb[2]:02x}"


def merge_graphs(grid_names: list[str], grids: dict[str, NetworkGrid]) -> nx.MultiDiGraph:
    # Define colors for each graph
    graph_colors = ["#FF0000", "#00FF00", "#0000FF"]  # RGB

    # Initialize a merged graph
    merged_graph = nx.MultiDiGraph()

    # Step 1: Add nodes and edges to the merged graph with attributes
    for i, grid_name in enumerate(grid_names):
        color = graph_colors[i]
        graph = grids[grid_name].G

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
    return merged_graph

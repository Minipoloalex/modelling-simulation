import osmnx as ox
import networkx as nx
import osmnx.distance as distance
import osmnx.routing as routing
import osmnx.truncate as truncate
import math
import numpy as np
from mesa.space import NetworkGrid
import random
from collections import namedtuple
from osmnx.utils_geo import bbox_from_point

# ox.settings.log_console = True

def load_graphs(center_point, distance=5000) -> dict[str, nx.Graph]:
    drive_graph = ox.graph_from_point(
        center_point=center_point, dist=distance, network_type="drive"
    )
    drive_graph = truncate.largest_component(drive_graph, strongly=True)

    bike_graph = ox.graph_from_point(
        center_point=center_point, dist=distance, network_type="bike"
    )
    bike_graph = truncate.largest_component(bike_graph, strongly=True)

    walk_graph = ox.graph_from_point(
        center_point=center_point, dist=distance, network_type="walk"
    )
    walk_graph = truncate.largest_component(walk_graph, strongly=True)

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

def create_subgraph_within_radius(G: nx.MultiDiGraph, center_position, distance):
    """
    Create a subgraph with only nodes within the specified distance from the center position.
    """
    bbox = bbox_from_point(center_position, distance)
    subgraph = truncate.truncate_graph_bbox(G, bbox, truncate_by_edge=False)
    return subgraph

def convert_m_to_km(distance: float) -> float:
    return distance / 1000

def _get_path_distance(graph: nx.Graph, path: list[int]) -> float:
    total_distance = 0.0

    # Iterate over consecutive pairs in the path
    for u, v in zip(path[:-1], path[1:]):
        mn_edge = min(graph[u][v].values(), key=lambda edge: edge["length"])
        total_distance += mn_edge["length"]
    return total_distance


PathInformation = namedtuple("PathInformation", ["path", "transport_distance", "additional_distance"])

def get_path_information(
    graph: nx.Graph,
    source_position: tuple[float, float],
    target_pos: tuple[float, float],
) -> PathInformation:
    source_node, source_distance = get_closest_node(graph, source_position)
    target_node, target_distance = get_closest_node(graph, target_pos)
    path = get_shortest_path(graph, source_node, target_node)

    transport_distance = convert_m_to_km(_get_path_distance(graph, path))
    additional_distance = convert_m_to_km(source_distance + target_distance)

    return PathInformation(path, transport_distance, additional_distance)

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


def merge_graphs(graph_names: list[str], graphs: dict[str, nx.MultiDiGraph]) -> nx.MultiDiGraph:
    merged_graph = graphs[graph_names[0]].copy()
    for grid_name in graph_names[1:]:
        graph = graphs[grid_name]
        merged_graph = nx.compose(merged_graph, graph)
    return merged_graph

from .distance_graph import juet_weighted_graph
from .polyline import polypoints_db
from ..navigation_tools.fnpp import (
    calculate_distance,
    to_tuple,
)
MAX_SEARCH_DEPTH = 1000
# COORDINATE → CLOSEST GRAPH VERTEX
def _find_closest_vertex(coords):
    current_point = to_tuple(coords)
    closest_vertex = None
    shortest_distance = float("inf")
    for vertex, data in polypoints_db.items():
        try:
            vertex_point = (
                float(data["lats"]),
                float(data["longs"])
            )
        except (KeyError, TypeError, ValueError):
            continue
        distance = calculate_distance(
            current_point,
            vertex_point
        )
        if distance < shortest_distance:
            shortest_distance = distance
            closest_vertex = vertex
    return closest_vertex
# DFS SHORTEST PATH SEARCH
def extract_vertices(
    current_vertex,
    end_vertex,
    path,
    distance,
    result,
    visited=None,
):
    if visited is None:
        visited = set()
    # Safety: avoid malformed recursion
    if len(path) > MAX_SEARCH_DEPTH:
        return
    # Target reached
    if current_vertex == end_vertex:
        result[
            tuple(path)
        ] = distance
        return
    # Validate current vertex
    node_data = juet_weighted_graph.get(
        current_vertex
    )
    if not node_data:
        return
    # Explore neighbours
    connections = node_data.get(
        "connections",
        {}
    )
    for next_vertex, edge_distance in connections.items():
        # Ignore vertices which aren't actually defined
        if next_vertex not in juet_weighted_graph:
            continue
        # Prevent cycles
        if next_vertex in path:
            continue
        try:
            edge_distance = float(
                edge_distance
            )
        except (TypeError, ValueError):
            continue
        if edge_distance < 0:
            # Negative edge weights do not make sense for
            # physical road distance.
            continue
        new_path = (
            path
            + [next_vertex]
        )
        new_distance = (
            distance
            + edge_distance
        )
        extract_vertices(
            current_vertex=next_vertex,
            end_vertex=end_vertex,
            path=new_path,
            distance=new_distance,
            result=result,
            visited=visited,
        )
# FIND SHORTEST VERTEX PATH
def find_shortest_vertex_path(
    start_vertex,
    end_vertex
):
    # Basic validation
    if start_vertex is None:
        return {}
    if end_vertex is None:
        return {}
    if start_vertex not in juet_weighted_graph:
        return {}
    if end_vertex not in juet_weighted_graph:
        return {}
    # Same vertex
    if start_vertex == end_vertex:
        return {
            (start_vertex,): 0.0
        }
    # Search
    result = {}
    extract_vertices(
        current_vertex=start_vertex,
        end_vertex=end_vertex,
        path=[start_vertex],
        distance=0.0,
        result=result,
    )

    return result
# PUBLIC SHORTEST DISTANCE FUNCTION
def short_distance(
    kart_coords,
    target_coords
):
    # Resolve GPS → graph vertices
    try:
        start_vertex = _find_closest_vertex(
            kart_coords
        )
        end_vertex = _find_closest_vertex(
            target_coords
        )
    except (TypeError, ValueError):
        return {}
    # No vertex found
    if start_vertex is None:
        return {}
    if end_vertex is None:
        return {}
    # Find shortest path
    result = find_shortest_vertex_path(
        start_vertex,
        end_vertex
    )
    if not result:
        return {}
    # Select shortest complete path
    shortest_path = min(
        result,
        key=result.get
    )
    shortest_distance = result[
        shortest_path
    ]
    return {
        shortest_path: round(
            float(shortest_distance),
            2
        )
    }
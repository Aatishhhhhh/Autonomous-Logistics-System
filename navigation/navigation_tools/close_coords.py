from ..navigation_tools.fnpp import (
    calculate_distance,
    to_tuple,
)
from ..self_navigation.polyline import (
    polypoints_db,
)
SELF_ROUTING_RADIUS = 1000.0  # metres
ARRIVAL_THRESHOLD = 7.0  # metres
def _normalize_coordinates(coords):
    latitude, longitude = to_tuple(
        coords
    )
    return {
        "lats": latitude,
        "longs": longitude
    }
def close_coords(current_coords):
    try:
        current_point = to_tuple(
            current_coords
        )
    except (
        TypeError,
        ValueError
    ):
        return None
    closest_vertex = None
    shortest_distance = float("inf")
    for vertex, coordinates in (
        polypoints_db.items()
    ):
        try:
            vertex_point = (
                float(coordinates["lats"]),
                float(coordinates["longs"])
            )
        except (
            KeyError,
            TypeError,
            ValueError
        ):
            continue
        distance = calculate_distance(
            current_point,
            vertex_point
        )
        if distance < shortest_distance:
            shortest_distance = distance
            closest_vertex = vertex
    return closest_vertex
def closest_vertex_info(current_coords):
    try:
        current_point = to_tuple(
            current_coords
        )
    except (
        TypeError,
        ValueError
    ):
        return {
            "vertex": None,
            "distance_m": None
        }
    closest_vertex = None
    shortest_distance = float("inf")
    for vertex, coordinates in (
        polypoints_db.items()
    ):
        try:
            vertex_point = (
                float(coordinates["lats"]),
                float(coordinates["longs"])
            )
        except (
            KeyError,
            TypeError,
            ValueError
        ):
            continue
        distance = calculate_distance(
            current_point,
            vertex_point
        )
        if distance < shortest_distance:
            shortest_distance = distance
            closest_vertex = vertex
    if closest_vertex is None:
        return {
            "vertex": None,
            "distance_m": None
        }
    return {
        "vertex": closest_vertex,
        "distance_m": round(
            shortest_distance,
            2
        )
    }
def check_self_dependence(
    kart_coords,
    marketplace_coords
):
    try:
        kart_point = to_tuple(
            kart_coords
        )
        marketplace_point = to_tuple(
            marketplace_coords
        )
    except (
        TypeError,
        ValueError
    ):
        return 0
    distance = calculate_distance(
        kart_point,
        marketplace_point
    )
    if distance <= SELF_ROUTING_RADIUS:
        return 1
    return 0
def distance_between(
    point1,
    point2
):
    try:
        p1 = to_tuple(
            point1
        )
        p2 = to_tuple(
            point2
        )
    except (
        TypeError,
        ValueError
    ):
        return float("inf")
    return calculate_distance(
        p1,
        p2
    )
def very_close_coords(
    kart_coords,
    target_coords
):
    distance = distance_between(
        kart_coords,
        target_coords
    )
    if distance <= ARRIVAL_THRESHOLD:
        return 1
    return 0
def arrival_distance(
    kart_coords,
    target_coords
):
    distance = distance_between(
        kart_coords,
        target_coords
    )
    if distance == float("inf"):
        return None
    return round(
        distance,
        2
    )
def has_reached_destination(
    kart_coords,
    target_coords,
    threshold=ARRIVAL_THRESHOLD
):
    try:
        threshold = float(
            threshold
        )
    except (
        TypeError,
        ValueError
    ):
        threshold = ARRIVAL_THRESHOLD
    if threshold < 0:
        threshold = ARRIVAL_THRESHOLD
    distance = distance_between(
        kart_coords,
        target_coords
    )
    return distance <= threshold
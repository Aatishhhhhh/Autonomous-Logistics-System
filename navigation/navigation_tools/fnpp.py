import math
EARTH_RADIUS_METERS = 6371000.0
WAYPOINT_REACHED_RADIUS = 10.0  # meters
WAYPOINT_LOOKAHEAD = 2
def calculate_distance(point1, point2):
    if point1 is None or point2 is None:
        return float("inf")
    lat1, lon1 = point1
    lat2, lon2 = point2
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (
        math.sin(delta_lat / 2.0) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2.0) ** 2
    )
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.atan2(
        math.sqrt(a),
        math.sqrt(1.0 - a)
    )
    return EARTH_RADIUS_METERS * c
def to_tuple(coords):
    if coords is None:
        raise ValueError("Coordinates cannot be None")
    if isinstance(coords, (tuple, list)):
        if len(coords) < 2:
            raise ValueError(
                "Coordinate sequence must contain latitude and longitude"
            )
        latitude = float(coords[0])
        longitude = float(coords[1])

        return latitude, longitude
    if isinstance(coords, dict):
        if (
            "latitude" in coords
            and "longitude" in coords
        ):
            return (
                float(coords["latitude"]),
                float(coords["longitude"])
            )
        if (
            "lat" in coords
            and "lng" in coords
        ):
            return (
                float(coords["lat"]),
                float(coords["lng"])
            )
        if (
            "lats" in coords
            and "longs" in coords
        ):
            return (
                float(coords["lats"]),
                float(coords["longs"])
            )
        raise ValueError(
            "Dictionary must contain either "
            "(latitude, longitude), "
            "(lat, lng), or "
            "(lats, longs)"
        )
    if hasattr(coords, "latitude") and hasattr(coords, "longitude"):

        return (
            float(coords.latitude),
            float(coords.longitude)
        )
    raise ValueError(
        f"Unsupported coordinate type: {type(coords).__name__}"
    )
def polypoint(current_coords, points):
    """
    Find the geographically closest point from a list of route points.
    This function is retained for backward compatibility with
    older parts of the project.
    NOTE:
    For actual navigation, use get_next_waypoint().
    """
    if not points:
        return None
    current = to_tuple(current_coords)
    closest_point = None
    shortest_distance = float("inf")
    for point in points:
        try:
            route_point = to_tuple(point)
        except ValueError:
            # Ignore malformed route point
            continue
        distance = calculate_distance(
            current,
            route_point
        )
        if distance < shortest_distance:
            shortest_distance = distance
            closest_point = point
    return closest_point
def get_next_waypoint(
    current_coords,
    points,
    current_index
):
    if not points:
        return None, current_index
    try:
        current_index = int(current_index)
    except (TypeError, ValueError):
        current_index = 0
    current_index = max(0, current_index)
    if current_index >= len(points):
        return None, current_index

    current = to_tuple(current_coords)
    while current_index < len(points):
        waypoint = to_tuple(points[current_index])
        distance = calculate_distance(
            current,
            waypoint
        )
        if distance <= WAYPOINT_REACHED_RADIUS:
            current_index += 1
        else:
            break
    if current_index >= len(points):
        return None, current_index
    target_index = min(
        current_index + WAYPOINT_LOOKAHEAD,
        len(points) - 1
    )
    target_waypoint = to_tuple(
        points[target_index]
    )
    return target_waypoint, current_index
def distance_to_waypoint(
    current_coords,
    waypoint
):
    current = to_tuple(current_coords)
    target = to_tuple(waypoint)
    return calculate_distance(
        current,
        target
    )
def is_route_complete(
    current_coords,
    points,
    current_index
):
    if not points:
        return True
    try:
        current_index = int(current_index)
    except (TypeError, ValueError):
        return False
    # Already beyond final waypoint
    if current_index >= len(points):
        return True
    current = to_tuple(current_coords)
    final_point = to_tuple(
        points[-1]
    )
    distance = calculate_distance(
        current,
        final_point
    )
    return distance <= WAYPOINT_REACHED_RADIUS
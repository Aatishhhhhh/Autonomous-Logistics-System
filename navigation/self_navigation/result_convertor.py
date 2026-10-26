from .polyline import polypoints_db
def _extract_path(route_result):
    if route_result is None:
        return None
    if isinstance(route_result, dict):
        if not route_result:
            return None
        valid_paths = {}
        for path, distance in route_result.items():
            if not isinstance(
                path,
                (tuple, list)
            ):
                continue
            if len(path) == 0:
                continue
            try:
                numeric_distance = float(
                    distance
                )
            except (
                TypeError,
                ValueError
            ):
                continue
            valid_paths[
                tuple(path)
            ] = numeric_distance
        if not valid_paths:
            return None
        shortest_path = min(
            valid_paths,
            key=valid_paths.get
        )
        return shortest_path
    if isinstance(
        route_result,
        (tuple, list)
    ):
        if not route_result:
            return None
        return tuple(
            route_result
        )
    return None
def result_convertor(route_result):
    """
    Convert graph vertices into their corresponding GPS
    coordinates.
    Example input:
        (
            "A",
            "A1",
            "A2"
        )
    Example output:
        [
            {
                "point": 1,
                "latitude": 24.436623,
                "longitude": 77.158963
            },
            {
                "point": 2,
                "latitude": 24.436647,
                "longitude": 77.160325
            },
            {
                "point": 3,
                "latitude": 24.436310,
                "longitude": 77.160758
            }
        ]
    NOTE:
    This function converts GRAPH VERTICES only.
    It does NOT add intermediate road/polyline points.
    For the complete dense road route, use:
        extract_polyline()
        or
        get_route_polyline()
    """
    path = _extract_path(
        route_result
    )
    if path is None:
        return []
    points = []
    for vertex in path:
        # Vertex must exist in coordinate database
        vertex_data = polypoints_db.get(
            vertex
        )
        if vertex_data is None:
            return []
        try:
            latitude = float(
                vertex_data["lats"]
            )
            longitude = float(
                vertex_data["longs"]
            )
        except (
            KeyError,
            TypeError,
            ValueError
        ):
            return []
        points.append({
            "point": len(points) + 1,
            "latitude": latitude,
            "longitude": longitude
        })
    return points
# EXPLICIT ALIAS
def convert_path_to_points(route_result):
    return result_convertor(
        route_result
    )

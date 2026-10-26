from .polyline import get_route_polyline
# ROUTE RESULT → GPS POLYLINE
def extract_polyline(route_result):
    if route_result is None:
        return []
    if isinstance(route_result, dict):
        if not route_result:
            return []
        valid_results = {}
        for path, distance in route_result.items():
            # Path should be tuple/list of vertex names.
            if not isinstance(
                path,
                (tuple, list)
            ):
                continue
            # Need at least one vertex.
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

            valid_results[
                tuple(path)
            ] = numeric_distance

        if not valid_results:
            return []
        shortest_path = min(
            valid_results,
            key=valid_results.get
        )
        return get_route_polyline(
            shortest_path
        )
    # CASE 2:
    #DIRECT TUPLE / LIST PATH
    if isinstance(
        route_result,
        (tuple, list)
    ):
        if not route_result:
            return []
        path = tuple(
            route_result
        )

        return get_route_polyline(
            path
        )
    return []
def route_to_polyline(route_result):
    return extract_polyline(
        route_result
    )



        



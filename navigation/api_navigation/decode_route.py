
def _decode_value(encoded: str, index: int):
    result = 0
    shift = 0
    while True:
        if index >= len(encoded):
            return None, index
        byte = ord(encoded[index]) - 63
        index += 1

        if byte < 0:
            return None, index
        result |= (byte & 0x1F) << shift
        shift += 5
        if byte < 0x20:
            break
        if shift > 60:
            return None, index
    if result & 1:
        value = ~(result >> 1)
    else:
        value = result >> 1
    return value, index
def decode_polyline(encoded):
    if not isinstance(encoded, str):
        return []
    if not encoded:
        return []
    points = []
    index = 0
    latitude = 0
    longitude = 0
    while index < len(encoded):
        # Decode latitude delta.
        delta_latitude, index = _decode_value(encoded, index)
        if delta_latitude is None:
            return []
        # Decode longitude delta.
        delta_longitude, index = _decode_value(encoded, index)
        if delta_longitude is None:
            return []
        latitude += delta_latitude
        longitude += delta_longitude
        points.append(
            {
                "point": len(points) + 1,
                "latitude": latitude / 100000.0,
                "longitude": longitude / 100000.0,
            }
        )
    return points
def extract_route_points(route_response):
    if not isinstance(route_response, dict):
        return []
    routes = route_response.get("routes")
    if not isinstance(routes, list) or not routes:
        return []
    route = routes[0]
    if not isinstance(route, dict):
        return []
    polyline = route.get("polyline")
    if not isinstance(polyline, dict):
        return []
    encoded = polyline.get("encodedPolyline")
    if not isinstance(encoded, str) or not encoded:
        return []
    return decode_polyline(encoded)
# Backward-compatible alias.
route_to_points = extract_route_points
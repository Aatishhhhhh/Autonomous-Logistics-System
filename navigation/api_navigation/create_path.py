
import os
import requests
ROUTES_API_URL = (
    "https://routes.googleapis.com/"
    "directions/v2:computeRoutes"
)
REQUEST_TIMEOUT = 8.0
API_KEY = (
    os.getenv("GOOGLE_MAPS_API_KEY")
    or os.getenv("GMAPS_API_KEY")
    or ""
)
def _get_latitude_longitude(coordinates):
    if coordinates is None:
        raise ValueError(
            "Coordinates cannot be None"
        )
    if isinstance(
        coordinates,
        (tuple, list)
    ):
        if len(coordinates) < 2:
            raise ValueError(
                "Coordinate sequence must contain "
                "latitude and longitude"
            )
        return (
            float(coordinates[0]),
            float(coordinates[1])
        )
    if isinstance(
        coordinates,
        dict
    ):
        if (
            "latitude" in coordinates
            and
            "longitude" in coordinates
        ):

            return (
                float(
                    coordinates["latitude"]
                ),
                float(
                    coordinates["longitude"]
                )
            )

        if (
            "lat" in coordinates
            and
            "lng" in coordinates
        ):

            return (
                float(
                    coordinates["lat"]
                ),
                float(
                    coordinates["lng"]
                )
            )

        if (
            "lats" in coordinates
            and
            "longs" in coordinates
        ):

            return (
                float(
                    coordinates["lats"]
                ),
                float(
                    coordinates["longs"]
                )
            )

        raise ValueError(
            "Dictionary must contain one of: "
            "(latitude, longitude), "
            "(lat, lng), "
            "(lats, longs)"
        )
    if (
        hasattr(coordinates, "latitude")
        and
        hasattr(coordinates, "longitude")
    ):

        return (
            float(
                coordinates.latitude
            ),
            float(
                coordinates.longitude
            )
        )

    raise ValueError(
        f"Unsupported coordinate type: "
        f"{type(coordinates).__name__}"
    )
def coordinates_to_location(
    coordinates
):
    latitude, longitude = (
        _get_latitude_longitude(
            coordinates
        )
    )
    return {
        "location": {
            "latLng": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
    }
def _has_api_key():
    return bool(
        API_KEY
        and
        API_KEY.strip()
    )
def _build_route_request(
    origin,
    destination
):
    return {
        "origin": coordinates_to_location(
            origin
        ),

        "destination": coordinates_to_location(
            destination
        ),

        "travelMode": "DRIVE",

        # We only need the primary route.
        "computeAlternativeRoutes": False,

        # Metric distance values are useful for the robot.
        "units": "METRIC",
    }
def _build_headers():
    return {
        "Content-Type": "application/json",

        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": (
            "routes.distanceMeters,"
            "routes.duration,"
            "routes.polyline.encodedPolyline"
        ),
    }
def get_google_route(
    origin,
    destination
):
    if not _has_api_key():
        print(
            "Google Routes API key is not configured."
        )
        print(
            "Set GOOGLE_MAPS_API_KEY or GMAPS_API_KEY."
        )
        return None
    try:

        request_body = (
            _build_route_request(
                origin,
                destination
            )
        )
    except (
        TypeError,
        ValueError
    ) as error:
        print(
            f"Google route coordinate error: "
            f"{error}"
        )
        return None
    headers = _build_headers()
    try:
        response = requests.post(
            ROUTES_API_URL,
            headers=headers,
            json=request_body,
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        print(
            "Google Routes API request timed out."
        )
        return None
    except requests.exceptions.ConnectionError:
        print(
            "Could not connect to Google Routes API."
        )
        return None
    except requests.exceptions.RequestException as error:
        print(
            f"Google Routes API request error: "
            f"{error}"
        )
        return None
    print(
        "Google Status:",
        response.status_code
    )
    if response.status_code != 200:

        print(
            "Google Routes API error:"
        )
        try:
            print(
                response.text
            )

        except Exception:
            pass

        return None
    try:
        route_response = (
            response.json()
        )
    except ValueError:

        print(
            "Google returned an invalid JSON response."
        )
        return None
    if not isinstance(
        route_response,
        dict
    ):
        print(
            "Google response is not a valid JSON object."
        )
        return None
    routes = route_response.get(
        "routes"
    )
    if not isinstance(
        routes,
        list
    ):
        print(
            "Google response does not contain a valid routes list."
        )
        return None
    if len(routes) == 0:
        print(
            "Google returned no routes."
        )
        return None
    first_route = routes[0]
    if not isinstance(
        first_route,
        dict
    ):
        print(
            "Google returned an invalid route object."
        )
        return None
    polyline = first_route.get(
        "polyline"
    )
    if not isinstance(
        polyline,
        dict
    ):
        print(
            "Google route does not contain a polyline."
        )
        return None
    encoded_polyline = polyline.get(
        "encodedPolyline"
    )
    if not encoded_polyline:
        print(
            "Google route contains an empty polyline."
        )
        return None
    return route_response
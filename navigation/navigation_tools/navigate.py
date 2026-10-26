import math
from .fnpp import (
    get_next_waypoint,
    to_tuple,
    calculate_distance
)

# NAVIGATION CONFIGURATION
FORWARD_ANGLE_THRESHOLD = 10.0
SLIGHT_TURN_THRESHOLD = 30.0
def calculate_bearing(point1, point2):
    lat1, lon1 = to_tuple(point1)
    lat2, lon2 = to_tuple(point2)
    # Convert latitude to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    # Longitude difference in radians
    delta_lon = math.radians(lon2 - lon1)
    # Geographic bearing formula
    y = (
        math.sin(delta_lon)
        * math.cos(lat2_rad)
    )
    x = (
        math.cos(lat1_rad)
        * math.sin(lat2_rad)
        -
        math.sin(lat1_rad)
        * math.cos(lat2_rad)
        * math.cos(delta_lon)
    )
    bearing = math.atan2(y, x)
    # Radians -> degrees
    bearing = math.degrees(bearing)
    # Normalize to 0-360
    bearing = (bearing + 360.0) % 360.0
    return bearing
def angle_difference(desired_bearing, current_bearing):
    difference = (
        desired_bearing
        - current_bearing
    )
    difference = (
        difference + 180.0
    ) % 360.0 - 180.0

    return difference
def normalize_heading(heading):
    try:
        heading = float(heading)
    except (TypeError, ValueError):
        raise ValueError(
            "Heading must be a numeric value"
        )

    return heading % 360.0
def generate_command(angle_error):
    if abs(angle_error) <= FORWARD_ANGLE_THRESHOLD:
        return "F"
    elif (
        FORWARD_ANGLE_THRESHOLD
        < angle_error
        <= SLIGHT_TURN_THRESHOLD
    ):
        return "SR"
    elif (
        -SLIGHT_TURN_THRESHOLD
        <= angle_error
        < -FORWARD_ANGLE_THRESHOLD
    ):
        return "SL"
    elif angle_error > SLIGHT_TURN_THRESHOLD:
        return "R"
    else:
        return "L"

# MAIN NAVIGATION FUNCTION
def navigate(
    heading,
    current_coords,
    points,
    waypoint_index=0
):
    if not points:
        return {
            "command": "STOP",
            "waypoint_index": waypoint_index,
            "route_complete": True,
            "target_waypoint": None,
            "distance_to_target": 0.0,
            "desired_bearing": None,
            "angle_error": None
        }
    try:
        waypoint_index = int(waypoint_index)
    except (TypeError, ValueError):
        waypoint_index = 0
    waypoint_index = max(
        0,
        waypoint_index
    )
    heading = normalize_heading(heading)
    next_point, updated_index = get_next_waypoint(
        current_coords,
        points,
        waypoint_index
    )
    if next_point is None:
        return {
            "command": "STOP",
            "waypoint_index": updated_index,
            "route_complete": True,
            "target_waypoint": None,
            "distance_to_target": 0.0,
            "desired_bearing": None,
            "angle_error": None
        }
    desired_bearing = calculate_bearing(
        current_coords,
        next_point
    )
    angle_error = angle_difference(
        desired_bearing,
        heading
    )
    command = generate_command(
        angle_error
    )
    distance_to_target = calculate_distance(
        to_tuple(current_coords),
        to_tuple(next_point)
    )
    return {
        "command": command,
        "waypoint_index": updated_index,
        "route_complete": False,
        "target_waypoint": next_point,
        "distance_to_target": round(
            distance_to_target,
            2
        ),
        "desired_bearing": round(
            desired_bearing,
            2
        ),
        "angle_error": round(
            angle_error,
            2
        )
    }
import os
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional
# GOOGLE NAVIGATION
from .api_navigation.create_path import (
    get_google_route,
)
from .api_navigation.decode_route import (
    extract_route_points,
)
# AUTONOMOUS NAVIGATION
from .navigation_tools.navigate import (
    navigate,
)
from .navigation_tools.movement import (
    movement,
)
from .navigation_tools.fnpp import (
    calculate_distance,
    to_tuple,
)
# SELF NAVIGATION
from .self_navigation.shortest_distance import (
    short_distance,
)
from .self_navigation.polyline_extraction import (
    extract_polyline,
)
# CAMERA
from other_tools.frame_extraction import (
    get_frame,
)
# CONFIGURATION
# Destination arrival threshold
ARRIVAL_THRESHOLD = 7.0
# Waypoint route mode
GOOGLE_ROUTE = 0
SELF_ROUTE = 1
# Safe command
SAFE_STOP_COMMAND = "STOP"
# Allowed final commands
ALLOWED_COMMANDS = {
    "F",
    "SR",
    "SL",
    "R",
    "L",
    "STOP",
}
CAMERA_SOURCE = os.getenv(
    "CAMERA_SOURCE",
    "0",
)

POTHOLE_DETECTION_ENABLED = (
    os.getenv(
        "POTHOLE_DETECTION_ENABLED",
        "false",
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)
@dataclass
class PipelineState:
    route_key: Optional[tuple] = None
    route_points: list = field(
        default_factory=list
    )
    waypoint_index: int = 0
    routing_mode: Optional[int] = None
    last_command: str = SAFE_STOP_COMMAND
    last_error: Optional[str] = None
state = PipelineState()
state_lock = Lock()
def _normalize_command(
    command,
):
    if command is None:
        return SAFE_STOP_COMMAND
    command = str(
        command
    ).strip().upper()
    if command not in ALLOWED_COMMANDS:
        return SAFE_STOP_COMMAND
    return command
# ROUTE MODE NORMALIZATION
def _normalize_routing_mode(
    routing_mode,
):
    if isinstance(
        routing_mode,
        str,
    ):
        value = (
            routing_mode
            .strip()
            .lower()
        )
        if value in {
            "google",
            "0",
        }:
            return GOOGLE_ROUTE
        if value in {
            "self",
            "1",
        }:
            return SELF_ROUTE
        return None
    try:
        value = int(
            routing_mode
        )
    except (
        TypeError,
        ValueError,
    ):
        return None
    if value in {
        GOOGLE_ROUTE,
        SELF_ROUTE,
    }:
        return value
    return None
# CAMERA SOURCe
def _resolve_camera_source(
    source,
):
    if isinstance(
        source,
        str,
    ):
        value = source.strip()
        if value.isdigit():
            return int(
                value
            )
        return value
    return source
# CAMERA FRAME
def _get_camera_frame():
    source = _resolve_camera_source(
        CAMERA_SOURCE
    )
    try:
        return get_frame(
            source
        )
    except Exception:
        return None
# GOOGLE ROUTE
def _build_google_route(
    current_coords,
    target_coords,
):
    try:

        route_response = get_google_route(
            current_coords,
            target_coords,
        )
    except Exception as error:
        with state_lock:
            state.last_error = (
                f"Google route error: {error}"
            )
        return []
    if not route_response:
        with state_lock:
            state.last_error = (
                "Google route was not returned."
            )
        return []
    try:
        points = extract_route_points(
            route_response
        )
    except Exception as error:
        with state_lock:
            state.last_error = (
                f"Google polyline decode error: {error}"
            )
        return []
    if not points:
        with state_lock:
            state.last_error = (
                "Google route contained no usable points."
            )
        return []
    return points
# SELF ROUTE
def _build_self_route(
    current_coords,
    target_coords,
):
    try:
        route_result = short_distance(
            current_coords,
            target_coords,
        )
    except Exception as error:
        with state_lock:
            state.last_error = (
                f"Self route search error: {error}"
            )
        return []
    if not route_result:
        with state_lock:
            state.last_error = (
                "Self route could not be created."
            )
        return []
    try:
        points = extract_polyline(
            route_result
        )
    except Exception as error:
        with state_lock:
            state.last_error = (
                f"Self route polyline error: {error}"
            )
        return []
    if not points:
        with state_lock:
            state.last_error = (
                "Self route contained no usable points."
            )
        return []
    return points
# ROUTE BUILDER
def _build_route(
    current_coords,
    target_coords,
    routing_mode,
):
    if routing_mode == GOOGLE_ROUTE:
        return _build_google_route(
            current_coords,
            target_coords,
        )
    if routing_mode == SELF_ROUTE:
        return _build_self_route(
            current_coords,
            target_coords,
        )
    return []
def _create_route_key(
    target_coords,
    routing_mode,
):
    latitude, longitude = to_tuple(
        target_coords
    )
    return (
        round(
            latitude,
            7,
        ),
        round(
            longitude,
            7,
        ),
        int(
            routing_mode
        ),
    )
def _ensure_route(
    current_coords,
    target_coords,
    routing_mode,
):
    route_key = _create_route_key(
        target_coords,
        routing_mode,
    )
    with state_lock:
        route_already_exists = (
            state.route_key == route_key
            and bool(
                state.route_points
            )
            and state.routing_mode == routing_mode
        )
    if route_already_exists:
        return True
    route_points = _build_route(
        current_coords,
        target_coords,
        routing_mode,
    )
    if not route_points:
        with state_lock:
            state.route_key = route_key
            state.route_points = []
            state.waypoint_index = 0
            state.routing_mode = routing_mode
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return False
    with state_lock:
        state.route_key = route_key
        state.route_points = (
            route_points
        )
        state.waypoint_index = 0
        state.routing_mode = routing_mode
        state.last_error = None
        state.last_command = (
            SAFE_STOP_COMMAND
        )
    return True
def _detect_obstacle(
    frame,
):
    try:
        result = movement(
            frame
        )
    except Exception as error:

        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": "detector_error",
            "confidence": 1.0,
            "danger_score": 1.0,
            "error": str(error),
        }
    if not isinstance(
        result,
        dict,
    ):
        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": "invalid_detector_result",
            "confidence": 1.0,
            "danger_score": 1.0,
        }
    return result
def _detect_pothole(
    frame,
):
    if not POTHOLE_DETECTION_ENABLED:
        return {
            "pothole_present": False,
            "side": None,
            "command": None,
        }
    try:
        from .navigation_tools.pothole_detection import (
            detect_pothole,
        )
    except Exception as error:
        return {
            "pothole_present": True,
            "side": "CENTER",
            "command": "STOP",
            "error": (
                f"Pothole detector unavailable: {error}"
            ),
        }
    try:
        result = detect_pothole(
            frame
        )
    except Exception as error:
        return {
            "pothole_present": True,
            "side": "CENTER",
            "command": "STOP",
            "error": (
                f"Pothole detector error: {error}"
            ),
        }
    if not isinstance(
        result,
        dict,
    ):
        return {
            "pothole_present": True,
            "side": "CENTER",
            "command": "STOP",
            "error": (
                "Invalid pothole detector result."
            ),
        }
    return result
def _safety_command(
    obstacle_result,
    pothole_result,
):
    obstacle_present = bool(
        obstacle_result.get(
            "obstacle_present",
            False,
        )
    )
    pothole_present = bool(
        pothole_result.get(
            "pothole_present",
            False,
        )
    )
    if (
        not obstacle_present
        and not pothole_present
    ):
        return None
    sides = []
    if obstacle_present:
        obstacle_side = str(
            obstacle_result.get(
                "side",
                "CENTER",
            )
        ).upper()

        sides.append(
            obstacle_side
        )
    if pothole_present:
        pothole_side = str(
            pothole_result.get(
                "side",
                "CENTER",
            )
        ).upper()
        sides.append(
            pothole_side
        )
    if "CENTER" in sides:
        return SAFE_STOP_COMMAND
    unique_sides = set(
        sides
    )
    if (
        "LEFT" in unique_sides
        and
        "RIGHT" in unique_sides
    ):
        return SAFE_STOP_COMMAND
    if unique_sides == {
        "LEFT"
    }:
        return "SR"

    if unique_sides == {
        "RIGHT"
    }:
        return "SL"
    return SAFE_STOP_COMMAND
def _has_reached_target(
    current_coords,
    target_coords,
):
    try:
        current_point = to_tuple(
            current_coords
        )
        target_point = to_tuple(
            target_coords
        )
        distance = calculate_distance(
            current_point,
            target_point,
        )
    except (
        TypeError,
        ValueError,
    ):
        return False
    return (
        distance
        <= ARRIVAL_THRESHOLD
    )
def reset_pipeline():
    global state
    with state_lock:
        state = PipelineState()
def get_pipeline_state():
    with state_lock:
        return {
            "route_active": bool(
                state.route_points
            ),
            "routing_mode": (
                state.routing_mode
            ),
            "waypoint_index": (
                state.waypoint_index
            ),
            "route_points_count": len(
                state.route_points
            ),
            "last_command": (
                state.last_command
            ),
            "last_error": (
                state.last_error
            ),
        }
def pipeline(
    current_coords,
    target_coords,
    heading,
    routing_mode,
):
    try:
        to_tuple(
            current_coords
        )
    except (
        TypeError,
        ValueError,
    ) as error:
        with state_lock:
            state.last_error = (
                f"Invalid current coordinates: {error}"
            )
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    try:
        to_tuple(
            target_coords
        )
    except (
        TypeError,
        ValueError,
    ) as error:
        with state_lock:
            state.last_error = (
                f"Invalid target coordinates: {error}"
            )
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    routing_mode = _normalize_routing_mode(
        routing_mode
    )
    if routing_mode is None:
        with state_lock:
            state.last_error = (
                "Invalid routing mode."
            )
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    frame = _get_camera_frame()
    if frame is None:
        with state_lock:
            state.last_error = (
                "Camera frame unavailable."
            )
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    obstacle_result = _detect_obstacle(
        frame
    )
    pothole_result = _detect_pothole(
        frame
    )
    safety_command = _safety_command(
        obstacle_result,
        pothole_result,
    )
    if safety_command is not None:
        with state_lock:
            state.last_command = (
                safety_command
            )
            detector_error = (
                obstacle_result.get(
                    "error"
                )
                or
                pothole_result.get(
                    "error"
                )
            )
            if detector_error:

                state.last_error = (
                    str(
                        detector_error
                    )
                )
        return safety_command
    if _has_reached_target(
        current_coords,
        target_coords,
    ):
        with state_lock:
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    route_ready = _ensure_route(
        current_coords,
        target_coords,
        routing_mode,
    )
    if not route_ready:
        with state_lock:
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    with state_lock:
        route_points = list(
            state.route_points
        )

        waypoint_index = (
            state.waypoint_index
        )
    try:
        navigation_result = navigate(
            heading=heading,
            current_coords=current_coords,
            points=route_points,
            waypoint_index=waypoint_index,
        )
    except Exception as error:
        with state_lock:
            state.last_error = (
                f"Navigation error: {error}"
            )
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    new_waypoint_index = navigation_result.get(
        "waypoint_index",
        waypoint_index,
    )
    try:
        new_waypoint_index = int(
            new_waypoint_index
        )
    except (
        TypeError,
        ValueError,
    ):
        new_waypoint_index = (
            waypoint_index
        )
    route_complete = bool(
        navigation_result.get(
            "route_complete",
            False,
        )
    )
    if route_complete:
        with state_lock:
            state.waypoint_index = (
                new_waypoint_index
            )
            state.last_command = (
                SAFE_STOP_COMMAND
            )
        return SAFE_STOP_COMMAND
    command = _normalize_command(
        navigation_result.get(
            "command",
            SAFE_STOP_COMMAND,
        )
    )
    with state_lock:
        state.waypoint_index = (
            new_waypoint_index
        )
        state.last_command = command
    return command
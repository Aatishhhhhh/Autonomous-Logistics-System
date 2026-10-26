import os
from ultralytics import YOLO
MODEL_PATH = os.getenv(
    "YOLO_MODEL_PATH",
    "yolov8n.pt"
)
MIN_CONFIDENCE = 0.45
PATH_LEFT_RATIO = 0.30
PATH_RIGHT_RATIO = 0.70
SIDE_LEFT_RATIO = 0.15
SIDE_RIGHT_RATIO = 0.85
CLOSE_BOTTOM_RATIO = 0.82
CLOSE_AREA_RATIO = 0.12

# NOTE:
OBSTACLE_CLASSES = {
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "truck",
    "dog",
    "cow",
    "cat",
    "horse",
}
model = YOLO(MODEL_PATH)
def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
def _clamp(value, minimum, maximum):
    return max(
        minimum,
        min(maximum, value)
    )
def _calculate_danger_score(
    center_x,
    center_y,
    box_area,
    frame_width,
    frame_height
):
    frame_center_x = frame_width / 2.0
    horizontal_offset = abs(
        center_x - frame_center_x
    )
    max_horizontal_offset = (
        frame_width / 2.0
    )
    if max_horizontal_offset <= 0:
        centrality = 0.0
    else:
        centrality = 1.0 - (
            horizontal_offset
            / max_horizontal_offset
        )
    centrality = _clamp(
        centrality,
        0.0,
        1.0
    )
    bottom_ratio = (
        center_y
        / frame_height
    )
    bottom_proximity = _clamp(
        bottom_ratio,
        0.0,
        1.0
    )
    frame_area = (
        frame_width
        * frame_height
    )
    area_ratio = 0.0
    if frame_area > 0:
        area_ratio = (
            box_area
            / frame_area
        )
    size_score = _clamp(
        area_ratio * 5.0,
        0.0,
        1.0
    )
    danger_score = (
        0.45 * centrality
        +
        0.35 * bottom_proximity
        +
        0.20 * size_score
    )
    return _clamp(
        danger_score,
        0.0,
        1.0
    )
def _classify_position(
    center_x,
    frame_width
):
    path_left = (
        frame_width
        * PATH_LEFT_RATIO
    )
    path_right = (
        frame_width
        * PATH_RIGHT_RATIO
    )
    side_left = (
        frame_width
        * SIDE_LEFT_RATIO
    )
    side_right = (
        frame_width
        * SIDE_RIGHT_RATIO
    )
    if (
        path_left
        <= center_x
        <= path_right
    ):
        return "CENTER"
    if (
        side_left
        <= center_x
        < path_left
    ):
        return "LEFT"
    if (
        path_right
        < center_x
        <= side_right
    ):
        return "RIGHT"
    return "IGNORE"
def movement(frame):
    if frame is None:
        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": "camera_failure",
            "confidence": 1.0,
            "danger_score": 1.0,
            "bbox": None,
        }
    try:
        frame_height, frame_width = (
            frame.shape[:2]
        )
    except AttributeError:
        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": "invalid_frame",
            "confidence": 1.0,
            "danger_score": 1.0,
            "bbox": None,
        }
    if (
        frame_width <= 0
        or frame_height <= 0
    ):

        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": "invalid_frame",
            "confidence": 1.0,
            "danger_score": 1.0,
            "bbox": None,
        }
    try:
        results = model(
            frame,
            imgsz=416,
            conf=MIN_CONFIDENCE,
            verbose=False
        )
    except Exception as error:
        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": "vision_error",
            "confidence": 1.0,
            "danger_score": 1.0,
            "bbox": None,
            "error": str(error),
        }
    candidates = []
    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            try:
                confidence = float(
                    box.conf[0]
                )
            except Exception:
                continue
            if (
                confidence
                < MIN_CONFIDENCE
            ):
                continue
            try:
                class_id = int(
                    box.cls[0]
                )
                class_name = str(
                    model.names[class_id]
                ).lower().strip()
            except Exception:
                continue
            if (
                class_name
                not in OBSTACLE_CLASSES
            ):
                continue
            try:
                x1, y1, x2, y2 = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .tolist()
                )
            except Exception:
                continue
            x1 = int(
                _clamp(
                    x1,
                    0,
                    frame_width - 1
                )
            )
            y1 = int(
                _clamp(
                    y1,
                    0,
                    frame_height - 1
                )
            )
            x2 = int(
                _clamp(
                    x2,
                    0,
                    frame_width - 1
                )
            )

            y2 = int(
                _clamp(
                    y2,
                    0,
                    frame_height - 1
                )
            )

            if (
                x2 <= x1
                or y2 <= y1
            ):
                continue

            # ------------------------------------------------
            # Geometric properties
            # ------------------------------------------------

            center_x = (
                x1 + x2
            ) / 2.0

            center_y = (
                y1 + y2
            ) / 2.0

            box_width = (
                x2 - x1
            )

            box_height = (
                y2 - y1
            )

            box_area = (
                box_width
                * box_height
            )

            bottom_y = y2

            bottom_ratio = (
                bottom_y
                / frame_height
            )

            area_ratio = (
                box_area
                /
                (
                    frame_width
                    * frame_height
                )
            )
            side = _classify_position(
                center_x,
                frame_width
            )
            if side == "IGNORE":
                continue
            danger_score = (
                _calculate_danger_score(
                    center_x=center_x,
                    center_y=center_y,
                    box_area=box_area,
                    frame_width=frame_width,
                    frame_height=frame_height
                )
            )
            priority_score = (
                0.85 * danger_score
                +
                0.15 * confidence
            )
            candidates.append({
                "class_name": class_name,
                "confidence": confidence,
                "side": side,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "center_x": center_x,
                "center_y": center_y,
                "bottom_ratio": bottom_ratio,
                "area_ratio": area_ratio,
                "danger_score": danger_score,
                "priority_score": priority_score,
            })
    if not candidates:
        return {
            "obstacle_present": False,
            "side": None,
            "command": None,
            "obstacle_class": None,
            "confidence": None,
            "danger_score": 0.0,
            "bbox": None,
        }
    most_dangerous = max(
        candidates,
        key=lambda item: item[
            "priority_score"
        ]
    )
    side = most_dangerous[
        "side"
    ]
    confidence = most_dangerous[
        "confidence"
    ]
    obstacle_class = most_dangerous[
        "class_name"
    ]
    danger_score = most_dangerous[
        "danger_score"
    ]
    bottom_ratio = most_dangerous[
        "bottom_ratio"
    ]
    area_ratio = most_dangerous[
        "area_ratio"
    ]
    if side == "CENTER":
        return {
            "obstacle_present": True,
            "side": "CENTER",
            "command": "STOP",
            "obstacle_class": obstacle_class,
            "confidence": round(
                confidence,
                3
            ),
            "danger_score": round(
                danger_score,
                3
            ),
            "bbox": {
                "x1": most_dangerous["x1"],
                "y1": most_dangerous["y1"],
                "x2": most_dangerous["x2"],
                "y2": most_dangerous["y2"],
            },
            "bottom_ratio": round(
                bottom_ratio,
                3
            ),
            "area_ratio": round(
                area_ratio,
                4
            ),
        }
    if side == "LEFT":
        return {
            "obstacle_present": True,
            "side": "LEFT",
            "command": "SR",
            "obstacle_class": obstacle_class,
            "confidence": round(
                confidence,
                3
            ),
            "danger_score": round(
                danger_score,
                3
            ),
            "bbox": {
                "x1": most_dangerous["x1"],
                "y1": most_dangerous["y1"],
                "x2": most_dangerous["x2"],
                "y2": most_dangerous["y2"],
            },
            "bottom_ratio": round(
                bottom_ratio,
                3
            ),
            "area_ratio": round(
                area_ratio,
                4
            ),
        }
    if side == "RIGHT":
        return {
            "obstacle_present": True,
            "side": "RIGHT",
            "command": "SL",
            "obstacle_class": obstacle_class,
            "confidence": round(
                confidence,
                3
            ),
            "danger_score": round(
                danger_score,
                3
            ),
            "bbox": {
                "x1": most_dangerous["x1"],
                "y1": most_dangerous["y1"],
                "x2": most_dangerous["x2"],
                "y2": most_dangerous["y2"],
            },
            "bottom_ratio": round(
                bottom_ratio,
                3
            ),
            "area_ratio": round(
                area_ratio,
                4
            ),
        }

    return {
        "obstacle_present": True,
        "side": "CENTER",
        "command": "STOP",
        "obstacle_class": obstacle_class,
        "confidence": round(
            confidence,
            3
        ),
        "danger_score": round(
            danger_score,
            3
        ),
        "bbox": None,
    }
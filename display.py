"""
Display module for rendering multi-camera grid with detections.
"""

import math

import cv2
import numpy as np

from config import GRID_HEIGHT, GRID_WIDTH, GRID_WINDOW_NAME
from utils import inside_zone
from zone_manager import get_zones_for_camera


def display_loop(caps, shared_frames, last_detections, lock, employee_colors):
    """
    Displays camera feeds in a grid layout with detection overlays.

    Args:
        caps (dict): Camera capture objects.
        shared_frames (dict): Shared frames from camera threads.
        last_detections (dict): Latest detections per camera.
        lock (threading.Lock): Thread lock for synchronization.
        employee_colors (dict): Mapping of employee names to colors.
    """
    cam_list = list(caps.keys())
    num_cams = len(cam_list)

    grid_cols = math.ceil(math.sqrt(num_cams))
    grid_rows = math.ceil(num_cams / grid_cols)

    cell_w = GRID_WIDTH // grid_cols
    cell_h = GRID_HEIGHT // grid_rows

    cv2.namedWindow(GRID_WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(GRID_WINDOW_NAME, GRID_WIDTH, GRID_HEIGHT)

    while True:
        grid = np.zeros((GRID_HEIGHT, GRID_WIDTH, 3), dtype=np.uint8)

        for idx, cam in enumerate(cam_list):
            row = idx // grid_cols
            col = idx % grid_cols

            with lock:
                frame = shared_frames[cam]["frame"]
                detections = (
                    last_detections[cam].copy()
                    if cam in last_detections
                    else []
                )

            if frame is not None:
                display = frame.copy()

                # Draw detection bounding boxes
                for detection in detections:
                    x1, y1, x2, y2, name = detection

                    color = (255, 255, 255)  # Default white

                    # Check if inside zone
                    for emp_name, data in get_zones_for_camera(cam).items():
                        if inside_zone((x1, y1, x2, y2), data["zone"]):
                            color = employee_colors.get(emp_name, (0, 255, 0))
                            break

                    head_x = (x1 + x2) // 2
                    head_y = int(y1 + 0.15 * (y2 - y1))

                    cv2.rectangle(
                        display,
                        (x1, y1),
                        (x2, y2),
                        color,
                        2,
                        lineType=cv2.LINE_AA,
                    )

                    cv2.circle(display, (head_x, head_y), 5, (0, 0, 255), -1)

                # Camera label
                cam_label = f"CAM {cam}"
                (clw, clh), _ = cv2.getTextSize(
                    cam_label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    2,
                )

                cv2.rectangle(
                    display,
                    (0, 0),
                    (clw + 20, clh + 16),
                    (40, 40, 40),
                    -1,
                )

                cv2.putText(
                    display,
                    cam_label,
                    (10, clh + 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                cell = cv2.resize(display, (cell_w, cell_h))

            else:
                # No frame available
                cell = np.zeros((cell_h, cell_w, 3), dtype=np.uint8)

                cv2.putText(
                    cell,
                    f"CAM {cam} Connecting...",
                    (10, cell_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (100, 100, 100),
                    1,
                    cv2.LINE_AA,
                )

            y_start = row * cell_h
            x_start = col * cell_w

            grid[
                y_start : y_start + cell_h,
                x_start : x_start + cell_w,
            ] = cell

        # Draw grid lines
        for r in range(1, grid_rows):
            cv2.line(
                grid,
                (0, r * cell_h),
                (GRID_WIDTH, r * cell_h),
                (80, 80, 80),
                1,
            )

        for c in range(1, grid_cols):
            cv2.line(
                grid,
                (c * cell_w, 0),
                (c * cell_w, GRID_HEIGHT),
                (80, 80, 80),
                1,
            )

        cv2.imshow(GRID_WINDOW_NAME, grid)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
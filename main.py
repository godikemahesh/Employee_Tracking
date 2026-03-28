"""
Main entry point for Employee Zone Monitoring System.
"""

import math
import threading
import time
import urllib.parse

import cv2
import numpy as np

from config import *
from detector import detector
from display import display_loop
from report_manager import *
from state_manager import *
from utils import inside_zone
from zone_manager import *


def main(active_cameras):
    """
    Main function to run multi-camera monitoring.
    """
    num_cameras = len(active_cameras)

    all_report_data = load_report(REPORT_FILE)
    report_data = all_report_data[get_today_date()]

    base_frames = FRAMES_PER_CYCLE // num_cameras
    extra_frames = FRAMES_PER_CYCLE % num_cameras

    frames_per_cam = {
        cam: base_frames + (1 if i < extra_frames else 0)
        for i, cam in enumerate(active_cameras)
    }

    print("\n--- Multi-Camera Zone Monitoring (Detection Only) ---")
    print(f"Active cameras: {active_cameras}")
    print(f"Total frames per cycle: {FRAMES_PER_CYCLE}")

    for cam, nf in frames_per_cam.items():
        print(f"  Camera {cam}: {nf} frames")

    # -------- ZONES PER CAMERA --------
    cam_zones = {}

    for cam in active_cameras:
        zones = get_zones_for_camera(cam)
        cam_zones[cam] = zones

        if zones:
            print(f"  Camera {cam} employees: {', '.join(zones.keys())}")
        else:
            print(f"  Camera {cam}: No zones assigned!")

    # -------- OPEN STREAMS --------
    caps = {}
    encoded_pass = urllib.parse.quote(PASSWORD)

    for cam in active_cameras:
        rtsp_url = (
            f"rtsp://{USERNAME}:{encoded_pass}@{NVR_IP}:{RTSP_PORT}"
            f"/cam/realmonitor?channel={cam}&subtype={STREAM_TYPE}"
        )

        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            print(f"Failed to open Camera {cam}")
            continue

        caps[cam] = cap
        print(f"Camera {cam} stream opened.")

    if not caps:
        print("No cameras opened")
        return

    # -------- RESET STATES --------
    start_now = time.time()

    for name in all_employee_names:
        employee_states[name]["last_change"] = start_now
        employee_states[name]["presence_counter"] = 0
        employee_states[name]["absence_counter"] = 0

    lock = threading.Lock()

    shared_frames = {cam: {"frame": None} for cam in caps}
    last_detections = {cam: [] for cam in caps}

    running = True

    # -------- FRAME GRABBER --------
    def frame_grabber(cam, cap):
        while running:
            try:
                ret, frame = cap.read()
                if not running:
                    break

                if ret:
                    with lock:
                        shared_frames[cam]["frame"] = frame.copy()

            except Exception:
                break

    grabber_threads = []

    for cam, cap in caps.items():
        thread = threading.Thread(
            target=frame_grabber,
            args=(cam, cap),
            daemon=True,
        )
        thread.start()
        grabber_threads.append(thread)

    # -------- PROCESSOR --------
    def processor():
        nonlocal last_detections

        while running:
            start_time = time.time()

            cycle_results = {name: [] for name in all_employee_names}
            display_detections = {cam: [] for cam in caps}

            for cam in caps:
                cam_frame_count = frames_per_cam.get(cam, 0)
                this_cam_zones = cam_zones.get(cam, {})

                if not this_cam_zones or cam_frame_count == 0:
                    continue

                for frame_index in range(cam_frame_count):
                    with lock:
                        frame = shared_frames[cam]["frame"]

                    if frame is None:
                        continue

                    results = detector(frame, verbose=False)

                    current_frame_detections = []
                    detected_in_frame = set()

                    for result in results:
                        boxes = result.boxes.xyxy.cpu().numpy()
                        confs = result.boxes.conf.cpu().numpy()

                        for box, conf in zip(boxes, confs):
                            if conf < CONF_THRESHOLD:
                                continue

                            x1, y1, x2, y2 = map(int, box)

                            current_frame_detections.append(
                                (x1, y1, x2, y2, None)
                            )

                            for emp_name, data in this_cam_zones.items():
                                if inside_zone((x1, y1, x2, y2), data["zone"]):
                                    detected_in_frame.add(emp_name)

                    for emp_name in detected_in_frame:
                        cycle_results[emp_name].append(True)

                    if frame_index == cam_frame_count - 1:
                        display_detections[cam] = current_frame_detections.copy()

            # -------- STATE UPDATE --------
            for name in all_employee_names:
                employee_cams = get_cameras_for_employee(name)

                total_frames = sum(
                    frames_per_cam.get(int(c), 0)
                    for c in employee_cams
                    if int(c) in caps
                )

                threshold = max(1, total_frames // 2)

                detected = sum(cycle_results[name]) >= threshold

                update_state(name, detected, report_data)

            save_report(REPORT_FILE, all_report_data)

            with lock:
                for cam in caps:
                    last_detections[cam] = display_detections.get(cam, []).copy()

            elapsed = time.time() - start_time

            if elapsed < INTERVAL_SECONDS:
                time.sleep(INTERVAL_SECONDS - elapsed)

    threading.Thread(target=processor, daemon=True).start()

    print("Live Monitoring Started... Press Q to stop")

    display_loop(caps, shared_frames, last_detections, lock, {})

    # -------- CLEANUP --------
    current_time = time.time()

    for name, state_data in employee_states.items():
        duration = current_time - state_data["last_change"]

        if state_data["state"] == "PRESENT":
            report_data[name]["in_seat_seconds"] += duration
        else:
            report_data[name]["out_seat_seconds"] += duration

    save_report(REPORT_FILE, all_report_data)

    print("Final report saved")

    for thread in grabber_threads:
        thread.join(timeout=0.2)

    for cap in caps.values():
        try:
            cap.release()
        except Exception:
            pass

    cv2.destroyAllWindows()


# -------- ENTRY --------
if __name__ == "__main__":
    print("\n==============================")
    print("EMPLOYEE ZONE MONITORING")
    print("==============================")

    while True:
        try:
            cam_input = input("\nSelect cameras (or 0 to exit): ").strip()

            if cam_input == "0":
                break

            active_cameras = [
                int(c.strip()) for c in cam_input.split(",")
            ]

            active_cameras = [
                c for c in active_cameras if 1 <= c <= MAX_CAMERAS
            ]

            if not active_cameras:
                print("Invalid cameras")
                continue

            active_cameras = list(dict.fromkeys(active_cameras))

            main(active_cameras)

        except Exception as error:
            print(f"Error: {error}")
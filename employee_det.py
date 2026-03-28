import cv2
import numpy as np
import json
import threading
from ultralytics import YOLO
import urllib.parse
import time
from datetime import datetime
import os
import math

# -------- SETTINGS --------
ZONE_FILE = "zones.json"
REPORT_FILE = "report1.json"

INTERVAL_SECONDS = 5
FRAMES_PER_CYCLE = 10

MIN_BREAK_SECONDS = 30
CONF_THRESHOLD = 0.4

USERNAME = "admin1"
PASSWORD = "admin@123"
NVR_IP = "192.168.88.2"
RTSP_PORT = 554
STREAM_TYPE = 0
MAX_CAMERAS = 8

# -------- LOAD ZONES --------
with open(ZONE_FILE, "r") as f:
    zones = json.load(f)

all_employee_names = list(zones.keys())

# -------- EMPLOYEE STATES --------
employee_states = {}
for name in all_employee_names:
    employee_states[name] = {
        "state": "ABSENT",
        "last_change": time.time(),
        "presence_counter": 0,
        "absence_counter": 0
    }

today_date = datetime.now().strftime("%d-%m-%Y")

# -------- LOAD EXISTING REPORT --------
if os.path.exists(REPORT_FILE):
    with open(REPORT_FILE, "r") as f:
        try:
            all_report_data = json.load(f)
        except:
            all_report_data = {}
else:
    all_report_data = {}

# Migrate old format if needed
if "date" in all_report_data and "employees" in all_report_data:
    old_date = all_report_data["date"]
    all_report_data = {old_date: all_report_data["employees"]}
    print(f"Migrated old report format for date {old_date}.")

# Create today entry if not exists
if today_date not in all_report_data:
    all_report_data[today_date] = {}

# -------- EMPLOYEE COLORS --------
np.random.seed(42)
employee_colors = {}
for name in all_employee_names:
    employee_colors[name] = tuple(np.random.randint(50, 255, 3).tolist())

# Initialize employees for today
for name in all_employee_names:
    if name not in all_report_data[today_date]:
        all_report_data[today_date][name] = {
            "in_seat_seconds": 0,
            "out_seat_seconds": 0,
            "total_breaks": 0,
            "current_state": "ABSENT"
        }
    elif "in_seat_seconds" not in all_report_data[today_date][name]:
        all_report_data[today_date][name] = {
            "in_seat_seconds": 0,
            "out_seat_seconds": 0,
            "total_breaks": all_report_data[today_date][name].get("total_breaks", 0),
            "current_state": all_report_data[today_date][name].get("current_state", "ABSENT")
        }

# Shortcut reference to today's data
report_data = all_report_data[today_date]

# -------- MODEL --------
print("Loading YOLO model...")
detector = YOLO(r"C:\Users\valkontek 010\Downloads\new_crowd_ofc_head.pt")
print("Model loaded")

# -------- HELPER FUNCTIONS --------
def inside_zone(box, zone):
    x1, y1, x2, y2 = box
    zx1, zy1, zx2, zy2 = zone

    # Center (middle) point of bounding box
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    return zx1 < center_x < zx2 and zy1 < center_y < zy2


def get_zones_for_camera(cam_number):
    cam_key = str(cam_number)
    cam_zones = {}
    for name, data in zones.items():
        if "cameras" in data and cam_key in data["cameras"]:
            cam_zones[name] = data["cameras"][cam_key]
    return cam_zones


def get_cameras_for_employee(name):
    if name not in zones or "cameras" not in zones[name]:
        return []
    return list(zones[name]["cameras"].keys())


def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def format_time_hhmm(seconds):
    """Format seconds as HH:MM for on-screen display."""
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def update_state(name, detected):
    state_data = employee_states[name]
    current_time = time.time()

    if detected:
        state_data["presence_counter"] += 1
        state_data["absence_counter"] = 0

        if state_data["presence_counter"] >= 2 and state_data["state"] == "ABSENT":
            duration = current_time - state_data["last_change"]

            report_data[name]["out_seat_seconds"] += duration
            report_data[name]["current_state"] = "PRESENT"

            if duration > MIN_BREAK_SECONDS:
                report_data[name]["total_breaks"] += 1
                print(f"{name} CONFIRMED PRESENT (break counted: {int(duration)}s)")
            else:
                print(f"{name} CONFIRMED PRESENT (brief absence ignored: {int(duration)}s)")

            state_data["state"] = "PRESENT"
            state_data["last_change"] = current_time

    else:
        state_data["absence_counter"] += 1
        state_data["presence_counter"] = 0

        if state_data["absence_counter"] >= 2 and state_data["state"] == "PRESENT":
            duration = current_time - state_data["last_change"]

            report_data[name]["in_seat_seconds"] += duration
            report_data[name]["current_state"] = "ABSENT"

            state_data["state"] = "ABSENT"
            state_data["last_change"] = current_time

            print(f"{name} CONFIRMED ABSENT")


def save_report_with_live_time():
    """Save report with live running time included (not just state-change snapshots)."""
    with open("time.json", "w") as f:
        f.write(datetime.now().strftime("%H:%M:%S"))

    current_time = time.time()

    for name, state_data in employee_states.items():
        ongoing_duration = current_time - state_data["last_change"]

        if state_data["state"] == "PRESENT":
            report_data[name]["current_state"] = "PRESENT"
            report_data[name]["_live_in_seat"] = report_data[name]["in_seat_seconds"] + ongoing_duration
            report_data[name]["_live_out_seat"] = report_data[name]["out_seat_seconds"]
        else:
            report_data[name]["current_state"] = "ABSENT"
            report_data[name]["_live_in_seat"] = report_data[name]["in_seat_seconds"]
            report_data[name]["_live_out_seat"] = report_data[name]["out_seat_seconds"] + ongoing_duration

    # Save with live times
    save_data = {}
    for date_key, employees in all_report_data.items():
        save_data[date_key] = {}
        for name, data in employees.items():
            if "in_seat_seconds" in data:
                in_secs = data.get("_live_in_seat", data["in_seat_seconds"])
                out_secs = data.get("_live_out_seat", data["out_seat_seconds"])
                save_data[date_key][name] = {
                    "in_seat_seconds": in_secs,
                    "out_seat_seconds": out_secs,
                    "in_seat_time": format_time(in_secs),
                    "out_seat_time": format_time(out_secs),
                    "total_breaks": data["total_breaks"],
                    "current_state": data["current_state"]
                }
            else:
                save_data[date_key][name] = data

    with open(REPORT_FILE, "w") as f:
        json.dump(save_data, f, indent=4)

    # Clean up temp keys
    for name in all_employee_names:
        report_data[name].pop("_live_in_seat", None)
        report_data[name].pop("_live_out_seat", None)


def save_report():
    save_data = {}
    for date_key, employees in all_report_data.items():
        save_data[date_key] = {}
        for name, data in employees.items():
            if "in_seat_seconds" in data:
                save_data[date_key][name] = {
                    "in_seat_seconds": data["in_seat_seconds"],
                    "out_seat_seconds": data["out_seat_seconds"],
                    "in_seat_time": format_time(data["in_seat_seconds"]),
                    "out_seat_time": format_time(data["out_seat_seconds"]),
                    "total_breaks": data["total_breaks"],
                    "current_state": data["current_state"]
                }
            else:
                save_data[date_key][name] = data

    with open(REPORT_FILE, "w") as f:
        json.dump(save_data, f, indent=4)


def get_live_time_for_employee(name):
    """Get the live running time string and state for an employee."""
    state_data = employee_states[name]
    current_time = time.time()
    ongoing_duration = current_time - state_data["last_change"]

    if state_data["state"] == "PRESENT":
        live_secs = report_data[name]["in_seat_seconds"] + ongoing_duration
        return "PRESENT", format_time_hhmm(live_secs)
    else:
        live_secs = report_data[name]["out_seat_seconds"] + ongoing_duration
        return "ABSENT", format_time_hhmm(live_secs)


def draw_existing_zones(frame, cam_number):
    """Draw zones with live time display — green for PRESENT, red for ABSENT."""
    cam_key = str(cam_number)
    for name, data in zones.items():
        if "cameras" in data and cam_key in data["cameras"]:
            x1, y1, x2, y2 = data["cameras"][cam_key]["zone"]

            state, time_str = get_live_time_for_employee(name)

            if state == "PRESENT":
                zone_color = (0, 220, 100)       # green
                status_label = f"IN {time_str}"
            else:
                zone_color = (0, 80, 255)        # red-orange
                status_label = f"OUT {time_str}"

            # Zone rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), zone_color, 2, lineType=cv2.LINE_AA)

            # Name on the left above zone
            cv2.putText(frame, name, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 1, cv2.LINE_AA)

            # Time on the right above zone
            (tw, _), _ = cv2.getTextSize(status_label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.putText(frame, status_label, (x2 - tw, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 1, cv2.LINE_AA)


# -------- GRID SETTINGS --------
GRID_WINDOW_NAME = "Employee Zone Monitor"
GRID_WIDTH = 1280
GRID_HEIGHT = 720


# -------- MULTI-CAMERA MAIN --------
def main(active_cameras):
    num_cameras = len(active_cameras)

    base_frames = FRAMES_PER_CYCLE // num_cameras
    extra_frames = FRAMES_PER_CYCLE % num_cameras

    frames_per_cam = {}
    for i, cam in enumerate(active_cameras):
        frames_per_cam[cam] = base_frames + (1 if i < extra_frames else 0)

    print(f"\n--- Multi-Camera Zone Monitoring (Detection Only) ---")
    print(f"Active cameras: {active_cameras}")
    print(f"Total frames per cycle: {FRAMES_PER_CYCLE}")
    for cam, nf in frames_per_cam.items():
        print(f"  Camera {cam}: {nf} frames")

    # Build per-camera zone maps
    cam_zones = {}
    for cam in active_cameras:
        cz = get_zones_for_camera(cam)
        cam_zones[cam] = cz
        if cz:
            print(f"  Camera {cam} employees: {', '.join(cz.keys())}")
        else:
            print(f"  Camera {cam}: No zones assigned!")

    # Open all camera streams
    caps = {}
    encoded_pass = urllib.parse.quote(PASSWORD)
    for cam in active_cameras:
        rtsp_url = (
            f"rtsp://{USERNAME}:{encoded_pass}@{NVR_IP}:{RTSP_PORT}"
            f"/cam/realmonitor?channel={cam}&subtype={STREAM_TYPE}"
        )
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            print(f"Failed to open Camera {cam}. Skipping.")
            continue
        caps[cam] = cap
        print(f"Camera {cam} stream opened.")

    if not caps:
        print("No cameras could be opened.")
        return

    # Reset timers to NOW (not program start time)
    start_now = time.time()
    for name in all_employee_names:
        employee_states[name]["last_change"] = start_now
        employee_states[name]["presence_counter"] = 0
        employee_states[name]["absence_counter"] = 0

    lock = threading.Lock()
    shared_frames = {cam: {"frame": None} for cam in caps.keys()}
    last_detections = {cam: [] for cam in caps.keys()}
    running = True

    # -------- FRAME GRABBERS (one per camera) --------
    def frame_grabber(cam, cap):
        while running:
            try:
                ret, frame = cap.read()
                if not running:
                    break
                if ret:
                    with lock:
                        shared_frames[cam]["frame"] = frame.copy()
            except cv2.error:
                break
            except Exception:
                break

    grabber_threads = []
    for cam, cap in caps.items():
        t = threading.Thread(target=frame_grabber, args=(cam, cap), daemon=True)
        t.start()
        grabber_threads.append(t)

    # -------- PROCESSOR THREAD (detection + state update) --------
    def processor():
        nonlocal last_detections

        while running:
            start_time = time.time()

            cycle_results = {name: [] for name in all_employee_names}
            display_detections = {cam: {} for cam in caps.keys()}

            for cam in caps.keys():
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

                            # Store ALL detections
                            current_frame_detections.append((x1, y1, x2, y2, None))

                            # Check zones
                            for emp_name, data in this_cam_zones.items():
                                if inside_zone((x1, y1, x2, y2), data["zone"]):
                                    detected_in_frame.add(emp_name)

                    # AFTER all boxes
                    for emp_name in detected_in_frame:
                        cycle_results[emp_name].append(True)
                    # Keep last frame detections for display
                    if frame_index == cam_frame_count - 1:
                        display_detections[cam] = current_frame_detections.copy()

            # Update state using voting (same as live_monitor)
            for name in all_employee_names:
                employee_cams = get_cameras_for_employee(name)
                total_frames_for_employee = sum(
                    frames_per_cam.get(int(c), 0) for c in employee_cams if int(c) in caps
                )
                threshold = max(1, total_frames_for_employee // 2)
                detected = sum(cycle_results[name]) >= threshold
                update_state(name, detected)

            save_report_with_live_time()

            # Update display detections
            with lock:
                for cam in caps.keys():
                    last_detections[cam] = display_detections.get(cam, []).copy()

            elapsed = time.time() - start_time
            if elapsed < INTERVAL_SECONDS:
                time.sleep(INTERVAL_SECONDS - elapsed)

    threading.Thread(target=processor, daemon=True).start()

    print("\nLive Monitoring Started... Press Q to stop")

    # -------- GRID LAYOUT CALCULATION --------
    cam_list = list(caps.keys())
    n = len(cam_list)
    grid_cols = math.ceil(math.sqrt(n))
    grid_rows = math.ceil(n / grid_cols)
    cell_w = GRID_WIDTH // grid_cols
    cell_h = GRID_HEIGHT // grid_rows

    cv2.namedWindow(GRID_WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(GRID_WINDOW_NAME, GRID_WIDTH, GRID_HEIGHT)

    # -------- DISPLAY LOOP (main thread — lag-free) --------
    while True:
        grid = np.zeros((GRID_HEIGHT, GRID_WIDTH, 3), dtype=np.uint8)

        for idx, cam in enumerate(cam_list):
            row = idx // grid_cols
            col = idx % grid_cols

            with lock:
                frame = shared_frames[cam]["frame"]
                detections = last_detections[cam].copy() if cam in last_detections else []

            if frame is not None:
                display = frame.copy()

                # Draw detection bounding boxes only (no names)
                for detection in detections:
                    x1, y1, x2, y2, name = detection

                    # White for all detections
                    color = (255, 255, 255)

                    # If inside any zone → color it
                    for emp_name, data in get_zones_for_camera(cam).items():
                        if inside_zone((x1, y1, x2, y2), data["zone"]):
                            color = employee_colors.get(emp_name, (0, 255, 0))
                            break

                    head_x = (x1 + x2) // 2
                    head_y = int(y1 + 0.15 * (y2 - y1))

                    cv2.rectangle(display, (x1, y1), (x2, y2), color, 2, lineType=cv2.LINE_AA)
                    cv2.circle(display, (head_x, head_y), 5, (0, 0, 255), -1)

                # Draw zones with live time + camera label
                #draw_existing_zones(display, cam)

                # Camera label badge (top-left)
                cam_label = f"CAM {cam}"
                (clw, clh), _ = cv2.getTextSize(cam_label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(display, (0, 0), (clw + 20, clh + 16), (40, 40, 40), -1)
                cv2.putText(display, cam_label, (10, clh + 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

                # Resize to grid cell and place
                cell = cv2.resize(display, (cell_w, cell_h))
            else:
                # Black cell with "Connecting..." text
                cell = np.zeros((cell_h, cell_w, 3), dtype=np.uint8)
                cv2.putText(cell, f"CAM {cam} Connecting...", (10, cell_h // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1, cv2.LINE_AA)

            y_start = row * cell_h
            x_start = col * cell_w
            grid[y_start:y_start + cell_h, x_start:x_start + cell_w] = cell

        # Draw grid lines for separation
        for r in range(1, grid_rows):
            cv2.line(grid, (0, r * cell_h), (GRID_WIDTH, r * cell_h), (80, 80, 80), 1)
        for c in range(1, grid_cols):
            cv2.line(grid, (c * cell_w, 0), (c * cell_w, GRID_HEIGHT), (80, 80, 80), 1)

        cv2.imshow(GRID_WINDOW_NAME, grid)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # -------- CLEANUP --------
    # Flush final durations into raw seconds
    current_time = time.time()

    for name, state_data in employee_states.items():
        duration = current_time - state_data["last_change"]

        if state_data["state"] == "PRESENT":
            report_data[name]["in_seat_seconds"] += duration
        else:
            report_data[name]["out_seat_seconds"] += duration

        state_data["last_change"] = current_time

    save_report()
    print("Final report saved.")

    running = False

    # Wait for grabber threads to exit gracefully
    for t in grabber_threads:
        t.join(timeout=0.2)

    for cap in caps.values():
        try:
            cap.release()
        except:
            pass
    cv2.destroyAllWindows()


# -------- CAMERA SELECT --------
if __name__ == "__main__":
    print(f"\n{'='*55}")
    print("  EMPLOYEE ZONE MONITORING (Detection Only)")
    print(f"{'='*55}")

    # Show which cameras have zones
    print("\nZone assignments:")
    for name, data in zones.items():
        if "cameras" in data:
            cams = list(data["cameras"].keys())
            print(f"  {name}: Camera(s) {', '.join(cams)}")

    print(f"\nEnter camera numbers to monitor (1-{MAX_CAMERAS})")
    print("Examples: '1' for single camera, '1,5' for cameras 1 and 5")

    while True:
        try:
            cam_input = input("\nSelect cameras (comma-separated) or 0 to exit: ").strip()

            if cam_input == "0":
                break

            active_cameras = [int(c.strip()) for c in cam_input.split(",")]
            active_cameras = [c for c in active_cameras if 1 <= c <= MAX_CAMERAS]

            if not active_cameras:
                print("No valid cameras selected. Try again.")
                continue

            # Deduplicate while preserving order
            seen = set()
            unique_cameras = []
            for c in active_cameras:
                if c not in seen:
                    seen.add(c)
                    unique_cameras.append(c)
            active_cameras = unique_cameras

            main(active_cameras)

        except Exception as e:
            print(f"Error: {e}")
            continue
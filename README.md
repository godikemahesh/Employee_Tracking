

---

# 🚀 Employee Zone Monitoring System

## 🎯 Multi-Camera AI-Based Presence Tracking & Reporting System

---

## 📌 1. Overview

The **Employee Zone Monitoring System** is an AI-powered solution designed to monitor employee presence across multiple CCTV cameras using computer vision.

It detects human presence in predefined zones and tracks:

* ⏱️ Time spent in seat (working time)
* 🚶 Time spent out of seat (break time)
* 🔢 Number of breaks
* 📊 Real-time presence status

### 💡 Use Cases

* Offices
* Factories
* Work discipline monitoring
* Productivity reporting

---

## 🎯 2. Objective

The goal of this system is to:

* ✅ Automatically detect employee presence using AI
* 📡 Track real-time and historical attendance behavior
* ❌ Eliminate manual monitoring
* 📈 Provide accurate reports for management

---

## 🛠️ 3. Technologies Used

### 🔧 Core Technologies

* **Python** → Main programming language
* **OpenCV (cv2)** → Video processing
* **NumPy** → Numerical operations
* **Ultralytics YOLO** → Object detection

### 🤖 AI Model

* Custom YOLO model:

  ```
  croed_ofc_head_det.pt
  ```
* Used for head/person detection

### 🌐 Networking

* RTSP Stream:

  ```
  rtsp://username:password@IP:port
  ```
* Fetches CCTV feeds from NVR

### 📂 Data Handling

* `ozones.json` → Zone configuration
* `oreport1.json` → Employee report

---

## 🏗️ 4. System Architecture

```
CCTV Cameras → RTSP Stream → Frame Grabber Threads
         ↓
    YOLO Detection
         ↓
   Zone Mapping Logic
         ↓
  Presence Decision Engine
         ↓
  State Tracking System
         ↓
   Report Generator (JSON)
         ↓
   Live Monitoring Display (Grid UI)
```

---

## ⚙️ 5. Methodology

### 🔹 Step 1: Zone Definition

Each employee is assigned a fixed rectangular zone in camera view.

Stored in `zones.json`:

```json
{
  "Employee1": {
    "cameras": {
      "1": { "zone": [x1, y1, x2, y2] }
    }
  }
}
```

---

### 🔹 Step 2: Frame Capture (Multi-threading)

* Each camera runs a separate thread
* Continuously captures frames from RTSP

✅ Benefits:

* No lag
* Parallel processing

---

### 🔹 Step 3: Object Detection (YOLO)

```python
results = detector(frame)
```

Detects:

* Bounding boxes `(x1, y1, x2, y2)`
* Confidence score

Only valid detections:

```python
CONF_THRESHOLD = 0.4  # or 0.5
```

---

### 🔹 Step 4: Zone Checking Logic

```python
inside_zone(box, zone)
```

Logic:

* Find center of bounding box
* Check if inside zone

✔️ Inside → Detected
❌ Outside → Ignored

---

### 🔹 Step 5: Voting-Based Detection (Important)

Instead of trusting a single frame:

* Process multiple frames per cycle
* Use majority voting

```python
detected = sum(results) >= threshold
```

💡 Why?

* Avoid false detection
* Improve reliability

---

### 🔹 Step 6: State Management System

```json
{
  "state": "PRESENT" or "ABSENT",
  "last_change": timestamp,
  "presence_counter": int,
  "absence_counter": int
}
```

---

### 🔹 Step 7: Smart Transition Logic

```python
update_state(name, detected)
```

Rules:

* 2 consecutive detections → PRESENT
* 2 consecutive misses → ABSENT

🎯 Prevents flickering

---

### 🔹 Step 8: Time Tracking Logic

* ABSENT → PRESENT → add to `out_seat_seconds`
* PRESENT → ABSENT → add to `in_seat_seconds`

---

### 🔹 Step 9: Break Detection Logic

```python
if duration > MIN_BREAK_SECONDS:
    total_breaks += 1
```

✔️ Only meaningful breaks (>30 sec)

---

### 🔹 Step 10: Live Time Calculation

Real-time tracking:

* `_live_in_seat`
* `_live_out_seat`

Displayed instantly without waiting

---

### 🔹 Step 11: Report Generation

Stored in `report1.json`

```json
{
  "23-03-2026": {
    "Employee1": {
      "in_seat_seconds": 3600,
      "out_seat_seconds": 600,
      "in_seat_time": "1h 0m",
      "out_seat_time": "0h 10m",
      "total_breaks": 2,
      "current_state": "PRESENT"
    }
  }
}
```

---

### 🔹 Step 12: Live Monitoring UI

* Multi-camera grid layout
* Each camera in a cell

Displays:

* Bounding boxes
* Camera label
* Detection highlights

Grid auto-adjust:

```python
grid_cols = sqrt(n)
grid_rows = ceil(n / cols)
```

---

## 🧪 6. Development Process

### Phase 1: Basic Detection

* YOLO detection
* Bounding box validation

### Phase 2: Zone Mapping

* Employee zones
* Detection mapping

### Phase 3: State Tracking

* Presence/absence logic
* Counters

### Phase 4: Multi-Camera Support

* RTSP streaming
* Grid visualization

### Phase 5: Reporting System

* JSON storage
* Live updates

### Phase 6: Optimization

* Threading
* Voting mechanism
* Performance tuning

---

## ⚡ 7. Multi-threading Design

### Threads Used

1. **Frame Grabber Threads**

   * One per camera
   * Continuous frame capture

2. **Processor Thread**

   * Runs detection
   * Updates states
   * Saves reports

3. **Main Thread**

   * Displays UI

🚀 Result: High-performance system

---

## ⚙️ 8. Configuration Parameters

| Parameter         | Purpose              |
| ----------------- | -------------------- |
| CONF_THRESHOLD    | Detection confidence |
| MIN_BREAK_SECONDS | Break threshold      |
| FRAMES_PER_CYCLE  | Frames for voting    |
| INTERVAL_SECONDS  | Processing interval  |
| MAX_CAMERAS       | Max camera support   |

---

## 🌟 Final Note

This system provides a **scalable, intelligent, and real-time employee monitoring solution** using AI and multi-camera processing — ideal for modern workplaces aiming for automation and productivity insights.



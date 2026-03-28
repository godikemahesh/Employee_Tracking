&#x20;Employee Zone Monitoring System



An AI-powered multi-camera employee monitoring system that tracks presence, absence, working time, and breaks using computer vision.



&#x20;Overview



This project uses YOLO-based object detection to monitor employees across CCTV cameras. Each employee is assigned a predefined zone, and the system detects whether they are present inside their zone.



It generates real-time insights such as:



&#x20;In-seat time

&#x20;out-of-seat time

&#x20;Break count

&#x20;Live employee status

&#x20;Features

&#x20;Multi-camera support (RTSP streams)

&#x20;Zone-based employee tracking

&#x20;AI-powered detection using YOLO

&#x20;Smart presence detection (reduces false positives)

&#x20;Break detection logic

&#x20;Real-time monitoring dashboard (OpenCV grid)

&#x20;JSON-based reporting system

&#x20;Live time tracking



&#x20;**How It Works**

Camera Streams Input

Connects to CCTV cameras via RTSP

project\_root/

├── main.py

├── zones.json

├── report1.json

├── croed\_ofc\_head\_det.pt

├── time.json

├── config.py

├── detector.py

├── display.py

├── draw\_desk.py

├── report.py

├── report\_manager.py

├── state\_manager.py

├── utils.py

├── zone\_manager.py

├── crowd\_head\_detection.pt

├── person\_detection.pt

└── requirements.txt

YOLO model detects human heads

**Zone Mapping**

Each employee has a predefined zone

Detection inside zone → employee present

**State Tracking**

Uses voting mechanism across frames

Avoids flickering detection

Time Calculation

**Tracks:**

In-seat duration

Out-seat duration

**Breaks**

**Reporting**

**Stores data in JSON format**

**Updates in real-time**



&#x20;**Project Structure**

**'''**

project\_root/

├── main.py

├── zones.json

├── report1.json

├── croed\_ofc\_head\_det.pt

├── time.json

├── config.py

├── detector.py

├── display.py

├── draw\_desk.py

├── employee\_det.py

├── report.py

├── report\_manager.py

├── state\_manager.py

├── utils.py

├── zone\_manager.py

├── crowd\_head\_detection.pt

├── person\_detection.pt

└── requirements.txt

'''

Install dependencies:



'''

pip install -r requirements.txt



'''



🔧 Configuration

1\. Camera Settings



Edit in code:

'''

USERNAME =

PASSWORD = 

NVR\_IP = 

RTSP\_PORT =

'''



2\. Zones Configuration (zones.json)



Example:

'''

{

&#x20; "Employee1": {

&#x20;   "cameras": {

&#x20;     "1": {

&#x20;       "zone": \[100, 100, 300, 300]

&#x20;     }

&#x20;   }

&#x20; }

}

'''



3\. Parameters

INTERVAL\_SECONDS = 5

FRAMES\_PER\_CYCLE = 10

MIN\_BREAK\_SECONDS = 30

CONF\_THRESHOLD = 0.4





**Usage**



Run the program:



'''python main.py'''



Then select cameras:



Enter camera numbers (e.g., 1 or 1,2,3)



Press Q to stop.



**Output**



Report File (report1.json)

{

&#x20; "date": {

&#x20;   "Employee1": {

&#x20;     "in\_seat\_time": "2h 30m",

&#x20;     "out\_seat\_time": "1h 10m",

&#x20;     "total\_breaks": 3,

&#x20;     "current\_state": "PRESENT"

&#x20;   }

&#x20; }

}





&#x20;**System Design**

Threads Used

> Frame Grabber Thread (per camera)

>Processor Thread (AI + logic)

> Main Thread (display)

> Key Concepts

Zone Detection: Uses bounding box center

Voting Mechanism: Multiple frames → stable decision

Break Logic: Ignores short absence (< 30s)

Live Time Tracking: Updates continuously



&#x20;**Tech Stack**

Python 

OpenCV 

YOLO (Ultralytics) 

NumPy 

JSON 

Multithreading 


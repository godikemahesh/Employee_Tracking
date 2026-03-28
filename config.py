"""
Configuration settings for Employee Zone Monitoring System.
"""

# File paths
ZONE_FILE = "zones.json"
REPORT_FILE = "report1.json"

# Processing settings
INTERVAL_SECONDS = 5
FRAMES_PER_CYCLE = 10

# Detection settings
MIN_BREAK_SECONDS = 30
CONF_THRESHOLD = 0.3

# NVR (Network Video Recorder) credentials
USERNAME = "admin1"
PASSWORD = "admin@123"
NVR_IP = "192.168.88.2"
RTSP_PORT = 554
STREAM_TYPE = 0
MAX_CAMERAS = 8

# Display settings
GRID_WINDOW_NAME = "Employee Zone Monitor"
GRID_WIDTH = 1280
GRID_HEIGHT = 720
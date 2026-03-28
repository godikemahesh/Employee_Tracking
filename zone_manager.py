"""
Zone management module for handling employee zone configurations.
"""

import json

from config import ZONE_FILE


def load_zones(zone_file):
    """
    Loads zone configuration from JSON file.

    Args:
        zone_file (str): Path to the zone configuration file.

    Returns:
        dict: Zone data.
    """
    with open(zone_file, "r") as file:
        return json.load(file)


# Load zones once at startup
zones = load_zones(ZONE_FILE)

# Extract all employee names
all_employee_names = list(zones.keys())


def get_zones_for_camera(cam_number):
    """
    Returns zones for a specific camera.

    Args:
        cam_number (int or str): Camera ID.

    Returns:
        dict: Mapping of employee names to their zone data.
    """
    cam_key = str(cam_number)
    cam_zones = {}

    for name, data in zones.items():
        if "cameras" in data and cam_key in data["cameras"]:
            cam_zones[name] = data["cameras"][cam_key]

    return cam_zones


def get_cameras_for_employee(name):
    """
    Returns list of cameras assigned to an employee.

    Args:
        name (str): Employee name.

    Returns:
        list: Camera IDs.
    """
    if name not in zones or "cameras" not in zones[name]:
        return []

    return list(zones[name]["cameras"].keys())
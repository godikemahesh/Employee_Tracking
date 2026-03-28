"""
Report management module for handling employee activity data.
"""

import json
import os
from datetime import datetime

from zone_manager import all_employee_names


def get_today_date():
    """Returns today's date in DD-MM-YYYY format."""
    return datetime.now().strftime("%d-%m-%Y")


def load_report(report_file):
    """
    Loads report data from JSON file and initializes today's structure.

    Args:
        report_file (str): Path to the report JSON file.

    Returns:
        dict: Report data.
    """
    if os.path.exists(report_file):
        with open(report_file, "r") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    today_date = get_today_date()

    # Create today's entry if not exists
    if today_date not in data:
        data[today_date] = {}

    # Initialize employees
    for name in all_employee_names:
        if name not in data[today_date]:
            data[today_date][name] = {
                "in_seat_seconds": 0,
                "out_seat_seconds": 0,
                "total_breaks": 0,
                "current_state": "ABSENT",
            }

    return data


def save_report(report_file, all_report_data):
    """
    Saves report data to JSON file.

    Args:
        report_file (str): Path to the report JSON file.
        all_report_data (dict): Report data to save.
    """
    with open(report_file, "w") as file:
        json.dump(all_report_data, file, indent=4)
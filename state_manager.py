"""
State management module for tracking employee presence and absence.
"""

import time

from config import MIN_BREAK_SECONDS
from zone_manager import all_employee_names


# Initialize employee states
employee_states = {
    name: {
        "state": "ABSENT",
        "last_change": time.time(),
        "presence_counter": 0,
        "absence_counter": 0,
    }
    for name in all_employee_names
}


def update_state(name, detected, report_data):
    """
    Updates the state of an employee based on detection input.

    Args:
        name (str): Employee name.
        detected (bool): Whether the employee is detected.
        report_data (dict): Report data for the employee.
    """
    state_data = employee_states[name]
    current_time = time.time()

    if detected:
        state_data["presence_counter"] += 1
        state_data["absence_counter"] = 0

        if (
            state_data["presence_counter"] >= 2
            and state_data["state"] == "ABSENT"
        ):
            duration = current_time - state_data["last_change"]

            report_data[name]["out_seat_seconds"] += duration
            report_data[name]["current_state"] = "PRESENT"

            if duration > MIN_BREAK_SECONDS:
                report_data[name]["total_breaks"] += 1

            state_data["state"] = "PRESENT"
            state_data["last_change"] = current_time

    else:
        state_data["absence_counter"] += 1
        state_data["presence_counter"] = 0

        if (
            state_data["absence_counter"] >= 2
            and state_data["state"] == "PRESENT"
        ):
            duration = current_time - state_data["last_change"]

            report_data[name]["in_seat_seconds"] += duration
            report_data[name]["current_state"] = "ABSENT"

            state_data["state"] = "ABSENT"
            state_data["last_change"] = current_time
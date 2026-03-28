#Checks if the center of the detected box is inside the defined zone
def inside_zone(box, zone):
    x1, y1, x2, y2 = box
    zx1, zy1, zx2, zy2 = zone

    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    return zx1 < center_x < zx2 and zy1 < center_y < zy2

#Formats seconds into a human-readable string
def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"
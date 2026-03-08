import math

def calculate_azimuth(lat1, lon1, lat2, lon2):
    """
    Calculates the bearing/azimuth between two points.
    Input: Decimal degrees. Output: Degrees (0-360).
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    delta_lon = lon2 - lon1

    y = math.sin(delta_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - \
        math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)

    bearing = math.atan2(y, x)
    
    # Convert radians to degrees and normalize to 0-360
    return (math.degrees(bearing) + 360) % 360

"""
Distance calculation utilities for the Emergency Response System.
Provides functions to calculate distances between coordinates and estimate travel times.
"""

import math
from geopy.distance import geodesic

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth specified in decimal degrees.
    
    Args:
        lat1, lon1: Coordinates of the first point
        lat2, lon2: Coordinates of the second point
        
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r

def geodesic_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the geodesic distance between two points using geopy's geodesic function.
    More accurate than haversine for most earth distances.
    
    Args:
        lat1, lon1: Coordinates of the first point
        lat2, lon2: Coordinates of the second point
        
    Returns:
        Distance in kilometers
    """
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def estimate_travel_time(distance_km, avg_speed_kmh=40):
    """
    Estimate travel time based on distance and average speed.
    Default average speed is 40 km/h assuming urban traffic conditions.
    
    Args:
        distance_km: Distance in kilometers
        avg_speed_kmh: Average speed in kilometers per hour
        
    Returns:
        Estimated travel time in minutes
    """
    # Calculate time in hours, then convert to minutes
    time_hours = distance_km / avg_speed_kmh
    time_minutes = time_hours * 60
    
    return time_minutes

def format_distance(distance_km):
    """
    Format a distance value for display.
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        Formatted distance string
    """
    if distance_km < 1:
        # Convert to meters for small distances
        distance_m = int(distance_km * 1000)
        return f"{distance_m} meters"
    else:
        # Round to 1 decimal place
        return f"{distance_km:.1f} km"

def format_travel_time(minutes):
    """
    Format a travel time value for display.
    
    Args:
        minutes: Travel time in minutes
        
    Returns:
        Formatted time string
    """
    if minutes < 1:
        # Convert to seconds for very short times
        seconds = int(minutes * 60)
        return f"{seconds} seconds"
    elif minutes < 60:
        # Round to nearest minute
        return f"{int(round(minutes))} minutes"
    else:
        # Format as hours and minutes
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if mins == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours > 1 else ''} {mins} minute{'s' if mins > 1 else ''}"
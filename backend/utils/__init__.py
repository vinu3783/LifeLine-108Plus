"""
Utilities package for the Emergency Response System.
This package contains utility functions and helper modules used across the application.
"""

from .distance import (
    haversine_distance, 
    geodesic_distance, 
    estimate_travel_time,
    format_distance,
    format_travel_time
)

# Import test data utilities when in development mode
try:
    from .test_data import (
        DAVANAGERE_COORDINATES,
        SAMPLE_AMBULANCES,
        SAMPLE_EMERGENCY_CALL,
        populate_test_data
    )
except ImportError:
    # In production, test_data might not be available
    pass
"""
Services package for the Emergency Response System.
This package contains service classes that implement the core business logic.
"""

from .location_service import LocationService
from .sms_service import SMSService
from .ambulance_service import AmbulanceService

# Create service instances
location_service = None
sms_service = None
ambulance_service = None

def init_services(app):
    """
    Initialize all service classes with the Flask application context.
    This should be called after the Flask app is created.
    
    Args:
        app: Flask application instance
    """
    global location_service, sms_service, ambulance_service
    
    # Initialize services with application context
    with app.app_context():
        location_service = LocationService()
        sms_service = SMSService()
        ambulance_service = AmbulanceService()
    
    return {
        'location_service': location_service,
        'sms_service': sms_service,
        'ambulance_service': ambulance_service
    }

def get_location_service():
    """Get the LocationService instance"""
    return location_service

def get_sms_service():
    """Get the SMSService instance"""
    return sms_service

def get_ambulance_service():
    """Get the AmbulanceService instance"""
    return ambulance_service
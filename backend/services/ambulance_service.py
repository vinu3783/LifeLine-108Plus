from datetime import datetime
from flask import current_app as app
from backend.models import db, Ambulance, EmergencyCall
from backend.services.location_service import LocationService
from backend.services.sms_service import SMSService

class AmbulanceService:
    def __init__(self):
        self.location_service = LocationService()
        self.sms_service = SMSService()
    
    def update_ambulance_location(self, ambulance_id, latitude, longitude):
        """Update ambulance location in the database"""
        ambulance = Ambulance.query.filter_by(ambulance_id=ambulance_id).first()
        if ambulance:
            ambulance.latitude = latitude
            ambulance.longitude = longitude
            ambulance.last_updated = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def get_available_ambulances(self):
        """Get list of all available ambulances"""
        return Ambulance.query.filter_by(is_available=True).all()
    
    def assign_nearest_ambulance(self, emergency_call_id):
        """Find and assign the nearest available ambulance to the emergency"""
        emergency_call = EmergencyCall.query.get(emergency_call_id)
        if not emergency_call or not emergency_call.latitude or not emergency_call.longitude:
            return {"success": False, "error": "Invalid emergency call or location not shared"}
        
        # Get all available ambulances
        available_ambulances = self.get_available_ambulances()
        if not available_ambulances:
            return {"success": False, "error": "No ambulances available"}
        
        # Find the nearest ambulance
        nearest_ambulance, distance = self.location_service.find_nearest_ambulance(
            emergency_call.latitude, 
            emergency_call.longitude, 
            available_ambulances
        )
        
        if not nearest_ambulance:
            return {"success": False, "error": "Could not find a suitable ambulance"}
        
        # Calculate ETA (rough estimate: assume 40 km/h average speed in city traffic)
        eta_minutes = int((distance / 40) * 60)
        
        # Generate route URL
        route_url = self.location_service.get_route_url(
            nearest_ambulance.latitude,
            nearest_ambulance.longitude,
            emergency_call.latitude,
            emergency_call.longitude
        )
        
        # Update emergency call with assigned ambulance
        emergency_call.assigned_ambulance_id = nearest_ambulance.id
        emergency_call.assigned_time = datetime.utcnow()
        emergency_call.status = "assigned"
        
        # Mark ambulance as unavailable
        nearest_ambulance.is_available = False
        
        db.session.commit()
        
        # Notify ambulance driver
        self.sms_service.notify_ambulance_driver(
            nearest_ambulance.driver_phone,
            emergency_call.latitude,
            emergency_call.longitude,
            emergency_call.address,
            route_url
        )
        
        # Send confirmation to victim
        self.sms_service.send_confirmation_to_victim(
            emergency_call.caller_phone,
            nearest_ambulance.ambulance_id,
            nearest_ambulance.driver_name,
            eta_minutes
        )
        
        return {
            "success": True,
            "ambulance_id": nearest_ambulance.ambulance_id,
            "driver_name": nearest_ambulance.driver_name,
            "distance_km": round(distance, 2),
            "eta_minutes": eta_minutes
        }
    
    def mark_ambulance_arrived(self, ambulance_id, emergency_call_id):
        """Mark that ambulance has arrived at the emergency location"""
        emergency_call = EmergencyCall.query.get(emergency_call_id)
        if emergency_call:
            emergency_call.pickup_time = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def complete_emergency(self, emergency_call_id):
        """Mark emergency as complete and free up the ambulance"""
        emergency_call = EmergencyCall.query.get(emergency_call_id)
        if not emergency_call:
            return False
            
        # Update emergency call status
        emergency_call.status = "completed"
        emergency_call.completion_time = datetime.utcnow()
        
        # Make ambulance available again
        if emergency_call.assigned_ambulance:
            emergency_call.assigned_ambulance.is_available = True
            
        db.session.commit()
        return True
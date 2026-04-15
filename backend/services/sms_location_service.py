"""
SMS-based location protocol service.
Provides a fallback mechanism for location sharing when internet is unavailable.
"""

import random
import string
import re
from datetime import datetime, timedelta
from flask import current_app as app
from backend.models import db, EmergencyCall
from backend.services.sms_service import SMSService
from backend.services.location_service import LocationService

class SMSLocationService:
    def __init__(self):
        self.sms_service = SMSService()
        self.location_service = LocationService()
    
    def generate_location_code(self):
        """Generate a unique random code for SMS location sharing"""
        prefix = app.config.get('SMS_LOCATION_CODE_PREFIX', 'ERS-LOC')
        length = app.config.get('SMS_LOCATION_CODE_LENGTH', 6)
        chars = string.ascii_uppercase + string.digits
        
        # Generate a unique code
        while True:
            random_part = ''.join(random.choice(chars) for _ in range(length))
            code = f"{prefix}-{random_part}"
            
            # Check if code already exists
            existing = EmergencyCall.query.filter_by(sms_location_code=code).first()
            if not existing:
                return code
    
    def initiate_sms_location_protocol(self, emergency_call):
        """
        Initiate the SMS-based location protocol for an emergency call
        
        Args:
            emergency_call: EmergencyCall object
            
        Returns:
            Boolean indicating success
        """
        if not emergency_call.caller_phone:
            app.logger.error("Cannot initiate SMS location protocol: No caller phone number")
            return False
        
        # Generate and save location code
        location_code = self.generate_location_code()
        expiry_time = datetime.utcnow() + timedelta(seconds=app.config.get('SMS_LOCATION_CODE_EXPIRY', 60*30))
        
        emergency_call.sms_location_code = location_code
        emergency_call.sms_code_expiry = expiry_time
        emergency_call.connectivity_status = 'offline'  # Mark as offline since we're using SMS
        db.session.commit()
        
        # Send SMS with instructions
        keyword = app.config.get('SMS_REPLY_KEYWORD', 'LOCATION')
        sms_text = f"Emergency Response: Reply to this message with {keyword} to automatically share your exact location. Your emergency code is: {location_code}"
        
        result = self.sms_service.send_sms(emergency_call.caller_phone, sms_text)
        
        if result["success"]:
            app.logger.info(f"SMS location protocol initiated for call {emergency_call.id}")
            return True
        else:
            app.logger.error(f"Failed to send SMS for location protocol: {result.get('error', 'Unknown error')}")
            return False
    
    def process_location_sms(self, from_number, message_body):
        """
        Process an incoming SMS containing location information
        
        Args:
            from_number: Sender's phone number
            message_body: SMS text content
            
        Returns:
            Dict with processing results
        """
        # Look for location code in the message
        location_code = self.extract_location_code(message_body)
        
        if location_code:
            # Find emergency call by location code
            emergency_call = EmergencyCall.query.filter_by(
                sms_location_code=location_code
            ).filter(
                EmergencyCall.status.in_(['initiated', 'location_requested'])
            ).first()
        else:
            # If no code found, try to find by phone number (most recent call)
            emergency_call = EmergencyCall.query.filter_by(
                caller_phone=from_number
            ).filter(
                EmergencyCall.status.in_(['initiated', 'location_requested'])
            ).order_by(EmergencyCall.call_time.desc()).first()
        
        if not emergency_call:
            app.logger.warning(f"Received location SMS but no matching emergency call found: {from_number}")
            return {"success": False, "error": "No matching emergency call found"}
        
        # Check if the location code has expired
        if emergency_call.sms_code_expiry and emergency_call.sms_code_expiry < datetime.utcnow():
            app.logger.warning(f"Location code expired for call {emergency_call.id}")
            return {"success": False, "error": "Location code expired"}
        
        # Extract coordinates using various methods
        location_data = self.extract_location_from_sms(message_body)
        
        if location_data["success"]:
            # Update emergency call with location data
            emergency_call.latitude = location_data["latitude"]
            emergency_call.longitude = location_data["longitude"]
            emergency_call.status = 'location_shared'
            emergency_call.location_shared_time = datetime.utcnow()
            emergency_call.location_method = 'sms'
            
            # Try to get address using reverse geocoding
            address = self.location_service.get_address_from_coordinates(
                location_data["latitude"], 
                location_data["longitude"]
            )
            
            if address:
                emergency_call.address = address
            
            db.session.commit()
            
            # Send confirmation SMS
            confirmation_text = "Thank you. Your location has been received. Emergency services have been dispatched to your location. Stay where you are if possible."
            self.sms_service.send_sms(from_number, confirmation_text)
            
            return {
                "success": True,
                "emergency_call_id": emergency_call.id,
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"]
            }
        else:
            # Location extraction failed
            app.logger.warning(f"Failed to extract location from SMS: {message_body}")
            
            # Send error message
            keyword = app.config.get('SMS_REPLY_KEYWORD', 'LOCATION')
            error_text = f"We couldn't detect your location. Please reply with {keyword} followed by your address or a nearby landmark."
            self.sms_service.send_sms(from_number, error_text)
            
            return {"success": False, "error": "Could not extract location from SMS"}
    
    def extract_location_code(self, message_body):
        """Extract location code from SMS text"""
        prefix = app.config.get('SMS_LOCATION_CODE_PREFIX', 'ERS-LOC')
        length = app.config.get('SMS_LOCATION_CODE_LENGTH', 6)
        
        pattern = f"{prefix}-[A-Z0-9]{{{length}}}"
        match = re.search(pattern, message_body)
        
        if match:
            return match.group(0)
        
        return None
    
    def extract_location_from_sms(self, message_body):
        """
        Extract coordinates from an SMS message.
        Handles multiple formats:
        1. Explicit coordinates: "14.4644, 75.9218"
        2. Google Maps links: "https://maps.google.com/?q=14.4644,75.9218"
        3. Keyword followed by coordinates: "LOCATION 14.4644, 75.9218"
        4. Automated location SMS format from various phone models
        
        Returns:
            Dict with success flag and coordinates if successful
        """
        # Try to find explicit coordinates pattern
        coord_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        match = re.search(coord_pattern, message_body)
        
        if match:
            try:
                latitude = float(match.group(1))
                longitude = float(match.group(2))
                
                # Basic validation of coordinates
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    return {
                        "success": True, 
                        "latitude": latitude, 
                        "longitude": longitude,
                        "method": "explicit_coordinates"
                    }
            except ValueError:
                pass
        
        # Try to find Google Maps link
        maps_pattern = r'maps\.google\.com/\?q=(-?\d+\.?\d*),(-?\d+\.?\d*)'
        maps_match = re.search(maps_pattern, message_body)
        
        if maps_match:
            try:
                latitude = float(maps_match.group(1))
                longitude = float(maps_match.group(2))
                
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    return {
                        "success": True, 
                        "latitude": latitude, 
                        "longitude": longitude,
                        "method": "google_maps_link"
                    }
            except ValueError:
                pass
        
        # Check for common formats from different phone models
        # Android format often includes altitude, accuracy, etc.
        android_pattern = r'http://maps\.google\.com/\?saddr=(-?\d+\.?\d*),(-?\d+\.?\d*)'
        android_match = re.search(android_pattern, message_body)
        
        if android_match:
            try:
                latitude = float(android_match.group(1))
                longitude = float(android_match.group(2))
                
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    return {
                        "success": True, 
                        "latitude": latitude, 
                        "longitude": longitude,
                        "method": "android_format"
                    }
            except ValueError:
                pass
        
        # Check for WhatsApp location format
        whatsapp_pattern = r'WhatsApp Location: (-?\d+\.?\d*),(-?\d+\.?\d*)'
        whatsapp_match = re.search(whatsapp_pattern, message_body, re.IGNORECASE)
        
        if whatsapp_match:
            try:
                latitude = float(whatsapp_match.group(1))
                longitude = float(whatsapp_match.group(2))
                
                if -90 <= latitude <= 90 and -180 <= longitude <= 180:
                    return {
                        "success": True, 
                        "latitude": latitude, 
                        "longitude": longitude,
                        "method": "whatsapp_format"
                    }
            except ValueError:
                pass
        
        # Location extraction failed
        return {"success": False, "error": "Could not extract location from SMS"}
    
    def handle_sms_menu(self, from_number, message_body):
        """
        Handle SMS menu system for callers without internet
        
        Args:
            from_number: Sender's phone number
            message_body: SMS text content
            
        Returns:
            Boolean indicating if command was handled
        """
        message_upper = message_body.strip().upper()
        
        if message_upper == 'MENU':
            menu_text = "Emergency Response System Menu:\n" \
                       "1. HELP [location] - Report emergency\n" \
                       "2. STATUS - Check ambulance status\n" \
                       "3. CANCEL - Cancel emergency request\n" \
                       "4. INFO - About this service"
            self.sms_service.send_sms(from_number, menu_text)
            return True
        
        elif message_upper == 'STATUS':
            # Find active emergency for this number
            emergency_call = EmergencyCall.query.filter_by(
                caller_phone=from_number
            ).filter(
                EmergencyCall.status.in_(['initiated', 'location_shared', 'assigned'])
            ).order_by(EmergencyCall.call_time.desc()).first()
            
            if emergency_call:
                if emergency_call.status == 'assigned' and emergency_call.assigned_ambulance_id:
                    # Get ambulance info
                    from backend.models import Ambulance
                    ambulance = Ambulance.query.get(emergency_call.assigned_ambulance_id)
                    
                    if ambulance:
                        # Calculate ETA
                        from backend.services.ambulance_service import AmbulanceService
                        ambulance_service = AmbulanceService()
                        eta_minutes = ambulance_service.calculate_eta(emergency_call.id)
                        
                        status_text = f"Ambulance {ambulance.ambulance_id} is on the way. " \
                                    f"Driver: {ambulance.driver_name}. " \
                                    f"ETA: approximately {eta_minutes} minutes."
                    else:
                        status_text = "An ambulance has been assigned and is on the way to your location."
                else:
                    status_text = "Your emergency has been recorded. " \
                                "We are working on assigning an ambulance to your location."
                
                self.sms_service.send_sms(from_number, status_text)
            else:
                self.sms_service.send_sms(from_number, "No active emergency found for your number.")
            
            return True
        
        elif message_upper == 'CANCEL':
            # Find active emergency for this number
            emergency_call = EmergencyCall.query.filter_by(
                caller_phone=from_number
            ).filter(
                EmergencyCall.status.in_(['initiated', 'location_shared', 'assigned'])
            ).order_by(EmergencyCall.call_time.desc()).first()
            
            if emergency_call:
                # Add cancellation logic here
                emergency_call.status = 'cancelled'
                emergency_call.completion_time = datetime.utcnow()
                db.session.commit()
                
                # If ambulance was assigned, make it available again
                if emergency_call.assigned_ambulance_id:
                    from backend.models import Ambulance
                    ambulance = Ambulance.query.get(emergency_call.assigned_ambulance_id)
                    if ambulance:
                        ambulance.is_available = True
                        db.session.commit()
                
                self.sms_service.send_sms(from_number, "Your emergency request has been cancelled.")
            else:
                self.sms_service.send_sms(from_number, "No active emergency found to cancel.")
            
            return True
        
        elif message_upper == 'INFO':
            info_text = "Emergency Response System provides immediate assistance in medical emergencies. " \
                       "Available 24/7. Operated by Davanagere Emergency Services."
            self.sms_service.send_sms(from_number, info_text)
            return True
        
        return False  
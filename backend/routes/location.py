from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, abort
from backend.models import db, EmergencyCall
from backend.services.location_service import LocationService
from backend.services.ambulance_service import AmbulanceService

location_bp = Blueprint('location', __name__)
location_service = LocationService()
ambulance_service = AmbulanceService()

@location_bp.route('/share-location/<location_link_id>')
def share_location_page(location_link_id):
    """Render the location sharing page for the victim"""
    # Check if the location link ID is valid
    emergency_call = EmergencyCall.query.filter_by(location_link_id=location_link_id).first()
    
    if not emergency_call:
        abort(404)
    
    # Return the location sharing HTML page
    return render_template('location_share/index.html', 
                          location_link_id=location_link_id,
                          emergency_call_id=emergency_call.id)

@location_bp.route('/api/location/submit', methods=['POST'])
def submit_location():
    """API endpoint to receive the shared location from the victim"""
    data = request.get_json()
    
    if not data or 'location_link_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    # Find the emergency call with the provided location_link_id
    emergency_call = EmergencyCall.query.filter_by(
        location_link_id=data['location_link_id']
    ).first()
    
    if not emergency_call:
        return jsonify({"success": False, "error": "Invalid location link"}), 404
    
    # Update the emergency call with location data
    emergency_call.latitude = data['latitude']
    emergency_call.longitude = data['longitude']
    emergency_call.status = 'location_shared'
    emergency_call.location_shared_time = datetime.utcnow()
    
    # Get address based on coordinates
    address = location_service.get_address_from_coordinates(
        data['latitude'], 
        data['longitude']
    )
    emergency_call.address = address
    
    db.session.commit()
    
    # Automatically assign the nearest ambulance
    ambulance_result = ambulance_service.assign_nearest_ambulance(emergency_call.id)
    
    return jsonify({
        "success": True,
        "message": "Location shared successfully",
        "ambulance_assigned": ambulance_result["success"] if "success" in ambulance_result else False
    })

@location_bp.route('/api/location/test-coordinates', methods=['GET'])
def test_coordinates():
    """
    Test endpoint for demo purposes to get some coordinates in Davanagere, Karnataka
    In a real application, you would use actual GPS coordinates, not test data
    """
    # Sample coordinates for Davanagere, Karnataka, India
    test_locations = {
        "victim": {
            "latitude": 14.4644,
            "longitude": 75.9218,
            "description": "Near Davanagere Central Bus Station"
        },
        "ambulance1": {
            "latitude": 14.4732,
            "longitude": 75.9260,
            "description": "Near Chigateri District Hospital, Davanagere"
        },
        "ambulance2": {
            "latitude": 14.4510,
            "longitude": 75.9190,
            "description": "Near GMIT College, Davanagere"
        }
    }
    
    return jsonify({
        "success": True,
        "test_locations": test_locations
    })

@location_bp.route('/api/sms/webhook', methods=['POST'])
def sms_webhook():
    """Webhook for incoming SMS messages from Twilio"""
    # Extract message data
    from_number = request.values.get('From', '')
    message_body = request.values.get('Body', '')
    
    app.logger.info(f"Received SMS from {from_number}: {message_body}")
    
    # Initialize SMS location service
    from backend.services.sms_location_service import SMSLocationService
    sms_location_service = SMSLocationService()
    
    # Check if this is a MENU command
    if message_body.strip().upper() == 'MENU':
        sms_location_service.handle_sms_menu(from_number, message_body)
        return '', 200
    
    # Check if this contains the location reply keyword
    keyword = app.config['SMS_REPLY_KEYWORD']
    if keyword in message_body.upper():
        # This is likely a location response
        result = sms_location_service.process_location_sms(from_number, message_body)
        
        if result["success"]:
            # Attempt to assign an ambulance automatically
            from backend.services.ambulance_service import AmbulanceService
            ambulance_service = AmbulanceService()
            
            ambulance_result = ambulance_service.assign_nearest_ambulance(result["emergency_call_id"])
            
            if ambulance_result["success"]:
                # Send ambulance dispatch confirmation via SMS
                eta_minutes = ambulance_result.get("eta_minutes", "")
                ambulance_id = ambulance_result.get("ambulance_id", "")
                
                confirmation_msg = f"An ambulance ({ambulance_id}) has been dispatched to your location. "
                if eta_minutes:
                    confirmation_msg += f"Estimated arrival time: {eta_minutes} minutes. "
                confirmation_msg += "Please stay where you are."
                
                sms_service.send_sms(from_number, confirmation_msg)
        
        return '', 200
    
    # If not a location message, check if this is a new emergency request
    emergency_keywords = ['HELP', 'SOS', 'EMERGENCY', '108']
    for keyword in emergency_keywords:
        if keyword in message_body.upper():
            # This appears to be a new emergency request via SMS
            
            # Extract location if present in the initial message
            location_data = sms_location_service.extract_location_from_sms(message_body)
            
            # Create a new emergency call
            emergency_call = EmergencyCall(
                caller_phone=from_number,
                status='initiated',
                source='sms'
            )
            
            if location_data["success"]:
                # Location included in initial message
                emergency_call.latitude = location_data["latitude"]
                emergency_call.longitude = location_data["longitude"]
                emergency_call.status = 'location_shared'
                emergency_call.location_shared_time = datetime.utcnow()
                emergency_call.location_method = 'sms'
                
                # Try to get address
                from backend.services.location_service import LocationService
                location_service = LocationService()
                address = location_service.get_address_from_coordinates(
                    location_data["latitude"], 
                    location_data["longitude"]
                )
                
                if address:
                    emergency_call.address = address
            
            db.session.add(emergency_call)
            db.session.commit()
            
            if location_data["success"]:
                # Send confirmation and try to assign ambulance
                sms_service.send_sms(
                    from_number, 
                    "Your location has been received. Emergency services are being dispatched."
                )
                
                # Try to assign ambulance
                from backend.services.ambulance_service import AmbulanceService
                ambulance_service = AmbulanceService()
                
                ambulance_result = ambulance_service.assign_nearest_ambulance(emergency_call.id)
                
                if ambulance_result["success"]:
                    # Send ambulance dispatch confirmation
                    eta_minutes = ambulance_result.get("eta_minutes", "")
                    ambulance_id = ambulance_result.get("ambulance_id", "")
                    
                    confirmation_msg = f"An ambulance ({ambulance_id}) has been dispatched to your location. "
                    if eta_minutes:
                        confirmation_msg += f"Estimated arrival time: {eta_minutes} minutes. "
                    confirmation_msg += "Please stay where you are."
                    
                    sms_service.send_sms(from_number, confirmation_msg)
            else:
                # Initiate SMS location protocol to get location
                sms_location_service.initiate_sms_location_protocol(emergency_call)
            
            return '', 200
    
    # If we get here, it's not a recognized command
    # Send help menu
    sms_location_service.handle_sms_menu(from_number, 'MENU')
    
    return '', 200
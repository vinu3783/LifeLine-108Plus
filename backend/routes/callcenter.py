from datetime import datetime
from flask import Blueprint, request, jsonify, current_app as app
from backend.models import db, EmergencyCall
from backend.services.location_service import LocationService
from backend.services.sms_service import SMSService
from backend.services.ambulance_service import AmbulanceService

callcenter_bp = Blueprint('callcenter', __name__, url_prefix='/api/callcenter')
location_service = LocationService()
sms_service = SMSService()
ambulance_service = AmbulanceService()

@callcenter_bp.route('/initiate-call', methods=['POST'])
def initiate_call():
    """API endpoint for call center to initiate emergency response process"""
    data = request.get_json()
    
    if not data or 'caller_phone' not in data:
        return jsonify({"success": False, "error": "Caller phone number is required"}), 400
    
    # Generate location sharing link ID
    location_link_id = location_service.generate_location_link_id()
    
    # Create emergency call record
    emergency_call = EmergencyCall(
        caller_phone=data['caller_phone'],
        location_link_id=location_link_id,
        status='initiated'
    )
    
    db.session.add(emergency_call)
    db.session.commit()
    
    # Generate location sharing URL
    location_share_url = location_service.get_location_share_url(location_link_id)
    
    # Send SMS with location sharing link to the caller
    sms_result = sms_service.send_location_share_link(
        data['caller_phone'], 
        location_share_url
    )
    
    return jsonify({
        "success": True,
        "emergency_call_id": emergency_call.id,
        "location_link_id": location_link_id,
        "location_share_url": location_share_url,
        "sms_sent": sms_result["success"]
    })

@callcenter_bp.route('/active-calls', methods=['GET'])
def get_active_calls():
    """API endpoint to get all active emergency calls for the dashboard"""
    # Get all calls that are not completed
    active_calls = EmergencyCall.query.filter(
        EmergencyCall.status != 'completed'
    ).order_by(EmergencyCall.call_time.desc()).all()
    
    return jsonify({
        "success": True,
        "calls": [call.to_dict() for call in active_calls]
    })

@callcenter_bp.route('/call/<int:call_id>', methods=['GET'])
def get_call_details(call_id):
    """API endpoint to get details of a specific emergency call"""
    call = EmergencyCall.query.get(call_id)
    
    if not call:
        return jsonify({"success": False, "error": "Call not found"}), 404
    
    return jsonify({
        "success": True,
        "call": call.to_dict()
    })

@callcenter_bp.route('/assign-ambulance/<int:call_id>', methods=['POST'])
def assign_ambulance(call_id):
    """API endpoint to manually assign the nearest ambulance to an emergency"""
    result = ambulance_service.assign_nearest_ambulance(call_id)
    
    if not result["success"]:
        return jsonify(result), 400
    
    return jsonify(result)

@callcenter_bp.route('/complete-emergency/<int:call_id>', methods=['POST'])
def complete_emergency(call_id):
    """API endpoint to mark an emergency as completed"""
    success = ambulance_service.complete_emergency(call_id)
    
    if not success:
        return jsonify({"success": False, "error": "Failed to complete emergency call"}), 400
    
    return jsonify({"success": True})

@callcenter_bp.route('/api/callcenter/initiate-call', methods=['POST'])
def initiate_call():
    """API endpoint for call center to initiate emergency response process"""
    data = request.get_json()
    
    if not data or 'caller_phone' not in data:
        return jsonify({"success": False, "error": "Caller phone number is required"}), 400
    
    # Check connectivity status if provided
    connectivity_status = data.get('connectivity_status', 'unknown')
    
    # Generate location sharing link ID for web-based sharing
    location_link_id = location_service.generate_location_link_id()
    
    # Create emergency call record
    emergency_call = EmergencyCall(
        caller_phone=data['caller_phone'],
        location_link_id=location_link_id,
        connectivity_status=connectivity_status,
        status='initiated'
    )
    
    db.session.add(emergency_call)
    db.session.commit()
    
    # Generate location sharing URL for web-based sharing
    location_share_url = location_service.get_location_share_url(location_link_id)
    
    sms_success = False
    sms_protocol_initiated = False
    
    # If the caller has internet access, send web link
    if connectivity_status in ['online', 'unknown']:
        # Send SMS with location sharing link to the caller
        sms_result = sms_service.send_location_share_link(
            data['caller_phone'], 
            location_share_url
        )
        sms_success = sms_result.get("success", False)
    
    # If the caller has no internet or SMS failed, initiate SMS protocol
    if connectivity_status == 'offline' or not sms_success:
        from backend.services.sms_location_service import SMSLocationService
        sms_location_service = SMSLocationService()
        
        sms_protocol_initiated = sms_location_service.initiate_sms_location_protocol(emergency_call)
    
    return jsonify({
        "success": True,
        "emergency_call_id": emergency_call.id,
        "location_link_id": location_link_id,
        "location_share_url": location_share_url,
        "sms_sent": sms_success,
        "sms_protocol_initiated": sms_protocol_initiated,
        "connectivity_status": connectivity_status
    })

# Add a new endpoint to manually initiate SMS protocol for an existing call
@callcenter_bp.route('/api/callcenter/initiate-sms-protocol/<int:call_id>', methods=['POST'])
def initiate_sms_protocol(call_id):
    """Manually initiate SMS-based location protocol for an existing call"""
    emergency_call = EmergencyCall.query.get(call_id)
    
    if not emergency_call:
        return jsonify({"success": False, "error": "Emergency call not found"}), 404
    
    from backend.services.sms_location_service import SMSLocationService
    sms_location_service = SMSLocationService()
    
    success = sms_location_service.initiate_sms_location_protocol(emergency_call)
    
    if success:
        return jsonify({
            "success": True,
            "message": "SMS location protocol initiated successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Failed to initiate SMS location protocol"
        })
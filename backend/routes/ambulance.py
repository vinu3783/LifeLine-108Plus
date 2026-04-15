from flask import Blueprint, request, jsonify, render_template
from backend.models import db, Ambulance, EmergencyCall
from backend.services.ambulance_service import AmbulanceService

ambulance_bp = Blueprint('ambulance', __name__, url_prefix='/api/ambulance')
ambulance_service = AmbulanceService()

@ambulance_bp.route('/app')
def ambulance_app():
    """Render the ambulance driver web application"""
    return render_template('ambulance_app/index.html')

@ambulance_bp.route('/login', methods=['POST'])
def ambulance_login():
    """API endpoint for ambulance driver to log in"""
    data = request.get_json()
    
    if not data or 'ambulance_id' not in data:
        return jsonify({"success": False, "error": "Ambulance ID is required"}), 400
    
    # Find the ambulance in the database
    ambulance = Ambulance.query.filter_by(ambulance_id=data['ambulance_id']).first()
    
    if not ambulance:
        return jsonify({"success": False, "error": "Invalid ambulance ID"}), 404
    
    return jsonify({
        "success": True,
        "ambulance": ambulance.to_dict()
    })

@ambulance_bp.route('/update-location', methods=['POST'])
def update_location():
    """API endpoint for ambulance driver to update their location"""
    data = request.get_json()
    
    if not data or 'ambulance_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    # Update ambulance location
    success = ambulance_service.update_ambulance_location(
        data['ambulance_id'],
        data['latitude'],
        data['longitude']
    )
    
    if not success:
        return jsonify({"success": False, "error": "Failed to update location"}), 400
    
    return jsonify({"success": True})

@ambulance_bp.route('/get-assignment/<ambulance_id>', methods=['GET'])
def get_assignment(ambulance_id):
    """API endpoint for ambulance driver to get their active assignment"""
    # Find the ambulance
    ambulance = Ambulance.query.filter_by(ambulance_id=ambulance_id).first()
    
    if not ambulance:
        return jsonify({"success": False, "error": "Invalid ambulance ID"}), 404
    
    # Find active emergency assignment
    emergency_call = EmergencyCall.query.filter_by(
        assigned_ambulance_id=ambulance.id,
        status='assigned'
    ).first()
    
    if not emergency_call:
        return jsonify({
            "success": True,
            "has_assignment": False
        })
    
    return jsonify({
        "success": True,
        "has_assignment": True,
        "emergency_call": emergency_call.to_dict()
    })

@ambulance_bp.route('/mark-arrived', methods=['POST'])
def mark_arrived():
    """API endpoint for ambulance driver to mark arrival at the emergency location"""
    data = request.get_json()
    
    if not data or 'ambulance_id' not in data or 'emergency_call_id' not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    success = ambulance_service.mark_ambulance_arrived(
        data['ambulance_id'],
        data['emergency_call_id']
    )
    
    if not success:
        return jsonify({"success": False, "error": "Failed to mark arrival"}), 400
    
    return jsonify({"success": True})

@ambulance_bp.route('/mark-completed', methods=['POST'])
def mark_completed():
    """API endpoint for ambulance driver to mark emergency as completed"""
    data = request.get_json()
    
    if not data or 'emergency_call_id' not in data:
        return jsonify({"success": False, "error": "Emergency call ID is required"}), 400
    
    success = ambulance_service.complete_emergency(data['emergency_call_id'])
    
    if not success:
        return jsonify({"success": False, "error": "Failed to complete emergency"}), 400
    
    return jsonify({"success": True})

@ambulance_bp.route('/register', methods=['POST'])
def register_ambulance():
    """API endpoint to register a new ambulance in the system"""
    data = request.get_json()
    
    required_fields = ['ambulance_id', 'driver_name', 'driver_phone', 'latitude', 'longitude']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    # Check if ambulance_id already exists
    existing = Ambulance.query.filter_by(ambulance_id=data['ambulance_id']).first()
    if existing:
        return jsonify({"success": False, "error": "Ambulance ID already registered"}), 400
    
    # Create new ambulance
    new_ambulance = Ambulance(
        ambulance_id=data['ambulance_id'],
        driver_name=data['driver_name'],
        driver_phone=data['driver_phone'],
        latitude=data['latitude'],
        longitude=data['longitude'],
        is_available=True
    )
    
    db.session.add(new_ambulance)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "ambulance": new_ambulance.to_dict()
    })

@ambulance_bp.route('/all', methods=['GET'])
def get_all_ambulances():
    """API endpoint to get all registered ambulances"""
    ambulances = Ambulance.query.all()
    
    return jsonify({
        "success": True,
        "ambulances": [ambulance.to_dict() for ambulance in ambulances]
    })
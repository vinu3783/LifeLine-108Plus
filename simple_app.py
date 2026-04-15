"""
Improved Emergency Response System application with better path handling.
"""

import eventlet
eventlet.monkey_patch()

import os
import sqlite3
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g, abort, send_from_directory
from flask_socketio import SocketIO

# Get absolute path to the current directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Ensure frontend directory exists
if not os.path.exists(FRONTEND_DIR):
    os.makedirs(FRONTEND_DIR)
    for subdir in ['callcenter', 'ambulance_app', 'location_share']:
        os.makedirs(os.path.join(FRONTEND_DIR, subdir), exist_ok=True)

# Check if index.html files exist
for subdir in ['callcenter', 'ambulance_app', 'location_share']:
    index_path = os.path.join(FRONTEND_DIR, subdir, 'index.html')
    if not os.path.exists(index_path):
        print(f"WARNING: {index_path} does not exist!")

# Create Flask application
app = Flask(__name__, 
            static_folder=FRONTEND_DIR,
            template_folder=FRONTEND_DIR)

# Configuration
DATABASE = os.path.join(BASE_DIR, 'emergency_response.db')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
DEBUG = True

app.config.from_mapping(
    SECRET_KEY=SECRET_KEY,
    DEBUG=DEBUG
)

# Initialize database tables
def init_db_tables():
    try:
        with app.app_context():
            db = get_db()
            # Create ambulances table
            db.execute('''
            CREATE TABLE IF NOT EXISTS ambulances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ambulance_id TEXT UNIQUE NOT NULL,
                driver_name TEXT NOT NULL,
                driver_phone TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                is_available INTEGER DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create emergency_calls table
            db.execute('''
            CREATE TABLE IF NOT EXISTS emergency_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caller_phone TEXT NOT NULL,
                call_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'initiated',
                location_link_id TEXT UNIQUE,
                latitude REAL,
                longitude REAL,
                address TEXT,
                assigned_ambulance_id INTEGER,
                assigned_time TIMESTAMP,
                location_shared_time TIMESTAMP,
                pickup_time TIMESTAMP,
                completion_time TIMESTAMP,
                FOREIGN KEY (assigned_ambulance_id) REFERENCES ambulances (id)
            )
            ''')
            
            # Seed test data if empty
            cursor = db.execute("SELECT COUNT(*) FROM ambulances")
            count = cursor.fetchone()[0]
            if count == 0:
                print("Seeding database with test ambulances...")
                test_ambulances = [
                    ("DVG-AMB-001", "Rajesh Kumar", "+919876543210", 14.4732, 75.9260),
                    ("DVG-AMB-002", "Suresh Gowda", "+919876543211", 14.4510, 75.9190)
                ]
                db.executemany(
                    "INSERT OR IGNORE INTO ambulances (ambulance_id, driver_name, driver_phone, latitude, longitude) VALUES (?, ?, ?, ?, ?)",
                    test_ambulances
                )
                print("Database seeded with test data.")

            db.commit()
            print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database tables: {e}")

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

print(f"Using database: {DATABASE}")
print(f"Frontend directory: {FRONTEND_DIR}")

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # This enables column access by name
    return db

# Run initialization (must be after get_db is defined)
init_db_tables()

def query_db(query, args=(), one=False):
    try:
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None if one else []

def insert_db(query, args=()):
    try:
        db = get_db()
        cur = db.execute(query, args)
        db.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        db.rollback()
        return None

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Static file serving for assets
@app.route('/frontend/<path:filename>')
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# Root route
@app.route('/')
def root():
    return render_template('callcenter/index.html')

# Home route - Call Center Dashboard
@app.route('/callcenter')
def callcenter():
    return render_template('callcenter/index.html')

# Ambulance Driver App
@app.route('/api/ambulance/app')
def ambulance_app():
    return render_template('ambulance_app/index.html')

# Location Sharing Page
@app.route('/share-location/<location_link_id>')
def share_location_page(location_link_id):
    # Check if location link ID exists
    emergency_call = query_db('SELECT * FROM emergency_calls WHERE location_link_id = ?', 
                             [location_link_id], one=True)
    
    if not emergency_call:
        abort(404)
    
    return render_template('location_share/index.html', 
                          location_link_id=location_link_id,
                          emergency_call_id=emergency_call['id'])

# Simple test route
@app.route('/test')
def test():
    return jsonify({
        "status": "OK",
        "message": "Server is running correctly",
        "database": os.path.exists(DATABASE)
    })

# API Endpoints

# 1. Call Center API
@app.route('/api/callcenter/initiate-call', methods=['POST'])
def initiate_call():
    data = request.get_json()
    
    if not data or 'caller_phone' not in data:
        return jsonify({"success": False, "error": "Caller phone number is required"}), 400
    
    # Generate location sharing link ID
    location_link_id = str(uuid.uuid4())
    
    # Create emergency call record
    call_id = insert_db(
        'INSERT INTO emergency_calls (caller_phone, location_link_id, status) VALUES (?, ?, ?)',
        [data['caller_phone'], location_link_id, 'initiated']
    )
    
    if call_id is None:
        return jsonify({"success": False, "error": "Failed to create emergency call"}), 500
    
    # Generate location sharing URL
    base_url = request.host_url.rstrip('/')
    location_share_url = f"{base_url}/share-location/{location_link_id}"
    
    # Log for testing purposes
    print(f"INFO - New emergency call initiated for {data['caller_phone']}")
    print(f"INFO - Location sharing URL: {location_share_url}")
    
    # In a real app, send SMS here
    sms_sent = True  # Simulated
    
    return jsonify({
        "success": True,
        "emergency_call_id": call_id,
        "location_link_id": location_link_id,
        "location_share_url": location_share_url,
        "sms_sent": sms_sent
    })

@app.route('/api/callcenter/active-calls', methods=['GET'])
def get_active_calls():
    # Get all calls that are not completed
    active_calls = query_db('SELECT * FROM emergency_calls WHERE status != ? ORDER BY call_time DESC', ['completed'])
    
    # Convert to list of dictionaries
    calls = []
    for call in active_calls:
        calls.append(dict(call))
    
    return jsonify({
        "success": True,
        "calls": calls
    })

@app.route('/api/callcenter/call/<int:call_id>', methods=['GET'])
def get_call_details(call_id):
    call = query_db('SELECT * FROM emergency_calls WHERE id = ?', [call_id], one=True)
    
    if not call:
        return jsonify({"success": False, "error": "Call not found"}), 404
    
    # Get assigned ambulance details if available
    ambulance = None
    if call['assigned_ambulance_id']:
        ambulance = query_db(
            'SELECT * FROM ambulances WHERE id = ?', 
            [call['assigned_ambulance_id']], 
            one=True
        )
    
    call_dict = dict(call)
    if ambulance:
        call_dict['assigned_ambulance'] = dict(ambulance)
    
    return jsonify({
        "success": True,
        "call": call_dict
    })

@app.route('/api/callcenter/assign-ambulance/<int:call_id>', methods=['POST'])
def assign_ambulance(call_id):
    # Get emergency call
    call = query_db('SELECT * FROM emergency_calls WHERE id = ?', [call_id], one=True)
    
    if not call or not call['latitude'] or not call['longitude']:
        return jsonify({"success": False, "error": "Invalid emergency call or location not shared"}), 400
    
    # Get all available ambulances
    available_ambulances = query_db('SELECT * FROM ambulances WHERE is_available = 1')
    
    if not available_ambulances:
        return jsonify({"success": False, "error": "No ambulances available"}), 400
    
    # Find nearest ambulance (simplified)
    nearest_ambulance = available_ambulances[0]  # Just use first one for this simplified version
    
    # Calculate rough distance and ETA
    distance_km = 5.0  # Simplified
    eta_minutes = 15   # Simplified
    
    # Update emergency call with assigned ambulance
    db = get_db()
    db.execute(
        'UPDATE emergency_calls SET assigned_ambulance_id = ?, assigned_time = CURRENT_TIMESTAMP, status = ? WHERE id = ?',
        [nearest_ambulance['id'], 'assigned', call_id]
    )
    
    # Mark ambulance as unavailable
    db.execute(
        'UPDATE ambulances SET is_available = 0 WHERE id = ?',
        [nearest_ambulance['id']]
    )
    
    db.commit()
    
    # Emit socket event
    socketio.emit('assignment_update', {
        'emergency_call_id': call_id,
        'ambulance_id': nearest_ambulance['id']
    })
    
    return jsonify({
        "success": True,
        "ambulance_id": nearest_ambulance['ambulance_id'],
        "driver_name": nearest_ambulance['driver_name'],
        "distance_km": distance_km,
        "eta_minutes": eta_minutes
    })

@app.route('/api/callcenter/complete-emergency/<int:call_id>', methods=['POST'])
def complete_emergency(call_id):
    # Get emergency call
    call = query_db('SELECT * FROM emergency_calls WHERE id = ?', [call_id], one=True)
    
    if not call:
        return jsonify({"success": False, "error": "Emergency call not found"}), 404
    
    db = get_db()
    
    # Update emergency call status
    db.execute(
        'UPDATE emergency_calls SET status = ?, completion_time = CURRENT_TIMESTAMP WHERE id = ?',
        ['completed', call_id]
    )
    
    # Make ambulance available again if assigned
    if call['assigned_ambulance_id']:
        db.execute(
            'UPDATE ambulances SET is_available = 1 WHERE id = ?',
            [call['assigned_ambulance_id']]
        )
    
    db.commit()
    
    # Emit socket event
    socketio.emit('assignment_update', {
        'emergency_call_id': call_id,
        'completed': True
    })
    
    return jsonify({"success": True})

# 2. Location API
@app.route('/api/location/submit', methods=['POST'])
def submit_location():
    data = request.get_json()
    
    if not data or 'location_link_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    # Find the emergency call
    call = query_db(
        'SELECT * FROM emergency_calls WHERE location_link_id = ?',
        [data['location_link_id']], 
        one=True
    )
    
    if not call:
        return jsonify({"success": False, "error": "Invalid location link"}), 404
    
    # Simple address lookup (would use Nominatim in real app)
    address = "Near Davanagere, Karnataka, India"
    
    # Update the emergency call with location data
    db = get_db()
    db.execute(
        '''UPDATE emergency_calls 
           SET latitude = ?, longitude = ?, address = ?, 
               status = ?, location_shared_time = CURRENT_TIMESTAMP
           WHERE location_link_id = ?''',
        [data['latitude'], data['longitude'], address, 'location_shared', data['location_link_id']]
    )
    db.commit()
    
    # Emit socket event
    socketio.emit('location_update', {
        'emergency_call_id': call['id'],
        'latitude': data['latitude'],
        'longitude': data['longitude']
    })
    
    return jsonify({
        "success": True,
        "message": "Location shared successfully",
        "ambulance_assigned": False  # In a full implementation, you would auto-assign ambulance here
    })

# 3. Ambulance API
@app.route('/api/ambulance/login', methods=['POST'])
def ambulance_login():
    data = request.get_json()
    
    if not data or 'ambulance_id' not in data:
        return jsonify({"success": False, "error": "Ambulance ID is required"}), 400
    
    # Find the ambulance
    ambulance = query_db(
        'SELECT * FROM ambulances WHERE ambulance_id = ?',
        [data['ambulance_id']], 
        one=True
    )
    
    if not ambulance:
        return jsonify({"success": False, "error": "Invalid ambulance ID"}), 404
    
    return jsonify({
        "success": True,
        "ambulance": dict(ambulance)
    })

@app.route('/api/ambulance/register', methods=['POST'])
def register_ambulance():
    data = request.get_json()
    
    required_fields = ['ambulance_id', 'driver_name', 'driver_phone', 'latitude', 'longitude']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    
    # Check if ambulance already exists
    existing = query_db(
        'SELECT * FROM ambulances WHERE ambulance_id = ?',
        [data['ambulance_id']], 
        one=True
    )
    
    if existing:
        return jsonify({"success": False, "error": "Ambulance ID already registered"}), 400
    
    # Create new ambulance
    ambulance_id = insert_db(
        '''INSERT INTO ambulances 
           (ambulance_id, driver_name, driver_phone, latitude, longitude, is_available) 
           VALUES (?, ?, ?, ?, ?, 1)''',
        [data['ambulance_id'], data['driver_name'], data['driver_phone'], 
         data['latitude'], data['longitude']]
    )
    
    if not ambulance_id:
        return jsonify({"success": False, "error": "Failed to register ambulance (Database Error)"}), 500
    
    # Get the created ambulance
    ambulance = query_db(
        'SELECT * FROM ambulances WHERE id = ?',
        [ambulance_id], 
        one=True
    )
    
    if not ambulance:
         return jsonify({"success": False, "error": "Registered but failed to retrieve details"}), 500

    return jsonify({
        "success": True,
        "ambulance": dict(ambulance)
    })

@app.route('/api/ambulance/all', methods=['GET'])
def get_all_ambulances():
    ambulances = query_db('SELECT * FROM ambulances')
    
    return jsonify({
        "success": True,
        "ambulances": [dict(ambulance) for ambulance in ambulances]
    })

@app.route('/api/ambulance/get-assignment/<ambulance_id>', methods=['GET'])
def get_assignment(ambulance_id):
    # Find the ambulance
    ambulance = query_db(
        'SELECT * FROM ambulances WHERE ambulance_id = ?',
        [ambulance_id], 
        one=True
    )
    
    if not ambulance:
        return jsonify({"success": False, "error": "Invalid ambulance ID"}), 404
    
    # Find active emergency assignment
    emergency_call = query_db(
        'SELECT * FROM emergency_calls WHERE assigned_ambulance_id = ? AND status = ?',
        [ambulance['id'], 'assigned'],
        one=True
    )
    
    if not emergency_call:
        return jsonify({
            "success": True,
            "has_assignment": False
        })
    
    return jsonify({
        "success": True,
        "has_assignment": True,
        "emergency_call": dict(emergency_call)
    })

@app.route('/api/ambulance/mark-arrived', methods=['POST'])
def mark_arrived():
    data = request.get_json()
    
    if not data or 'ambulance_id' not in data or 'emergency_call_id' not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    # Find the ambulance
    ambulance = query_db(
        'SELECT * FROM ambulances WHERE ambulance_id = ?',
        [data['ambulance_id']], 
        one=True
    )
    
    if not ambulance:
        return jsonify({"success": False, "error": "Invalid ambulance ID"}), 404
    
    # Update emergency call
    db = get_db()
    db.execute(
        'UPDATE emergency_calls SET pickup_time = CURRENT_TIMESTAMP WHERE id = ?',
        [data['emergency_call_id']]
    )
    db.commit()
    
    return jsonify({"success": True})

@app.route('/api/ambulance/mark-completed', methods=['POST'])
def mark_completed():
    data = request.get_json()
    
    if not data or 'emergency_call_id' not in data:
        return jsonify({"success": False, "error": "Emergency call ID is required"}), 400
    
    # Get the emergency call
    call = query_db(
        'SELECT * FROM emergency_calls WHERE id = ?',
        [data['emergency_call_id']], 
        one=True
    )
    
    if not call:
        return jsonify({"success": False, "error": "Emergency call not found"}), 404
    
    db = get_db()
    
    # Update emergency call
    db.execute(
        'UPDATE emergency_calls SET status = ?, completion_time = CURRENT_TIMESTAMP WHERE id = ?',
        ['completed', data['emergency_call_id']]
    )
    
    # Update ambulance availability
    if call['assigned_ambulance_id']:
        db.execute(
            'UPDATE ambulances SET is_available = 1 WHERE id = ?',
            [call['assigned_ambulance_id']]
        )
    
    db.commit()
    
    # Emit socket event
    socketio.emit('assignment_update', {
        'emergency_call_id': call['id'],
        'completed': True
    })
    
    return jsonify({"success": True})

@app.route('/api/ambulance/update-location', methods=['POST'])
def update_location():
    data = request.get_json()
    
    if not data or 'ambulance_id' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    # Find the ambulance
    ambulance = query_db(
        'SELECT * FROM ambulances WHERE ambulance_id = ?',
        [data['ambulance_id']], 
        one=True
    )
    
    if not ambulance:
        return jsonify({"success": False, "error": "Invalid ambulance ID"}), 404
    
    # Update location
    db = get_db()
    db.execute(
        'UPDATE ambulances SET latitude = ?, longitude = ?, last_updated = CURRENT_TIMESTAMP WHERE ambulance_id = ?',
        [data['latitude'], data['longitude'], data['ambulance_id']]
    )
    db.commit()
    
    return jsonify({"success": True})

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected to Socket.IO')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from Socket.IO')

@socketio.on('location_shared')
def handle_location_shared(data):
    # Broadcast to call center dashboard
    socketio.emit('location_update', data)
    print(f"Location shared: {data}")

@socketio.on('ambulance_location_update')
def handle_ambulance_update(data):
    # Broadcast ambulance location updates to call center
    socketio.emit('ambulance_update', data)

# Main entry point
if __name__ == '__main__':
    print("\n==== Emergency Response System ====")
    print(f"Frontend directory: {FRONTEND_DIR}")
    print(f"Database: {DATABASE}")
    print("\nAccess points:")
    print("- Call Center Dashboard: http://localhost:5000/")
    print("- Ambulance Driver App: http://localhost:5000/api/ambulance/app")
    print("- Test endpoint: http://localhost:5000/test")
    print("\n=================================\n")
    socketio.run(app, host='0.0.0.0', debug=True)
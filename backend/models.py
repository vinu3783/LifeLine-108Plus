from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ambulance(db.Model):
    __tablename__ = 'ambulances'
    
    id = db.Column(db.Integer, primary_key=True)
    ambulance_id = db.Column(db.String(20), unique=True, nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    driver_phone = db.Column(db.String(15), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Ambulance('{self.ambulance_id}', '{self.driver_name}')"
    
    def to_dict(self):
        return {
            'id': self.id,
            'ambulance_id': self.ambulance_id,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'is_available': self.is_available,
            'last_updated': self.last_updated.isoformat()
        }

class EmergencyCall(db.Model):
    __tablename__ = 'emergency_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    caller_phone = db.Column(db.String(15), nullable=False)
    call_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='initiated')  # initiated, location_shared, assigned, completed
    location_link_id = db.Column(db.String(50), unique=True)
    
    # SMS protocol fields
    sms_location_code = db.Column(db.String(20), index=True, unique=True, nullable=True)
    sms_code_expiry = db.Column(db.DateTime, nullable=True)
    connectivity_status = db.Column(db.String(20), default='unknown')  # Options: unknown, online, offline, low_bandwidth
    location_method = db.Column(db.String(20), nullable=True)  # Options: web, app, sms, manual, estimated
    
    # Location details (will be updated once shared)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.Text, nullable=True)
    
    # Assignment details
    assigned_ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulances.id'), nullable=True)
    assigned_time = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    location_shared_time = db.Column(db.DateTime, nullable=True)
    pickup_time = db.Column(db.DateTime, nullable=True)
    completion_time = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    assigned_ambulance = db.relationship('Ambulance', backref='emergency_calls')
    
    def __repr__(self):
        return f"EmergencyCall('{self.id}', '{self.caller_phone}', '{self.status}')"
    
    def to_dict(self):
        return {
            'id': self.id,
            'caller_phone': self.caller_phone,
            'call_time': self.call_time.isoformat(),
            'status': self.status,
            'location_link_id': self.location_link_id,
            'sms_location_code': self.sms_location_code,
            'sms_code_expiry': self.sms_code_expiry.isoformat() if self.sms_code_expiry else None,
            'connectivity_status': self.connectivity_status,
            'location_method': self.location_method,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'assigned_ambulance_id': self.assigned_ambulance_id,
            'assigned_time': self.assigned_time.isoformat() if self.assigned_time else None,
            'location_shared_time': self.location_shared_time.isoformat() if self.location_shared_time else None,
            'pickup_time': self.pickup_time.isoformat() if self.pickup_time else None,
            'completion_time': self.completion_time.isoformat() if self.completion_time else None
        }
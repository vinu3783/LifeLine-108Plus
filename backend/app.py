import os
from flask import Flask, render_template
from flask_socketio import SocketIO

from backend.config import Config
from backend.models import db
from backend.routes.callcenter import callcenter_bp
from backend.routes.location import location_bp
from backend.routes.ambulance import ambulance_bp

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__, 
                static_folder='../frontend',
                template_folder='../frontend')
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Register blueprints
    app.register_blueprint(callcenter_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(ambulance_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Home route
    @app.route('/')
    def home():
        return render_template('callcenter/index.html')
    
    # Socket.IO events for real-time updates
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('location_shared')
    def handle_location_shared(data):
        # Broadcast to call center dashboard
        socketio.emit('location_update', data, broadcast=True)
    
    @socketio.on('ambulance_assigned')
    def handle_ambulance_assigned(data):
        # Broadcast to call center dashboard and ambulance app
        socketio.emit('assignment_update', data, broadcast=True)
    
    @socketio.on('ambulance_location_update')
    def handle_ambulance_update(data):
        # Broadcast ambulance location updates to call center
        socketio.emit('ambulance_update', data, broadcast=True)
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
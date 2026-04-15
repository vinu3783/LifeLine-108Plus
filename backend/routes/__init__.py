"""
Routes package for the Emergency Response System.
This package contains all the route blueprints for the Flask application.
"""

from flask import Blueprint

# Import route blueprints
from .callcenter import callcenter_bp
from .location import location_bp
from .ambulance import ambulance_bp

# List of all blueprints to be registered with the Flask app
all_blueprints = [
    callcenter_bp,
    location_bp,
    ambulance_bp
]

def register_all_blueprints(app):
    """
    Register all blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    for blueprint in all_blueprints:
        app.register_blueprint(blueprint)
    
    return app
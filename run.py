"""
Runner script for the Emergency Response System.
This script correctly handles Python module imports and runs the application.
"""

import os
from backend.app import create_app

if __name__ == '__main__':
    app, socketio = create_app()
    print("Starting Emergency Response System...")
    print("Access the Call Center Dashboard at: http://localhost:5000/")
    print("Access the Ambulance Driver App at: http://localhost:5000/api/ambulance/app")
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
import uuid
import requests
from geopy.distance import geodesic
from flask import current_app as app

class LocationService:
    def __init__(self):
        self.user_agent = app.config['NOMINATIM_USER_AGENT']
    
    def generate_location_link_id(self):
        """Generate a unique ID for location sharing link"""
        return str(uuid.uuid4())
    
    def get_location_share_url(self, location_link_id):
        """Generate a URL for the victim to share their location"""
        base_url = app.config['BASE_URL']
        return f"{base_url}/share-location/{location_link_id}"
    
    def get_address_from_coordinates(self, latitude, longitude):
        """Reverse geocoding using OpenStreetMap Nominatim API"""
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        headers = {'User-Agent': self.user_agent}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if 'display_name' in data:
                    return data['display_name']
            return "Address not found"
        except Exception as e:
            app.logger.error(f"Error in reverse geocoding: {str(e)}")
            return "Error getting address"
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in kilometers"""
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    
    def find_nearest_ambulance(self, victim_lat, victim_lon, ambulances):
        """Find the nearest available ambulance to the victim's location"""
        if not ambulances:
            return None
            
        nearest_ambulance = None
        min_distance = float('inf')
        
        for ambulance in ambulances:
            if not ambulance.is_available:
                continue
                
            distance = self.calculate_distance(
                victim_lat, victim_lon,
                ambulance.latitude, ambulance.longitude
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_ambulance = ambulance
        
        return nearest_ambulance, min_distance if nearest_ambulance else (None, None)
    
    def get_route_url(self, start_lat, start_lon, end_lat, end_lon):
        """Generate an OpenStreetMap route URL"""
        return f"https://www.openstreetmap.org/directions?engine=graphhopper_car&route={start_lat}%2C{start_lon}%3B{end_lat}%2C{end_lon}"
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-for-development')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///emergency_response.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Twilio settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'your_actual_sid_here')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your_actual_token_here')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', 'your_actual_phone_here')
    
    # OpenStreetMap settings
    NOMINATIM_USER_AGENT = os.getenv('NOMINATIM_USER_AGENT', 'emergency_response_system')
    
    # Application settings
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    EMERGENCY_NUMBER = os.getenv('EMERGENCY_NUMBER', '108')
    
    # SMS Protocol Settings
    SMS_ENABLED = os.getenv('SMS_ENABLED', 'True') == 'True'
    SMS_LOCATION_CODE_PREFIX = os.getenv('SMS_LOCATION_CODE_PREFIX', 'ERS-LOC')
    SMS_LOCATION_CODE_LENGTH = int(os.getenv('SMS_LOCATION_CODE_LENGTH', '6'))
    SMS_LOCATION_CODE_EXPIRY = int(os.getenv('SMS_LOCATION_CODE_EXPIRY', '1800'))  # 30 minutes in seconds
    SMS_REPLY_KEYWORD = os.getenv('SMS_REPLY_KEYWORD', 'LOCATION')
    
    # SMS Templates
    SMS_TEMPLATES = {
        'location_request': "Emergency Response: Reply to this message with {keyword} to automatically share your exact location. Your emergency code is: {code}",
        'location_received': "Thank you. Your location has been received. Emergency services have been dispatched to your location. Stay where you are if possible.",
        'location_error': "We couldn't detect your location. Please reply with {keyword} followed by your address or a nearby landmark.",
        'emergency_dispatch': "An ambulance ({ambulance_id}) has been dispatched to your location. ETA: approximately {eta_minutes} minutes. Please stay where you are.",
        'emergency_menu': "Emergency Response System Menu:\n1. HELP [location] - Report emergency\n2. STATUS - Check ambulance status\n3. CANCEL - Cancel emergency request\n4. INFO - About this service"
    }
from twilio.rest import Client
from flask import current_app as app

class SMSService:
    def __init__(self):
        self.account_sid = app.config['TWILIO_ACCOUNT_SID']
        self.auth_token = app.config['TWILIO_AUTH_TOKEN']
        self.twilio_phone = app.config['TWILIO_PHONE_NUMBER']
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_location_share_link(self, to_phone, location_link):
        """Send location sharing link to the victim"""
        message = (
            f"Emergency Response: Please click on this link to share your exact location: "
            f"{location_link}"
        )
        return self._send_sms(to_phone, message)
    
    def notify_ambulance_driver(self, driver_phone, victim_lat, victim_lon, address, route_url):
        """Notify ambulance driver about the emergency"""
        message = (
            f"EMERGENCY ALERT: You have been assigned to an emergency at: {address}. "
            f"Location coordinates: {victim_lat}, {victim_lon}. "
            f"Route: {route_url}"
        )
        return self._send_sms(driver_phone, message)
    
    def send_confirmation_to_victim(self, victim_phone, ambulance_id, driver_name, eta_minutes):
        """Send confirmation to the victim that ambulance is on the way"""
        message = (
            f"Emergency Response: Ambulance {ambulance_id} has been dispatched to your location. "
            f"Driver: {driver_name}. Estimated arrival time: {eta_minutes} minutes. "
            f"Stay calm and wait for help to arrive."
        )
        return self._send_sms(victim_phone, message)
    
    def _send_sms(self, to_phone, message):
        """Private method to send SMS using Twilio"""
        try:
            # Make sure phone number starts with "+"
            if not to_phone.startswith('+'):
                to_phone = '+' + to_phone
                
            message = self.client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=to_phone
            )
            return {"success": True, "message_sid": message.sid}
        except Exception as e:
            app.logger.error(f"Error sending SMS: {str(e)}")
            return {"success": False, "error": str(e)}
        

        # Add this method to the SMSService class
def send_location_share_link(self, to_phone, location_share_url):
    """Send location sharing link to the victim"""
    message = (
        f"Emergency Response: Please click on this link to share your exact location: "
        f"{location_share_url}"
    )
    return self._send_sms(to_phone, message)
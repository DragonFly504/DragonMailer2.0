# Azure Communication Services SMS Sender
# For sending SMS via Azure phone number

import json
import os
from pathlib import Path
from azure.communication.sms import SmsClient

# Default config path - use main app's config folder
DEFAULT_CONFIG = Path(__file__).parent.parent / "config" / "azure_sms.json"

class AzureSMSSender:
    """Send SMS via Azure Communication Services"""
    
    def __init__(self, config_file=None):
        """Initialize with Azure config"""
        if config_file is None:
            config_file = DEFAULT_CONFIG
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.connection_string = config.get('connection_string')
                self.from_number = config.get('phone_number') or config.get('sms_phone_number')
        else:
            raise FileNotFoundError(f"Configuration file {config_file} not found")
        
        if not self.from_number:
            raise ValueError("SMS phone number not configured. Run setup_azure_sms.ps1 first.")
        
        # Initialize SMS client
        self.client = SmsClient.from_connection_string(self.connection_string)
    
    def send_sms(self, to_number, message):
        """Send a single SMS"""
        try:
            # Ensure numbers are in E.164 format (+1234567890)
            if not to_number.startswith('+'):
                to_number = '+1' + to_number.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
            
            response = self.client.send(
                from_=self.from_number,
                to=[to_number],
                message=message
            )
            
            return {
                "success": True,
                "message_id": response[0].message_id,
                "status": response[0].successful
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_bulk_sms(self, recipients, message):
        """Send SMS to multiple recipients"""
        results = []
        
        for recipient in recipients:
            result = self.send_sms(recipient, message)
            results.append({
                "recipient": recipient,
                **result
            })
        
        return results

# Example usage
if __name__ == "__main__":
    try:
        sender = AzureSMSSender()
        
        # Send test SMS
        result = sender.send_sms(
            to_number="+1234567890",  # Replace with actual number
            message="Test SMS from Azure Communication Services"
        )
        
        print(f"SMS sent: {result}")
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use Azure SMS:")
        print("1. Run: python purchase_azure_sms.py")
        print("2. Purchase a phone number")
        print("3. Try again")

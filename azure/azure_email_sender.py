# Azure Communication Services Email Integration
# Add this to your messaging app for bulk email

import os
import json
from azure.communication.email import EmailClient

class AzureEmailSender:
    """Send emails via Azure Communication Services"""
    
    def __init__(self, config_file="azure_email_config.json"):
        """Initialize with Azure config"""
        # Load configuration
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.connection_string = config['connection_string']
                self.from_email = config['from_email']
        else:
            raise FileNotFoundError(f"Configuration file {config_file} not found")
        
        # Initialize email client
        self.client = EmailClient.from_connection_string(self.connection_string)
    
    def send_email(self, to_email, subject, body_html, body_text=None):
        """Send a single email"""
        try:
            message = {
                "senderAddress": self.from_email,
                "recipients": {
                    "to": [{"address": to_email}]
                },
                "content": {
                    "subject": subject,
                    "plainText": body_text or body_html,
                    "html": body_html
                }
            }
            
            poller = self.client.begin_send(message)
            result = poller.result()
            
            return {
                "success": True,
                "message_id": result['id'],
                "status": result['status']
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_bulk_email(self, recipients, subject, body_html, body_text=None):
        """Send emails to multiple recipients"""
        results = []
        
        for recipient in recipients:
            result = self.send_email(recipient, subject, body_html, body_text)
            results.append({
                "recipient": recipient,
                **result
            })
        
        return results

# Example usage
if __name__ == "__main__":
    # Initialize sender
    sender = AzureEmailSender()
    
    # Send test email to TTCPWORLDWIDE@Onlinefcu.com
    result = sender.send_email(
        to_email="TTCPWORLDWIDE@Onlinefcu.com",
        subject="Test from Azure Communication Services",
        body_html="<h1>Success!</h1><p>Your Azure Communication Services Email is working! This email won't go to spam.</p>",
        body_text="Success! Your Azure Communication Services Email is working!"
    )
    
    print(f"\nEmail sent: {result}\n")

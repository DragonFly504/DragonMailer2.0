"""
SMS Delivery Tracking System
Sends SMS and tracks delivery confirmation
"""

import smtplib
import imaplib
import email
import json
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path

# Config
TRACKING_FILE = Path(__file__).parent / "config" / "sms_tracking.json"

def load_tracking():
    """Load tracking data."""
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE) as f:
            return json.load(f)
    return {}

def save_tracking(data):
    """Save tracking data."""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def send_tracked_sms(
    smtp_server: str,
    smtp_port: int,
    email_address: str,
    password: str,
    phone: str,
    message: str,
    carrier: str = "auto"
):
    """Send SMS with tracking ID and log delivery attempt."""
    
    # Generate tracking ID
    tracking_id = str(uuid.uuid4())[:8]
    
    # Clean phone number
    clean_phone = ''.join(filter(str.isdigit, phone))[-10:]
    
    # Carrier gateways
    gateways = {
        "verizon": "vtext.com",
        "tmobile": "tmomail.net", 
        "att": "txt.att.net",
        "sprint": "messaging.sprintpcs.com",
        "auto": ["vtext.com", "tmomail.net", "txt.att.net", "messaging.sprintpcs.com"]
    }
    
    # Load existing tracking
    tracking = load_tracking()
    
    results = []
    
    try:
        # Connect to SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, password)
        
        # Determine gateways to try
        if carrier.lower() == "auto":
            gateway_list = gateways["auto"]
        else:
            gateway_list = [gateways.get(carrier.lower(), carrier)]
        
        for gateway in gateway_list:
            sms_email = f"{clean_phone}@{gateway}"
            msg_id = make_msgid(domain=email_address.split('@')[-1])
            
            try:
                # Create message with tracking info
                tracked_message = f"{message}\n[ID:{tracking_id}]"
                
                msg = MIMEText(tracked_message, 'plain')
                msg['From'] = email_address
                msg['To'] = sms_email
                msg['Subject'] = ''
                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = msg_id
                # Request delivery receipt
                msg['Disposition-Notification-To'] = email_address
                msg['Return-Receipt-To'] = email_address
                
                server.sendmail(email_address, sms_email, msg.as_string())
                
                # Log to tracking
                tracking[tracking_id] = {
                    "phone": phone,
                    "gateway": gateway,
                    "message": message,
                    "sent_at": datetime.now().isoformat(),
                    "status": "sent",
                    "smtp_account": email_address,
                    "message_id": msg_id,
                    "delivery_confirmed": False
                }
                
                results.append({
                    "tracking_id": tracking_id,
                    "gateway": gateway,
                    "success": True,
                    "message": f"Sent to {sms_email}"
                })
                
                print(f"✅ Sent to {sms_email}")
                print(f"   Tracking ID: {tracking_id}")
                
            except Exception as e:
                results.append({
                    "tracking_id": tracking_id,
                    "gateway": gateway,
                    "success": False,
                    "message": str(e)
                })
                print(f"❌ Failed {gateway}: {e}")
        
        server.quit()
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None
    
    # Save tracking
    save_tracking(tracking)
    
    return results

def check_delivery_status(email_address: str, password: str, imap_server: str = "outlook.office365.com"):
    """Check inbox for delivery receipts and bounce messages."""
    
    tracking = load_tracking()
    updates = []
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select('INBOX')
        
        # Search for delivery status notifications
        status, messages = mail.search(None, 'SUBJECT "Delivered"')
        
        for msg_id in messages[0].split():
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            email_body = email.message_from_bytes(msg_data[0][1])
            subject = email_body['Subject']
            
            # Check if this is a delivery confirmation
            if 'delivered' in subject.lower() or 'delivery' in subject.lower():
                # Try to match with tracked messages
                for track_id, data in tracking.items():
                    if not data.get('delivery_confirmed'):
                        data['delivery_confirmed'] = True
                        data['confirmed_at'] = datetime.now().isoformat()
                        updates.append(track_id)
        
        # Also check for bounces
        status, messages = mail.search(None, 'SUBJECT "Undeliverable"')
        
        for msg_id in messages[0].split():
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            email_body = email.message_from_bytes(msg_data[0][1])
            
            for track_id, data in tracking.items():
                if data.get('status') == 'sent' and not data.get('delivery_confirmed'):
                    # Mark as potentially bounced
                    data['status'] = 'bounced'
                    updates.append(track_id)
        
        mail.logout()
        
    except Exception as e:
        print(f"❌ IMAP error: {e}")
        return None
    
    # Save updates
    if updates:
        save_tracking(tracking)
    
    return updates

def get_tracking_report():
    """Generate tracking report."""
    tracking = load_tracking()
    
    print("\n" + "="*60)
    print("SMS DELIVERY TRACKING REPORT")
    print("="*60)
    
    total = len(tracking)
    confirmed = sum(1 for t in tracking.values() if t.get('delivery_confirmed'))
    pending = sum(1 for t in tracking.values() if t.get('status') == 'sent' and not t.get('delivery_confirmed'))
    bounced = sum(1 for t in tracking.values() if t.get('status') == 'bounced')
    
    print(f"\n📊 Summary:")
    print(f"   Total Sent: {total}")
    print(f"   ✅ Confirmed: {confirmed}")
    print(f"   ⏳ Pending: {pending}")
    print(f"   ❌ Bounced: {bounced}")
    
    print(f"\n📱 Recent Messages:")
    print("-"*60)
    
    for track_id, data in sorted(tracking.items(), key=lambda x: x[1].get('sent_at', ''), reverse=True)[:10]:
        status_icon = "✅" if data.get('delivery_confirmed') else ("❌" if data.get('status') == 'bounced' else "⏳")
        print(f"{status_icon} [{track_id}] {data.get('phone')} via {data.get('gateway')}")
        print(f"   Sent: {data.get('sent_at')}")
        if data.get('delivery_confirmed'):
            print(f"   Confirmed: {data.get('confirmed_at')}")
    
    print("="*60)
    return tracking

# Main test
if __name__ == "__main__":
    # Test with TTCPWORLDWIDE account
    results = send_tracked_sms(
        smtp_server="smtp.office365.com",
        smtp_port=587,
        email_address="TTCPWORLDWIDE@onlinefcu.com",
        password="Amachampion1@",
        phone="3213675667",
        message="Tracked SMS test from Dragon Mailer",
        carrier="auto"
    )
    
    print("\n" + "="*40)
    print("Checking for delivery confirmations...")
    
    # Note: Delivery confirmation via IMAP may take a few minutes
    # check_delivery_status("TTCPWORLDWIDE@onlinefcu.com", "Amachampion1@")
    
    # Show tracking report
    get_tracking_report()

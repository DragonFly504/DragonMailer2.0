"""
Streamlit Messaging App - Enhanced Email & SMS Sender
Features:
- Multiple SMTP configurations with upload/management
- Bulk recipient upload (CSV/TXT)
- HTML email body support
- File attachments
- Real-time sent message tracking
- Email read tracking (via tracking pixel)
"""

import streamlit as st
import smtplib
import json
import os
import csv
import io
import uuid
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Optional
import threading
import time

# Config file paths
CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(exist_ok=True)
SMTP_CONFIG_FILE = CONFIG_DIR / "smtp_configs.json"
RECIPIENTS_FILE = CONFIG_DIR / "recipients.json"
SENT_MESSAGES_FILE = CONFIG_DIR / "sent_messages.json"
TRACKING_FILE = CONFIG_DIR / "tracking.json"

# SMS Gateway domains for major carriers
SMS_GATEWAYS = {
    "AT&T": "txt.att.net",
    "T-Mobile": "tmomail.net",
    "Verizon": "vtext.com",
    "Sprint": "messaging.sprintpcs.com",
    "US Cellular": "email.uscc.net",
    "Metro PCS": "mymetropcs.com",
    "Boost Mobile": "sms.myboostmobile.com",
    "Cricket": "sms.cricketwireless.net",
    "Virgin Mobile": "vmobl.com",
    "Google Fi": "msg.fi.google.com",
    "Republic Wireless": "text.republicwireless.com",
    "Straight Talk": "vtext.com",
    "Mint Mobile": "tmomail.net",
    "Xfinity Mobile": "vtext.com",
    "Visible": "vtext.com",
}

# Default SMTP presets
DEFAULT_SMTP_PRESETS = {
    "Gmail": {
        "server": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Google Gmail - requires App Password (Security > 2-Step Verification > App Passwords)",
        "email": "",
        "password": ""
    },
    "Outlook/Hotmail (Personal)": {
        "server": "smtp-mail.outlook.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Microsoft Outlook.com / Hotmail / Live.com personal accounts",
        "email": "",
        "password": ""
    },
    "Office 365 (Business)": {
        "server": "smtp.office365.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Microsoft 365 Business accounts",
        "email": "",
        "password": ""
    },
    "Office 365 (No-Reply)": {
        "server": "smtp.office365.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "For automated/no-reply emails from your domain",
        "email": "",
        "password": ""
    },
    "Office 365 (Direct Send)": {
        "server": "yourdomain-com.mail.protection.outlook.com",
        "port": 25,
        "use_tls": True,
        "use_ssl": False,
        "description": "Office 365 Direct Send - replace server with your MX record",
        "email": "",
        "password": "",
        "no_auth": True
    },
    "Yahoo": {
        "server": "smtp.mail.yahoo.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Yahoo Mail - requires App Password (Account Security > Generate App Password)",
        "email": "",
        "password": ""
    },
    "iCloud": {
        "server": "smtp.mail.me.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Apple iCloud Mail - requires App-Specific Password (appleid.apple.com > Sign-In > App-Specific Passwords)",
        "email": "",
        "password": ""
    },
    "iCloud+ (Custom Domain)": {
        "server": "smtp.mail.me.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "iCloud+ with custom email domain - use your custom domain email",
        "email": "",
        "password": ""
    },
    "SendGrid": {
        "server": "smtp.sendgrid.net",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "SendGrid SMTP Relay - username is 'apikey', password is your API key",
        "email": "",
        "password": ""
    },
    "Mailgun": {
        "server": "smtp.mailgun.org",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Mailgun SMTP - use your domain's SMTP credentials",
        "email": "",
        "password": ""
    },
    "Amazon SES (US East)": {
        "server": "email-smtp.us-east-1.amazonaws.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Amazon SES US East (N. Virginia) - use SMTP credentials from SES console",
        "email": "",
        "password": ""
    },
    "Amazon SES (EU West)": {
        "server": "email-smtp.eu-west-1.amazonaws.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Amazon SES EU West (Ireland)",
        "email": "",
        "password": ""
    },
    "Zoho Mail": {
        "server": "smtp.zoho.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Zoho Mail - use your Zoho email and password",
        "email": "",
        "password": ""
    },
    "ProtonMail Bridge": {
        "server": "127.0.0.1",
        "port": 1025,
        "use_tls": False,
        "use_ssl": False,
        "description": "ProtonMail via Bridge app (must be running locally)",
        "email": "",
        "password": ""
    },
    "FastMail": {
        "server": "smtp.fastmail.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "FastMail - requires App Password",
        "email": "",
        "password": ""
    },
    "GoDaddy (Workspace)": {
        "server": "smtpout.secureserver.net",
        "port": 465,
        "use_tls": False,
        "use_ssl": True,
        "description": "GoDaddy Workspace Email",
        "email": "",
        "password": ""
    },
    "Brevo (Sendinblue)": {
        "server": "smtp-relay.brevo.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Brevo (formerly Sendinblue) - use your SMTP key",
        "email": "",
        "password": ""
    },
    "Postmark": {
        "server": "smtp.postmarkapp.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
        "description": "Postmark - use Server API Token as password",
        "email": "",
        "password": ""
    },
}


# ============== DATA MANAGEMENT FUNCTIONS ==============

def load_json_file(filepath: Path, default: dict | list = None) -> dict | list:
    """Load JSON data from file."""
    if default is None:
        default = {}
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default
    return default


def save_json_file(filepath: Path, data: dict | list):
    """Save data to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_smtp_configs() -> dict:
    """Load all SMTP configurations."""
    saved = load_json_file(SMTP_CONFIG_FILE, {})
    # Merge with defaults (saved takes priority)
    all_configs = DEFAULT_SMTP_PRESETS.copy()
    all_configs.update(saved)
    return all_configs


def save_smtp_config(name: str, config: dict):
    """Save an SMTP configuration."""
    configs = load_json_file(SMTP_CONFIG_FILE, {})
    configs[name] = config
    save_json_file(SMTP_CONFIG_FILE, configs)


def delete_smtp_config(name: str):
    """Delete an SMTP configuration."""
    configs = load_json_file(SMTP_CONFIG_FILE, {})
    if name in configs:
        del configs[name]
        save_json_file(SMTP_CONFIG_FILE, configs)


def load_recipient_lists() -> dict:
    """Load saved recipient lists."""
    return load_json_file(RECIPIENTS_FILE, {})


def save_recipient_list(name: str, recipients: list):
    """Save a recipient list."""
    lists = load_recipient_lists()
    lists[name] = {
        "recipients": recipients,
        "created": datetime.now().isoformat(),
        "count": len(recipients)
    }
    save_json_file(RECIPIENTS_FILE, lists)


def delete_recipient_list(name: str):
    """Delete a recipient list."""
    lists = load_recipient_lists()
    if name in lists:
        del lists[name]
        save_json_file(RECIPIENTS_FILE, lists)


def load_sent_messages() -> list:
    """Load sent message history."""
    return load_json_file(SENT_MESSAGES_FILE, [])


def save_sent_message(message_data: dict):
    """Save a sent message to history."""
    messages = load_sent_messages()
    messages.insert(0, message_data)  # Add to beginning
    # Keep only last 1000 messages
    messages = messages[:1000]
    save_json_file(SENT_MESSAGES_FILE, messages)


def load_tracking_data() -> dict:
    """Load email tracking data."""
    return load_json_file(TRACKING_FILE, {})


def update_tracking(tracking_id: str, event: str):
    """Update tracking data for an email."""
    tracking = load_tracking_data()
    if tracking_id not in tracking:
        tracking[tracking_id] = {"events": []}
    tracking[tracking_id]["events"].append({
        "event": event,
        "timestamp": datetime.now().isoformat()
    })
    save_json_file(TRACKING_FILE, tracking)


def generate_tracking_pixel(tracking_id: str, tracking_server_url: str = None) -> str:
    """Generate HTML tracking pixel."""
    if tracking_server_url:
        return f'<img src="{tracking_server_url}/track/{tracking_id}" width="1" height="1" style="display:none" alt="" />'
    # If no server, just add a placeholder comment
    return f'<!-- tracking-id: {tracking_id} -->'


# ============== EMAIL SENDING FUNCTIONS ==============

def send_email(
    smtp_server: str, 
    smtp_port: int, 
    sender_email: str,
    sender_password: str, 
    recipient_emails: list[str],
    subject: str, 
    message: str, 
    html_content: str = None,
    attachments: list = None,
    use_tls: bool = True,
    use_ssl: bool = False,
    enable_tracking: bool = False,
    progress_callback = None,
    no_auth: bool = False,
    sender_name: str = None
) -> list[dict]:
    """
    Send emails to multiple recipients with HTML and attachments support.
    
    Returns:
        list of dicts with results for each recipient
    """
    results = []
    total = len(recipient_emails)
    
    try:
        # Connect once for all recipients
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        # Skip authentication for Direct Send (Office 365)
        if not no_auth:
            server.login(sender_email, sender_password)
        
        for idx, recipient in enumerate(recipient_emails):
            recipient = recipient.strip()
            if not recipient:
                continue
            
            tracking_id = str(uuid.uuid4()) if enable_tracking else None
            
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                # Format From field with display name if provided
                if sender_name:
                    msg['From'] = f"{sender_name} <{sender_email}>"
                else:
                    msg['From'] = sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                
                # Add standard headers to improve deliverability
                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[-1] if '@' in sender_email else 'localhost')
                msg['Reply-To'] = sender_email
                
                # Only add tracking header if tracking is enabled (empty headers look suspicious)
                if tracking_id:
                    msg['X-Tracking-ID'] = tracking_id
                
                # Add plain text version
                msg.attach(MIMEText(message, 'plain'))
                
                # Add HTML version if provided
                if html_content:
                    html_body = html_content
                    # Add tracking pixel if enabled
                    if enable_tracking and tracking_id:
                        tracking_pixel = generate_tracking_pixel(tracking_id)
                        if '</body>' in html_body.lower():
                            html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
                        else:
                            html_body += tracking_pixel
                    msg.attach(MIMEText(html_body, 'html'))
                
                # Add attachments
                if attachments:
                    for attachment in attachments:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment['data'])
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{attachment["name"]}"'
                        )
                        msg.attach(part)
                
                server.sendmail(sender_email, recipient, msg.as_string())
                
                result = {
                    "recipient": recipient,
                    "success": True,
                    "message": "Sent successfully",
                    "tracking_id": tracking_id,
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                # Save to history
                save_sent_message({
                    **result,
                    "subject": subject,
                    "type": "email",
                    "smtp_server": smtp_server
                })
                
            except Exception as e:
                results.append({
                    "recipient": recipient,
                    "success": False,
                    "message": str(e),
                    "tracking_id": None,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Update progress
            if progress_callback:
                progress_callback((idx + 1) / total)
        
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        return [{"recipient": r.strip(), "success": False, "message": "Authentication failed", "timestamp": datetime.now().isoformat()} 
                for r in recipient_emails if r.strip()]
    except smtplib.SMTPException as e:
        return [{"recipient": r.strip(), "success": False, "message": f"SMTP error: {str(e)}", "timestamp": datetime.now().isoformat()} 
                for r in recipient_emails if r.strip()]
    except Exception as e:
        return [{"recipient": r.strip(), "success": False, "message": f"Error: {str(e)}", "timestamp": datetime.now().isoformat()} 
                for r in recipient_emails if r.strip()]
    
    return results


def send_sms_via_gateway(
    smtp_server: str, 
    smtp_port: int, 
    sender_email: str,
    sender_password: str, 
    phone_entries: list[tuple[str, str]],
    message: str, 
    use_tls: bool = True,
    use_ssl: bool = False,
    progress_callback = None
) -> list[dict]:
    """
    Send SMS to multiple phone numbers via carrier's email-to-SMS gateway.
    """
    results = []
    total = len(phone_entries)
    
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        server.login(sender_email, sender_password)
        
        for idx, (phone_number, carrier) in enumerate(phone_entries):
            phone_number = phone_number.strip()
            if not phone_number:
                continue
            
            try:
                clean_number = ''.join(filter(str.isdigit, phone_number))
                
                if len(clean_number) < 10:
                    results.append({
                        "recipient": phone_number,
                        "success": False,
                        "message": "Invalid phone number",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                clean_number = clean_number[-10:]
                gateway_domain = SMS_GATEWAYS.get(carrier)
                
                if not gateway_domain:
                    results.append({
                        "recipient": phone_number,
                        "success": False,
                        "message": f"Unknown carrier: {carrier}",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                sms_email = f"{clean_number}@{gateway_domain}"
                
                msg = MIMEText(message, 'plain')
                msg['From'] = sender_email
                msg['To'] = sms_email
                msg['Subject'] = ""
                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[-1] if '@' in sender_email else 'localhost')
                
                server.sendmail(sender_email, sms_email, msg.as_string())
                
                result = {
                    "recipient": phone_number,
                    "success": True,
                    "message": f"Sent to {sms_email}",
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                
                save_sent_message({
                    **result,
                    "type": "sms",
                    "carrier": carrier,
                    "smtp_server": smtp_server
                })
                
            except Exception as e:
                results.append({
                    "recipient": phone_number,
                    "success": False,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            
            if progress_callback:
                progress_callback((idx + 1) / total)
        
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        return [{"recipient": p[0].strip(), "success": False, "message": "Authentication failed", "timestamp": datetime.now().isoformat()} 
                for p in phone_entries if p[0].strip()]
    except Exception as e:
        return [{"recipient": p[0].strip(), "success": False, "message": f"Error: {str(e)}", "timestamp": datetime.now().isoformat()} 
                for p in phone_entries if p[0].strip()]
    
    return results


def inject_custom_css():
    st.markdown("""
        <style>
        /* Dragon Mailer - Premium Theme 2026 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Hide Streamlit Branding */
        #MainMenu, footer, header {visibility: hidden;}
        
        /* ========== MAIN BACKGROUND - CLEAN & VISIBLE ========== */
        
        .stApp {
            background: #1f1f1f;
        }
        
        /* Main content area */
        .main .block-container {
            max-width: 1100px;
            padding: 2rem 2rem 5rem 2rem;
            position: relative;
            z-index: 1;
        }
        
        /* Content cards/sections */
        .stTabs, .element-container, .stMarkdown {
            position: relative;
            z-index: 1;
        }
        
        /* ========== DRAGON LOGO ========== */
        
        /* Sidebar Dragon Logo Container */
        .dragon-logo-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1rem 0;
        }
        
        .dragon-icon {
            width: 90px;
            height: 90px;
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 0 15px rgba(249, 115, 22, 0.5));
        }
        
        .dragon-svg {
            width: 100%;
            height: 100%;
            filter: drop-shadow(0 4px 12px rgba(249, 115, 22, 0.4));
        }
        
        /* Dragon head - STATIC */
        .dragon-head {
            fill: #f97316;
        }
        
        /* Dragon horns - STATIC */
        .dragon-horn {
            fill: #ea580c;
        }
        
        /* Dragon pupils - STATIC */
        .dragon-pupil {
            fill: #1f2937;
        }
        
        /* Fire - STATIC */
        .dragon-fire {
            opacity: 1;
        }
        
        /* Dragon title styling - STATIC */
        .dragon-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: #fbbf24;
            text-shadow: 0 2px 20px rgba(249, 115, 22, 0.5);
            letter-spacing: 0.02em;
        }
        
        /* Main Header */
        .main-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
            padding: 1.5rem 2rem;
            background: linear-gradient(135deg, rgba(234, 88, 12, 0.2) 0%, rgba(251, 191, 36, 0.15) 50%, rgba(234, 88, 12, 0.2) 100%);
            border-radius: 20px;
            border: 1px solid rgba(249, 115, 22, 0.4);
            box-shadow: 0 8px 32px rgba(234, 88, 12, 0.25);
            backdrop-filter: blur(10px);
        }
        
        .main-title {
            font-size: 2.8rem !important;
            font-weight: 800 !important;
            color: #fbbf24 !important;
            -webkit-text-fill-color: #fbbf24 !important;
            margin: 0 !important;
            letter-spacing: -0.02em;
        }
        
        /* Tagline */
        .tagline {
            color: #ffffff !important;
            font-size: 1.1rem;
            margin-top: 0.5rem;
        }
        .tagline strong {
            color: #fbbf24 !important;
        }
        
        /* ========== END DRAGON LOGO ========== */

        /* Sidebar Styling - Clean Dark Theme */
        section[data-testid="stSidebar"] {
            background: #171717;
            border-right: 1px solid #3f3f46;
        }
        section[data-testid="stSidebar"] .stMarkdown, 
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {
            color: #ffffff !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: #3f3f46;
        }

        /* Headers */
        h1 {
            background: linear-gradient(135deg, #ea580c 0%, #f97316 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
        }
        /* Headers - Dark Theme - HIGH VISIBILITY */
        h2 {
            color: #ffffff !important;
            font-weight: 700;
            font-size: 1.35rem;
            margin-top: 1.5rem;
        }
        h3 {
            color: #fbbf24 !important;
            font-size: 1.05rem;
            font-weight: 600;
        }
        
        /* All text on dark background - HIGH VISIBILITY */
        .stMarkdown, .stMarkdown p, .stMarkdown span {
            color: #ffffff !important;
        }
        .stMarkdown strong, .stMarkdown b {
            color: #fbbf24 !important;
        }

        /* Tabs - Clean Dark Theme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background: #262626;
            padding: 8px;
            border-radius: 14px;
            border: 1px solid #3f3f46;
        }
        .stTabs [data-baseweb="tab"] {
            height: 44px;
            background-color: transparent;
            border-radius: 10px;
            border: none;
            color: #d4d4d4;
            font-weight: 500;
            font-size: 0.9rem;
            padding: 0 18px;
            transition: all 0.2s ease;
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #3f3f46;
            color: #ffffff;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #ea580c 0%, #f97316 100%) !important;
            color: #FFFFFF !important;
        }

        /* Input Fields - Dark Glass Style - HIGH VISIBILITY */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            border-radius: 10px !important;
            border: 1.5px solid #3f3f46 !important;
            padding: 0.7rem 1rem !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
            background: #262626 !important;
            color: #ffffff !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #f97316 !important;
            box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.3) !important;
        }
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: #a1a1aa !important;
        }
        
        /* Text input value */
        .stTextInput input {
            color: #ffffff !important;
        }
        .stTextArea textarea {
            color: #ffffff !important;
        }
        
        /* Select boxes - Warm Brown HIGH VISIBILITY */
        .stSelectbox > div > div {
            background: #3d2b1f !important;
            color: #ffffff !important;
            border: 1.5px solid #8b5a2b !important;
            border-radius: 10px !important;
        }
        .stSelectbox > div > div > div {
            color: #ffffff !important;
            background: transparent !important;
        }
        .stSelectbox svg {
            fill: #f97316 !important;
        }
        .stSelectbox [data-baseweb="select"] span {
            color: #ffffff !important;
        }
        .stSelectbox [data-baseweb="select"] {
            background: #3d2b1f !important;
        }
        
        /* Labels - HIGH VISIBILITY */
        .stTextInput label, .stSelectbox label, .stTextArea label {
            font-weight: 600 !important;
            color: #ffffff !important;
            font-size: 0.95rem !important;
            margin-bottom: 0.4rem !important;
        }

        /* Buttons - Clean Fire Style */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            padding: 0.7rem 1.75rem;
            border: none;
            transition: all 0.2s ease;
            background: linear-gradient(135deg, #ea580c 0%, #f97316 100%);
            color: white;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(234, 88, 12, 0.5), 0 0 30px rgba(249, 115, 22, 0.3);
        }
        .stButton > button:active {
            transform: translateY(0) scale(0.98);
        }
        
        /* Secondary Buttons */
        .stDownloadButton > button {
            background: #262626;
            color: #f97316;
            border: 1.5px solid #3f3f46;
        }
        .stDownloadButton > button:hover {
            background: #3f3f46;
            border-color: #f97316;
        }
        
        /* Expanders - Clean Dark Style */
        .streamlit-expanderHeader {
            background: #262626;
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid #3f3f46;
            padding: 0.85rem 1.1rem;
            color: #ffffff !important;
        }
        .streamlit-expanderHeader:hover {
            border-color: #f97316;
        }
        .streamlit-expanderContent {
            border: 1px solid #3f3f46;
            border-top: none;
            border-radius: 0 0 10px 10px;
            padding: 1.25rem;
            background: #1f1f1f;
        }
        
        /* Metrics / Stats - Clean Dark */
        div[data-testid="metric-container"] {
            background: #262626;
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #3f3f46;
        }
        div[data-testid="metric-container"] label {
            color: #a1a1aa !important;
            font-weight: 500 !important;
            font-size: 0.85rem !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #f97316 !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
        }
        
        /* Alerts - Clean Style */
        .stAlert {
            border-radius: 10px;
        }
        
        /* Success Message */
        .stSuccess {
            background: #14532d;
            color: #86efac;
            border: 1px solid #22c55e;
        }
        
        /* Error Message */  
        .stError {
            background: #7f1d1d;
            color: #fca5a5;
            border: 1px solid #ef4444;
        }
        
        /* Info Message */
        .stInfo {
            background: #78350f;
            color: #fde68a;
            border: 1px solid #f59e0b;
        }
        
        /* Warning */
        .stWarning {
            background: #7c2d12;
            color: #fed7aa;
            border: 1px solid #f97316;
        }
        
        /* Checkbox & Radio - HIGH VISIBILITY */
        .stCheckbox label span, .stRadio label span {
            font-weight: 500;
            color: #ffffff !important;
        }
        .stCheckbox label, .stRadio label {
            color: #ffffff !important;
        }
        .stCheckbox p, .stRadio p {
            color: #ffffff !important;
        }
        
        /* Dividers */
        hr {
            border: none;
            height: 1px;
            background: #3f3f46;
            margin: 1.5rem 0;
        }
        
        /* File Uploader - Warm Brown */
        .stFileUploader > div {
            border-radius: 10px;
            border: 2px dashed #8b5a2b;
            background: #3d2b1f !important;
            transition: all 0.2s ease;
        }
        .stFileUploader > div:hover {
            border-color: #f97316;
            background: #4a3728 !important;
        }
        .stFileUploader label {
            color: #ffffff !important;
        }
        .stFileUploader p, .stFileUploader span, .stFileUploader div {
            color: #ffffff !important;
        }
        .stFileUploader small {
            color: #d4a574 !important;
        }
        .stFileUploader button {
            background: #8b5a2b !important;
            color: #ffffff !important;
        }
        
        /* Progress Bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, #ea580c 0%, #f97316 100%);
            border-radius: 999px;
        }
        
        /* Scrollbar - Clean Dark */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #262626;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: #525252;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #f97316;
        }
        
        /* Data Tables - HIGH VISIBILITY */
        .stDataFrame {
            background: #262626 !important;
            border-radius: 10px;
            border: 1px solid #3f3f46;
        }
        .stDataFrame td, .stDataFrame th {
            color: #ffffff !important;
        }
        
        /* Column styling */
        div[data-testid="column"] {
            padding: 0.5rem;
        }
        
        /* Sub-header styling */
        .stSubheader, [data-testid="stSubheader"] {
            color: #f97316 !important;
        }
        
        /* Caption text */
        .stCaption, [data-testid="stCaption"] {
            color: #a1a1aa !important;
        }
        
        /* Number inputs */
        .stNumberInput label {
            color: #ffffff !important;
        }
        .stNumberInput input {
            background: #262626 !important;
            color: #ffffff !important;
            border: 1.5px solid #3f3f46 !important;
            border-radius: 10px !important;
        }
        
        /* Date inputs */
        .stDateInput label {
            color: #ffffff !important;
        }
        .stDateInput input {
            background: #262626 !important;
            color: #ffffff !important;
            border: 1.5px solid #3f3f46 !important;
        }
        
        /* Time inputs */
        .stTimeInput label {
            color: #ffffff !important;
        }
        .stTimeInput input {
            background: #262626 !important;
            color: #ffffff !important;
        }
        
        /* Multiselect - Warm Brown */
        .stMultiSelect label {
            color: #ffffff !important;
        }
        .stMultiSelect > div > div {
            background: #3d2b1f !important;
            color: #ffffff !important;
            border: 1.5px solid #8b5a2b !important;
            border-radius: 10px !important;
        }
        .stMultiSelect span {
            color: #ffffff !important;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background: #6b4423 !important;
            color: #ffffff !important;
        }
        
        /* Slider */
        .stSlider label {
            color: #ffffff !important;
        }
        .stSlider p {
            color: #ffffff !important;
        }
        
        /* Select slider */
        .stSelectSlider label {
            color: #ffffff !important;
        }
        
        /* Color picker */
        .stColorPicker label {
            color: #ffffff !important;
        }
        
        /* Text in expander content */
        .streamlit-expanderContent p,
        .streamlit-expanderContent span,
        .streamlit-expanderContent label,
        .streamlit-expanderContent div {
            color: #ffffff !important;
        }
        
        /* Code blocks */
        .stCodeBlock {
            background: #262626 !important;
        }
        
        /* JSON display */
        .stJson {
            background: #262626 !important;
            color: #f97316 !important;
        }
        
        /* Tabs content text */
        .stTabs [data-baseweb="tab-panel"] p,
        .stTabs [data-baseweb="tab-panel"] span,
        .stTabs [data-baseweb="tab-panel"] label {
            color: #ffffff !important;
        }
        
        /* Links */
        a {
            color: #f97316 !important;
        }
        a:hover {
            color: #fbbf24 !important;
        }
        
        /* Toast messages */
        .stToast {
            background: #262626 !important;
            color: #ffffff !important;
            border: 1px solid #3f3f46 !important;
        }
        
        /* Popover - Warm Brown */
        [data-baseweb="popover"] {
            background: #3d2b1f !important;
            border: 1px solid #8b5a2b !important;
        }
        [data-baseweb="popover"] * {
            color: #ffffff !important;
        }
        
        /* Select dropdown menu - Warm Brown */
        [data-baseweb="menu"] {
            background: #3d2b1f !important;
            border: 1px solid #8b5a2b !important;
        }
        [data-baseweb="menu"] li {
            color: #ffffff !important;
            background: #3d2b1f !important;
        }
        [data-baseweb="menu"] li:hover {
            background: #5c4033 !important;
        }
        [data-baseweb="menu"] li[aria-selected="true"] {
            background: #6b4423 !important;
        }
        
        /* Empty state text */
        .stEmpty {
            color: #d4d4d4 !important;
        }
        
        </style>
    """, unsafe_allow_html=True)


# ============== UI HELPER FUNCTIONS ==============

def parse_recipients_file(uploaded_file) -> list[str]:
    """Parse recipients from uploaded CSV or TXT file."""
    recipients = []
    content = uploaded_file.read().decode('utf-8')
    
    if uploaded_file.name.endswith('.csv'):
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            for cell in row:
                cell = cell.strip()
                if cell and '@' in cell:
                    recipients.append(cell)
    else:
        for line in content.split('\n'):
            for email in line.split(','):
                email = email.strip()
                if email and '@' in email:
                    recipients.append(email)
    
    return list(set(recipients))  # Remove duplicates


def parse_sms_recipients_file(uploaded_file) -> list[tuple[str, str]]:
    """Parse SMS recipients from uploaded CSV file (phone, carrier)."""
    recipients = []
    content = uploaded_file.read().decode('utf-8')
    
    reader = csv.reader(io.StringIO(content))
    for row in reader:
        if len(row) >= 2:
            phone = row[0].strip()
            carrier = row[1].strip()
            if phone and carrier in SMS_GATEWAYS:
                recipients.append((phone, carrier))
        elif len(row) == 1:
            phone = row[0].strip()
            if phone:
                recipients.append((phone, "AT&T"))  # Default carrier
    
    return recipients


# ============== MAIN APP ==============

def main():
    st.set_page_config(
        page_title="Dragon Mailer - Email & SMS",
        page_icon="🐉",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject Custom CSS
    inject_custom_css()
    
    # Initialize session states
    if 'sending_results' not in st.session_state:
        st.session_state.sending_results = []
    if 'current_smtp' not in st.session_state:
        st.session_state.current_smtp = None
    
    # Sidebar
    with st.sidebar:
        st.markdown('''
            <div class="dragon-logo-container">
                <div class="dragon-icon">
                    <svg viewBox="0 0 100 100" class="dragon-svg">
                        <!-- Dragon Head -->
                        <ellipse cx="50" cy="45" rx="25" ry="20" fill="#f97316" class="dragon-head"/>
                        <!-- Dragon Horns -->
                        <polygon points="30,30 25,15 35,28" fill="#ea580c" class="dragon-horn"/>
                        <polygon points="70,30 75,15 65,28" fill="#ea580c" class="dragon-horn"/>
                        <!-- Dragon Eyes -->
                        <ellipse cx="40" cy="40" rx="5" ry="6" fill="#fef3c7"/>
                        <ellipse cx="60" cy="40" rx="5" ry="6" fill="#fef3c7"/>
                        <circle cx="41" cy="41" r="2.5" fill="#1f2937" class="dragon-pupil"/>
                        <circle cx="61" cy="41" r="2.5" fill="#1f2937" class="dragon-pupil"/>
                        <!-- Dragon Nostrils -->
                        <ellipse cx="45" cy="52" rx="2" ry="1.5" fill="#c2410c"/>
                        <ellipse cx="55" cy="52" rx="2" ry="1.5" fill="#c2410c"/>
                        <!-- Fire Breath -->
                        <path d="M50,58 Q45,70 40,80 Q50,75 50,85 Q50,75 60,80 Q55,70 50,58" fill="url(#fireGradient)" class="dragon-fire"/>
                        <!-- Gradient for fire -->
                        <defs>
                            <linearGradient id="fireGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" style="stop-color:#f97316"/>
                                <stop offset="50%" style="stop-color:#fbbf24"/>
                                <stop offset="100%" style="stop-color:#fef3c7"/>
                            </linearGradient>
                        </defs>
                    </svg>
                </div>
                <div class="dragon-title">Dragon Mailer</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown("---")
        
        # Stats
        history = load_sent_messages()
        today = datetime.now().strftime("%Y-%m-%d")
        today_msgs = [m for m in history if m.get('timestamp', '').startswith(today)]
        
        col1, col2 = st.columns(2)
        col1.metric("Total Sent", len(history))
        col2.metric("Today", len(today_msgs))
        
        st.markdown("---")
        st.info("**Quick Tip:**\nUse the 'SMTP Settings' tab to configure your email providers before sending.")
        
        st.markdown("---")
        st.caption(f"v1.0.0 | {datetime.now().year}")

    # Tagline only - logo is in sidebar
    st.markdown("<p class='tagline'>🔥 <strong>Powerful Bulk Messaging Suite</strong> - Breathe fire into your email campaigns.</p>", unsafe_allow_html=True)
    
    # Create tabs
    tabs = st.tabs([
        "📤 Send Email",
        "📱 Send SMS", 
        "⚙️ SMTP Settings", 
        "👥 Recipients",
        "📊 History",
        "📈 Tracking",
        "ℹ️ Help"
    ])
    
    # ============== SEND EMAIL TAB ==============
    with tabs[0]:
        st.subheader("📤 Send Email")
        
        # SMTP Selection
        col1, col2 = st.columns([3, 1])
        with col1:
            smtp_configs = load_smtp_configs()
            smtp_names = list(smtp_configs.keys())
            selected_smtp = st.selectbox(
                "Select SMTP Configuration",
                smtp_names,
                key="email_smtp_select"
            )
        with col2:
            if selected_smtp:
                config = smtp_configs[selected_smtp]
                st.info(f"**{config['server']}:{config['port']}**")
        
        if selected_smtp:
            config = smtp_configs[selected_smtp]
            
            # Credentials (show saved or ask for new)
            with st.expander("🔐 Sender Credentials", expanded=True):
                saved_email = config.get('email', '')
                saved_pass = config.get('password', '')
                
                col1, col2 = st.columns(2)
                with col1:
                    sender_email = st.text_input(
                        "Sender Email",
                        value=saved_email,
                        placeholder="your.email@example.com",
                        key="email_sender"
                    )
                with col2:
                    sender_password = st.text_input(
                        "App Password",
                        value=saved_pass,
                        type="password",
                        key="email_password"
                    )
                
                # Sender Display Name
                sender_name = st.text_input(
                    "Sender Display Name (appears in recipient's inbox)",
                    value="",
                    placeholder="Your Name or Company",
                    key="sender_display_name"
                )
                
                save_creds = st.checkbox("Save credentials for this SMTP", value=bool(saved_email))
                if save_creds and sender_email and sender_password:
                    config['email'] = sender_email
                    config['password'] = sender_password
                    save_smtp_config(selected_smtp, config)
            
            # Recipients Section
            st.markdown("---")
            st.markdown("### 👥 Recipients")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Manual Entry**")
                recipients_text = st.text_area(
                    "Email Addresses (one per line or comma-separated)",
                    height=120,
                    key="manual_recipients",
                    placeholder="email1@example.com\nemail2@example.com"
                )
            
            with col2:
                st.markdown("**Upload Recipients**")
                uploaded_recipients = st.file_uploader(
                    "Upload CSV or TXT file",
                    type=['csv', 'txt'],
                    key="upload_recipients"
                )
                
                # Load saved lists
                saved_lists = load_recipient_lists()
                if saved_lists:
                    selected_list = st.selectbox(
                        "Or use saved list",
                        ["-- Select --"] + list(saved_lists.keys()),
                        key="saved_list_select"
                    )
                else:
                    selected_list = None
            
            # Combine all recipients
            all_recipients = []
            
            # From text input
            if recipients_text:
                for line in recipients_text.split('\n'):
                    for email in line.split(','):
                        email = email.strip()
                        if email and '@' in email:
                            all_recipients.append(email)
            
            # From uploaded file
            if uploaded_recipients:
                uploaded_list = parse_recipients_file(uploaded_recipients)
                all_recipients.extend(uploaded_list)
                st.success(f"📁 Loaded {len(uploaded_list)} recipients from file")
                
                # Option to save the list
                save_name = st.text_input("Save this list as:", key="save_uploaded_list")
                if save_name and st.button("💾 Save List"):
                    save_recipient_list(save_name, uploaded_list)
                    st.success(f"Saved '{save_name}' with {len(uploaded_list)} recipients")
            
            # From saved list
            if selected_list and selected_list != "-- Select --":
                list_data = saved_lists[selected_list]
                all_recipients.extend(list_data['recipients'])
                st.info(f"📋 Loaded {len(list_data['recipients'])} recipients from '{selected_list}'")
            
            # Remove duplicates
            all_recipients = list(set(all_recipients))
            st.caption(f"📬 **Total: {len(all_recipients)} unique recipient(s)**")
            
            # Message Content
            st.markdown("---")
            st.markdown("### ✉️ Message Content")
            
            subject = st.text_input("Subject", placeholder="Enter email subject", key="email_subject")
            
            # Content type selection
            content_type = st.radio(
                "Content Type",
                ["Plain Text", "HTML", "Both (HTML with plain text fallback)"],
                horizontal=True,
                key="content_type"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Plain Text Body**")
                plain_message = st.text_area(
                    "Plain text message",
                    height=200,
                    key="plain_body",
                    placeholder="Type your plain text message here...",
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("**HTML Body**")
                html_upload = st.file_uploader(
                    "Upload HTML file",
                    type=['html', 'htm'],
                    key="html_upload"
                )
                
                if html_upload:
                    html_content = html_upload.read().decode('utf-8')
                    st.success(f"📄 Loaded HTML file: {html_upload.name}")
                else:
                    html_content = st.text_area(
                        "Or write HTML directly",
                        height=150,
                        key="html_body",
                        placeholder="<html><body>Your HTML content...</body></html>",
                        label_visibility="collapsed"
                    )
            
            # Attachments
            st.markdown("---")
            st.markdown("### 📎 Attachments")
            
            attachments_files = st.file_uploader(
                "Upload attachments",
                type=None,  # Allow all file types
                accept_multiple_files=True,
                key="attachments"
            )
            
            if attachments_files:
                st.caption(f"📎 {len(attachments_files)} file(s) attached")
                for f in attachments_files:
                    st.markdown(f"- {f.name} ({f.size / 1024:.1f} KB)")
            
            # Options
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                enable_tracking = st.checkbox(
                    "🔍 Enable read tracking (adds tracking pixel)",
                    key="enable_tracking",
                    help="Adds an invisible pixel to track when emails are opened. Requires HTML content."
                )
            
            # Send Button
            st.markdown("---")
            if st.button("📤 Send Emails", type="primary", use_container_width=True, key="send_email_btn"):
                if not sender_email or not sender_password:
                    st.error("Please enter sender credentials.")
                elif not all_recipients:
                    st.error("Please add at least one recipient.")
                elif not plain_message and not html_content:
                    st.error("Please enter a message (plain text or HTML).")
                else:
                    # Prepare attachments
                    attachments = []
                    if attachments_files:
                        for f in attachments_files:
                            attachments.append({
                                "name": f.name,
                                "data": f.read()
                            })
                    
                    # Determine HTML content based on selection
                    final_html = None
                    if content_type in ["HTML", "Both (HTML with plain text fallback)"]:
                        final_html = html_content if html_content else None
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(pct):
                        progress_bar.progress(pct)
                        status_text.text(f"Sending... {int(pct * 100)}% ({int(pct * len(all_recipients))}/{len(all_recipients)})")
                    
                    status_text.text(f"Sending to {len(all_recipients)} recipients...")
                    
                    results = send_email(
                        smtp_server=config['server'],
                        smtp_port=config['port'],
                        sender_email=sender_email,
                        sender_password=sender_password,
                        recipient_emails=all_recipients,
                        subject=subject,
                        message=plain_message or "This email requires an HTML-capable email client.",
                        html_content=final_html,
                        attachments=attachments if attachments else None,
                        use_tls=config.get('use_tls', True),
                        use_ssl=config.get('use_ssl', False),
                        enable_tracking=enable_tracking,
                        progress_callback=update_progress,
                        no_auth=config.get('no_auth', False),
                        sender_name=sender_name
                    )
                    
                    progress_bar.progress(1.0)
                    
                    # Store results for display
                    st.session_state.sending_results = results
                    
                    # Summary
                    success_count = sum(1 for r in results if r['success'])
                    fail_count = len(results) - success_count
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully sent to {success_count} recipient(s)")
                    if fail_count > 0:
                        st.error(f"❌ Failed to send to {fail_count} recipient(s)")
                    
                    # Detailed results
                    with st.expander("📋 Detailed Results", expanded=True):
                        for result in results:
                            if result['success']:
                                st.markdown(f"✅ **{result['recipient']}**: {result['message']}")
                            else:
                                st.markdown(f"❌ **{result['recipient']}**: {result['message']}")
    
    # ============== SEND SMS TAB ==============
    with tabs[1]:
        st.subheader("📱 Send SMS")
        st.info("SMS messages are sent through carrier email-to-SMS gateways. Works for US carriers.")
        
        # SMTP Selection
        smtp_configs = load_smtp_configs()
        selected_smtp = st.selectbox(
            "Select SMTP Configuration",
            list(smtp_configs.keys()),
            key="sms_smtp_select"
        )
        
        if selected_smtp:
            config = smtp_configs[selected_smtp]
            
            # Credentials
            with st.expander("🔐 Sender Credentials", expanded=True):
                saved_email = config.get('email', '')
                saved_pass = config.get('password', '')
                
                col1, col2 = st.columns(2)
                with col1:
                    sender_email = st.text_input(
                        "Sender Email",
                        value=saved_email,
                        placeholder="your.email@example.com",
                        key="sms_sender"
                    )
                with col2:
                    sender_password = st.text_input(
                        "App Password",
                        value=saved_pass,
                        type="password",
                        key="sms_password"
                    )
            
            # SMS Recipients
            st.markdown("---")
            st.markdown("### 👥 Recipients")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Upload Recipients (CSV)**")
                st.caption("Format: phone_number, carrier (one per line)")
                uploaded_sms = st.file_uploader(
                    "Upload CSV",
                    type=['csv'],
                    key="upload_sms_recipients"
                )
            
            with col2:
                st.markdown("**Manual Entry**")
                if 'sms_entries' not in st.session_state:
                    st.session_state.sms_entries = [{"phone": "", "carrier": "AT&T"}]
            
            # Show SMS entries
            sms_recipients = []
            
            if uploaded_sms:
                sms_recipients = parse_sms_recipients_file(uploaded_sms)
                st.success(f"📁 Loaded {len(sms_recipients)} recipients from file")
            else:
                for i, entry in enumerate(st.session_state.sms_entries):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        phone = st.text_input(
                            f"Phone #{i+1}",
                            value=entry["phone"],
                            placeholder="(555) 123-4567",
                            key=f"sms_phone_{i}"
                        )
                    with col2:
                        carrier = st.selectbox(
                            f"Carrier #{i+1}",
                            list(SMS_GATEWAYS.keys()),
                            index=list(SMS_GATEWAYS.keys()).index(entry.get("carrier", "AT&T")),
                            key=f"sms_carrier_{i}"
                        )
                    with col3:
                        if i > 0:
                            if st.button("🗑️", key=f"sms_remove_{i}"):
                                st.session_state.sms_entries.pop(i)
                                st.rerun()
                    
                    if phone:
                        sms_recipients.append((phone, carrier))
                        st.session_state.sms_entries[i] = {"phone": phone, "carrier": carrier}
                
                if st.button("➕ Add Another"):
                    st.session_state.sms_entries.append({"phone": "", "carrier": "AT&T"})
                    st.rerun()
            
            st.caption(f"📱 **{len(sms_recipients)} recipient(s)**")
            
            # Message
            st.markdown("---")
            sms_message = st.text_area(
                "Message (160 chars max)",
                max_chars=160,
                height=100,
                key="sms_message",
                placeholder="Type your SMS message..."
            )
            st.caption(f"Characters: {len(sms_message)}/160")
            
            # Send
            if st.button("📤 Send SMS", type="primary", use_container_width=True, key="send_sms_btn"):
                if not sender_email or not sender_password:
                    st.error("Please enter sender credentials.")
                elif not sms_recipients:
                    st.error("Please add at least one recipient.")
                elif not sms_message:
                    st.error("Please enter a message.")
                else:
                    progress_bar = st.progress(0)
                    
                    def update_progress(pct):
                        progress_bar.progress(pct)
                    
                    results = send_sms_via_gateway(
                        smtp_server=config['server'],
                        smtp_port=config['port'],
                        sender_email=sender_email,
                        sender_password=sender_password,
                        phone_entries=sms_recipients,
                        message=sms_message,
                        use_tls=config.get('use_tls', True),
                        use_ssl=config.get('use_ssl', False),
                        progress_callback=update_progress
                    )
                    
                    progress_bar.progress(1.0)
                    
                    success_count = sum(1 for r in results if r['success'])
                    fail_count = len(results) - success_count
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully sent to {success_count} recipient(s)")
                    if fail_count > 0:
                        st.error(f"❌ Failed to send to {fail_count} recipient(s)")
                    
                    with st.expander("📋 Detailed Results", expanded=True):
                        for result in results:
                            if result['success']:
                                st.markdown(f"✅ **{result['recipient']}**: {result['message']}")
                            else:
                                st.markdown(f"❌ **{result['recipient']}**: {result['message']}")
    
    # ============== SMTP SETTINGS TAB ==============
    with tabs[2]:
        st.subheader("⚙️ SMTP Configuration Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Existing Configurations")
            smtp_configs = load_smtp_configs()
            custom_configs = load_json_file(SMTP_CONFIG_FILE, {})
            
            for name, config in smtp_configs.items():
                with st.expander(f"{'🔧' if name in custom_configs else '📦'} {name}"):
                    st.markdown(f"**Server:** `{config['server']}`")
                    st.markdown(f"**Port:** `{config['port']}`")
                    st.markdown(f"**TLS:** `{config.get('use_tls', True)}`")
                    st.markdown(f"**SSL:** `{config.get('use_ssl', False)}`")
                    if config.get('description'):
                        st.markdown(f"**Description:** {config['description']}")
                    if config.get('email'):
                        st.markdown(f"**Saved Email:** `{config['email']}`")
                    
                    if name in custom_configs:
                        if st.button(f"🗑️ Delete", key=f"delete_smtp_{name}"):
                            delete_smtp_config(name)
                            st.success(f"Deleted '{name}'")
                            st.rerun()
        
        with col2:
            st.markdown("### ➕ Add New SMTP Configuration")
            
            new_name = st.text_input("Configuration Name", placeholder="My SMTP Server")
            new_server = st.text_input("SMTP Server", placeholder="smtp.example.com")
            new_port = st.number_input("Port", value=587, min_value=1, max_value=65535)
            new_tls = st.checkbox("Use STARTTLS", value=True)
            new_ssl = st.checkbox("Use SSL/TLS (implicit)", value=False)
            new_desc = st.text_input("Description", placeholder="Optional description")
            new_email = st.text_input("Default Email", placeholder="Optional - save email")
            new_pass = st.text_input("Default Password", type="password", placeholder="Optional - save password")
            
            if st.button("💾 Save Configuration", type="primary"):
                if new_name and new_server:
                    save_smtp_config(new_name, {
                        "server": new_server,
                        "port": new_port,
                        "use_tls": new_tls,
                        "use_ssl": new_ssl,
                        "description": new_desc,
                        "email": new_email,
                        "password": new_pass
                    })
                    st.success(f"✅ Saved '{new_name}'!")
                    st.rerun()
                else:
                    st.error("Please enter a name and server.")
            
            st.markdown("---")
            st.markdown("### 📤 Import/Export SMTP Configs")
            
            uploaded_smtp = st.file_uploader("Import SMTP configs (JSON)", type=['json'], key="import_smtp")
            if uploaded_smtp:
                try:
                    imported = json.load(uploaded_smtp)
                    for name, config in imported.items():
                        save_smtp_config(name, config)
                    st.success(f"Imported {len(imported)} configuration(s)")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error importing: {e}")
            
            if st.button("📥 Export All SMTP Configs"):
                export_data = load_json_file(SMTP_CONFIG_FILE, {})
                st.download_button(
                    "Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name="smtp_configs.json",
                    mime="application/json"
                )
    
    # ============== RECIPIENTS TAB ==============
    with tabs[3]:
        st.subheader("👥 Recipient Lists Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Saved Recipient Lists")
            saved_lists = load_recipient_lists()
            
            if saved_lists:
                for name, data in saved_lists.items():
                    with st.expander(f"📁 {name} ({data['count']} recipients)"):
                        st.caption(f"Created: {data['created']}")
                        
                        # Show first 10 recipients
                        recipients = data['recipients'][:10]
                        for r in recipients:
                            st.markdown(f"- {r}")
                        if len(data['recipients']) > 10:
                            st.caption(f"... and {len(data['recipients']) - 10} more")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("📥 Export", key=f"export_list_{name}"):
                                csv_content = "\n".join(data['recipients'])
                                st.download_button(
                                    "Download CSV",
                                    data=csv_content,
                                    file_name=f"{name}.csv",
                                    mime="text/csv",
                                    key=f"download_{name}"
                                )
                        with col_b:
                            if st.button("🗑️ Delete", key=f"delete_list_{name}"):
                                delete_recipient_list(name)
                                st.success(f"Deleted '{name}'")
                                st.rerun()
            else:
                st.info("No saved recipient lists yet.")
        
        with col2:
            st.markdown("### ➕ Create New Recipient List")
            
            list_name = st.text_input("List Name", placeholder="My Subscribers")
            
            st.markdown("**Upload file or paste recipients:**")
            uploaded_list = st.file_uploader("Upload CSV/TXT", type=['csv', 'txt'], key="new_list_upload")
            
            manual_list = st.text_area(
                "Or enter manually",
                placeholder="email1@example.com\nemail2@example.com",
                height=150
            )
            
            if st.button("💾 Save Recipient List", type="primary"):
                recipients = []
                
                if uploaded_list:
                    recipients = parse_recipients_file(uploaded_list)
                
                if manual_list:
                    for line in manual_list.split('\n'):
                        for email in line.split(','):
                            email = email.strip()
                            if email and '@' in email:
                                recipients.append(email)
                
                recipients = list(set(recipients))
                
                if list_name and recipients:
                    save_recipient_list(list_name, recipients)
                    st.success(f"✅ Saved '{list_name}' with {len(recipients)} recipients")
                    st.rerun()
                else:
                    st.error("Please enter a name and at least one recipient.")
    
    # ============== MESSAGE HISTORY TAB ==============
    with tabs[4]:
        st.subheader("📊 Message History")
        
        messages = load_sent_messages()
        
        if messages:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_type = st.selectbox("Filter by type", ["All", "email", "sms"])
            with col2:
                filter_status = st.selectbox("Filter by status", ["All", "Success", "Failed"])
            with col3:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
            # Apply filters
            filtered = messages
            if filter_type != "All":
                filtered = [m for m in filtered if m.get('type') == filter_type]
            if filter_status == "Success":
                filtered = [m for m in filtered if m.get('success')]
            elif filter_status == "Failed":
                filtered = [m for m in filtered if not m.get('success')]
            
            st.markdown(f"**Showing {len(filtered)} of {len(messages)} messages**")
            
            # Display messages in a table-like format
            for msg in filtered[:100]:  # Show last 100
                timestamp = msg.get('timestamp', 'Unknown time')
                recipient = msg.get('recipient', 'Unknown')
                msg_type = msg.get('type', 'email').upper()
                success = msg.get('success', False)
                status_icon = "✅" if success else "❌"
                
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                with col1:
                    st.markdown(f"**{msg_type}**")
                with col2:
                    st.markdown(f"{recipient}")
                with col3:
                    st.markdown(f"{status_icon} {msg.get('message', '')[:30]}")
                with col4:
                    st.caption(timestamp[:19] if len(timestamp) > 19 else timestamp)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export History"):
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(messages, indent=2),
                        file_name="message_history.json",
                        mime="application/json"
                    )
            with col2:
                if st.button("🗑️ Clear History"):
                    save_json_file(SENT_MESSAGES_FILE, [])
                    st.success("History cleared!")
                    st.rerun()
        else:
            st.info("No messages sent yet. Start sending to see history here!")
    
    # ============== TRACKING TAB ==============
    with tabs[5]:
        st.subheader("📈 Email Tracking")
        
        st.warning("""
        ⚠️ **Email Read Tracking Limitations:**
        
        - Tracking requires the email to be opened with images enabled
        - Many email clients block tracking pixels by default
        - This feature requires a tracking server to fully work
        - For full tracking, you would need to host a web server that logs when the tracking pixel is loaded
        
        **Current Implementation:** Tracking IDs are generated and stored, but actual read events require external server setup.
        """)
        
        tracking_data = load_tracking_data()
        
        if tracking_data:
            st.markdown(f"**{len(tracking_data)} tracked emails**")
            
            for tracking_id, data in list(tracking_data.items())[:50]:
                events = data.get('events', [])
                with st.expander(f"📧 {tracking_id[:8]}... ({len(events)} events)"):
                    for event in events:
                        st.markdown(f"- **{event['event']}** at {event['timestamp']}")
        else:
            st.info("No tracking data yet. Enable tracking when sending emails to see data here.")
        
        st.markdown("---")
        st.markdown("""
        ### 🔧 Setting Up Full Email Tracking
        
        To enable actual read tracking, you would need to:
        
        1. **Set up a tracking server** (e.g., Flask/FastAPI app)
        2. **Create an endpoint** that returns a 1x1 transparent pixel
        3. **Log the request** when the pixel is loaded
        4. **Update the tracking pixel URL** in the app
        
        Example tracking endpoint:
        ```python
        @app.get("/track/{tracking_id}")
        def track(tracking_id: str):
            # Log the open event
            update_tracking(tracking_id, "opened")
            # Return 1x1 transparent GIF
            return Response(content=TRANSPARENT_GIF, media_type="image/gif")
        ```
        """)
    
    # ============== HELP TAB ==============
    with tabs[6]:
        st.subheader("ℹ️ Help & Documentation")
        
        st.markdown("""
        ### 📧 Email Features
        
        - **Multiple SMTP Servers**: Add and manage multiple SMTP configurations
        - **Bulk Recipients**: Upload CSV/TXT files or paste multiple emails
        - **HTML Emails**: Upload HTML files or write HTML directly
        - **Attachments**: Attach multiple files to your emails
        - **Tracking**: Add tracking pixels to monitor email opens
        
        ### 📱 SMS Features
        
        - Send SMS via carrier email-to-SMS gateways
        - Bulk upload recipients with carriers
        - Works with major US carriers
        
        ### 📁 File Formats
        
        **Email Recipients (CSV/TXT):**
        ```
        email1@example.com
        email2@example.com, email3@example.com
        ```
        
        **SMS Recipients (CSV):**
        ```
        5551234567, AT&T
        5559876543, T-Mobile
        ```
        
        ### 🔐 Security Notes
        
        - Use **App Passwords** for Gmail, Yahoo, etc.
        - Credentials can be saved (stored locally in config files)
        - All data is stored locally in the `config` folder
        
        ### 📋 Carrier Gateway Reference
        """)
        
        cols = st.columns(2)
        carriers = list(SMS_GATEWAYS.items())
        mid = len(carriers) // 2
        with cols[0]:
            for carrier_name, domain in carriers[:mid]:
                st.markdown(f"- **{carrier_name}**: `[phone]@{domain}`")
        with cols[1]:
            for carrier_name, domain in carriers[mid:]:
                st.markdown(f"- **{carrier_name}**: `[phone]@{domain}`")


if __name__ == "__main__":
    main()

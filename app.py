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
from typing import Union, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid
from pathlib import Path
import threading
import time
import hashlib
import re
import random
import string

# Azure Communication Services for SMS
try:
    from azure.communication.sms import SmsClient
    AZURE_SMS_AVAILABLE = True
except ImportError:
    AZURE_SMS_AVAILABLE = False

# Jelly Components for enhanced Neon Jelly theme
try:
    from jelly_components import jelly_progress, jelly_slider_display, jelly_loading, jelly_metric
    JELLY_AVAILABLE = True
except ImportError:
    JELLY_AVAILABLE = False

# Config file paths
CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(exist_ok=True)
SMTP_CONFIG_FILE = CONFIG_DIR / "smtp_configs.json"
RECIPIENTS_FILE = CONFIG_DIR / "recipients.json"
SENT_MESSAGES_FILE = CONFIG_DIR / "sent_messages.json"
TRACKING_FILE = CONFIG_DIR / "tracking.json"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
SCHEDULED_FILE = CONFIG_DIR / "scheduled_tasks.json"
AZURE_SMS_CONFIG_FILE = CONFIG_DIR / "azure_sms.json"
USERS_FILE = CONFIG_DIR / "users.json"

# Default app settings - Multi-user enabled by default for security
DEFAULT_SETTINGS = {
    "theme": "Dragon Dark",  # Default theme
    "login_enabled": True,  # Login required by default
    "password_hash": "",  # SHA256 hash of password (legacy single-user)
    "multi_user_enabled": True,  # Multi-user mode enabled by default
    "session_timeout": 3600,  # 1 hour
}

# Available themes
THEMES = {
    "Dragon Dark": {"icon": "🐉", "type": "dark"},
    "Dragon Light": {"icon": "🐉", "type": "light"},
    "SecureMail Pro": {"icon": "🔒", "type": "dark"},
    "Midnight Blue": {"icon": "🌙", "type": "dark"},
    "Ocean Breeze": {"icon": "🌊", "type": "light"},
    "Forest Green": {"icon": "🌲", "type": "dark"},
    "Sunset Orange": {"icon": "🌅", "type": "light"},
    "Purple Haze": {"icon": "💜", "type": "dark"},
    "Rose Gold": {"icon": "🌸", "type": "light"},
    "Cyber Neon": {"icon": "💚", "type": "dark"},
    "Arctic Ice": {"icon": "❄️", "type": "light"},
    "Neon Jelly": {"icon": "🟢", "type": "dark"},
    "Glass": {"icon": "🔮", "type": "dark"},
}

# SMS Gateway domains for major carriers
SMS_GATEWAYS = {
    "Auto (Try All)": "auto",  # Special: will try all major carriers
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

# Primary gateways to try for Auto mode (most common US carriers)
AUTO_SMS_GATEWAYS = [
    "vtext.com",       # Verizon (largest)
    "tmomail.net",     # T-Mobile (2nd largest)
    "txt.att.net",     # AT&T (3rd largest)
    "messaging.sprintpcs.com",  # Sprint/T-Mobile
]

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

def load_json_file(filepath: Path, default: Union[dict, list] = None) -> Union[dict, list]:
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


def save_json_file(filepath: Path, data: Union[dict, list]):
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


# Azure SMS Configuration Functions
def load_azure_sms_config() -> dict:
    """Load Azure SMS configuration."""
    return load_json_file(AZURE_SMS_CONFIG_FILE, {})


def save_azure_sms_config(config: dict):
    """Save Azure SMS configuration."""
    save_json_file(AZURE_SMS_CONFIG_FILE, config)


def send_sms_via_azure(
    connection_string: str,
    from_number: str,
    phone_numbers: list,
    message: str,
    progress_callback=None
) -> tuple:
    """
    Send SMS via Azure Communication Services.
    Returns tuple of (success_count, failed_count, results_list)
    """
    results = []
    success_count = 0
    failed_count = 0
    
    if not AZURE_SMS_AVAILABLE:
        for phone in phone_numbers:
            results.append({
                "recipient": phone,
                "success": False,
                "message": "Azure SMS SDK not installed. Run: pip install azure-communication-sms",
                "timestamp": datetime.now().isoformat()
            })
        return (0, len(phone_numbers), results)
    
    try:
        sms_client = SmsClient.from_connection_string(connection_string)
        total = len(phone_numbers)
        
        for idx, phone in enumerate(phone_numbers):
            phone = phone.strip()
            if not phone:
                continue
            
            # Ensure phone has country code
            clean = ''.join(filter(str.isdigit, phone))
            if len(clean) == 10:
                phone = '+1' + clean
            elif not phone.startswith('+'):
                phone = '+' + clean
            
            try:
                response = sms_client.send(
                    from_=from_number,
                    to=[phone],
                    message=message
                )
                
                for sms_response in response:
                    if sms_response.successful:
                        success_count += 1
                        results.append({
                            "recipient": phone,
                            "success": True,
                            "message": f"Azure SMS sent (ID: {sms_response.message_id})",
                            "type": "azure_sms",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        failed_count += 1
                        results.append({
                            "recipient": phone,
                            "success": False,
                            "message": sms_response.error_message or "Failed",
                            "timestamp": datetime.now().isoformat()
                        })
                
                # Small delay between messages
                time.sleep(0.5)
                
                if progress_callback:
                    progress_callback(idx + 1, total, f"Sent {idx + 1}/{total}")
                    
            except Exception as e:
                failed_count += 1
                results.append({
                    "recipient": phone,
                    "success": False,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
    except Exception as e:
        for phone in phone_numbers:
            results.append({
                "recipient": phone,
                "success": False,
                "message": f"Connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        return (0, len(phone_numbers), results)
    
    return (success_count, failed_count, results)


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


# ============== SETTINGS & AUTHENTICATION FUNCTIONS ==============

def load_settings() -> dict:
    """Load app settings."""
    settings = load_json_file(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    # Ensure all default keys exist
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
    return settings


def save_settings(settings: dict):
    """Save app settings."""
    save_json_file(SETTINGS_FILE, settings)


def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash."""
    return hash_password(password) == stored_hash


# ============== MULTI-USER MANAGEMENT ==============

def load_users() -> dict:
    """Load users from file."""
    default_users = {
        "admin": {
            "password_hash": hash_password("WelcomePassword1@"),  # Default admin password - change after first login!
            "role": "admin",
            "created": datetime.now().isoformat(),
            "last_login": None
        }
    }
    return load_json_file(USERS_FILE, default_users)


def save_users(users: dict):
    """Save users to file."""
    save_json_file(USERS_FILE, users)


def create_user(username: str, password: str, role: str = "user") -> tuple[bool, str]:
    """Create a new user. Returns (success, message)."""
    users = load_users()
    
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters"
    
    if username.lower() in [u.lower() for u in users.keys()]:
        return False, "Username already exists"
    
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created": datetime.now().isoformat(),
        "last_login": None
    }
    save_users(users)
    return True, f"User '{username}' created successfully"


def delete_user(username: str, current_user: str) -> tuple[bool, str]:
    """Delete a user. Returns (success, message)."""
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    if username == current_user:
        return False, "Cannot delete your own account"
    
    if username == "admin":
        return False, "Cannot delete the admin account"
    
    del users[username]
    save_users(users)
    return True, f"User '{username}' deleted"


def change_user_password(username: str, new_password: str) -> tuple[bool, str]:
    """Change a user's password. Returns (success, message)."""
    users = load_users()
    
    if username not in users:
        return False, "User not found"
    
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters"
    
    users[username]["password_hash"] = hash_password(new_password)
    save_users(users)
    return True, "Password changed successfully"


def authenticate_user(username: str, password: str) -> tuple[bool, str, str]:
    """Authenticate a user. Returns (success, message, role)."""
    users = load_users()
    
    if username not in users:
        return False, "Invalid username or password", ""
    
    user = users[username]
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password", ""
    
    # Update last login
    users[username]["last_login"] = datetime.now().isoformat()
    save_users(users)
    
    return True, "Login successful", user.get("role", "user")


def check_login() -> bool:
    """Check if user is logged in. Returns True if access granted."""
    settings = load_settings()
    
    # If login not enabled, always grant access
    if not settings.get("login_enabled", False):
        return True
    
    # Check if already authenticated in session
    if st.session_state.get("authenticated", False):
        return True
    
    return False


def show_login_page():
    """Display centered glass login card with feature tiles."""
    settings = load_settings()
    multi_user = settings.get("multi_user_enabled", False)
    current_theme = settings.get("theme", "Dragon Dark")
    
    # Get theme accent color
    theme_accents = {
        "Dragon Dark": "#ff6b35", "Classic Light": "#2563eb", "Warm Ember": "#f97316",
        "Midnight Blue": "#3b82f6", "Ocean Breeze": "#0ea5e9", "Forest Green": "#22c55e",
        "Sunset Orange": "#f97316", "Purple Haze": "#a855f7", "Rose Gold": "#ec4899",
        "Cyber Neon": "#00ff88", "Arctic Ice": "#06b6d4", "Neon Jelly": "#c8ff00",
        "Glass": "#60a5fa",
    }
    accent = theme_accents.get(current_theme, "#ff6b35")
    
    # Beautiful background gradients that work well with glass effect
    # Each entry: (background_gradient, orb1_color, orb2_color, orb3_color)
    LOGIN_BACKGROUNDS = [
        # 1. Deep Ocean Night
        ("linear-gradient(135deg, #0d1b2a 0%, #1b263b 30%, #415a77 60%, #778da9 100%)", 
         "#3b82f6", "#667eea", "#11998e"),
        # 2. Purple Nebula
        ("linear-gradient(135deg, #1a0533 0%, #2d1b4e 25%, #4a2c7a 50%, #7c3aed 80%, #a855f7 100%)",
         "#a855f7", "#7c3aed", "#c084fc"),
        # 3. Aurora Borealis
        ("linear-gradient(135deg, #0f0c29 0%, #302b63 40%, #24243e 70%, #1a1a2e 100%)",
         "#00d4ff", "#7c3aed", "#00ff88"),
        # 4. Sunset Blaze
        ("linear-gradient(135deg, #1f1c2c 0%, #3a1c71 25%, #d76d77 60%, #ffaf7b 100%)",
         "#ff6b35", "#d76d77", "#ffaf7b"),
        # 5. Midnight Rose
        ("linear-gradient(135deg, #16141c 0%, #2c1e3d 30%, #4a2040 60%, #7c2d4d 100%)",
         "#ec4899", "#be185d", "#f472b6"),
        # 6. Deep Space
        ("linear-gradient(135deg, #000428 0%, #0a1628 30%, #1a2a4a 60%, #004e92 100%)",
         "#0ea5e9", "#3b82f6", "#06b6d4"),
        # 7. Emerald Forest
        ("linear-gradient(135deg, #0a1a10 0%, #132a1a 30%, #1e4d2b 60%, #2d6a4f 100%)",
         "#22c55e", "#059669", "#10b981"),
        # 8. Royal Purple
        ("linear-gradient(135deg, #150030 0%, #2a0a4a 30%, #4c1d6e 60%, #6b2d8a 100%)",
         "#9333ea", "#7c3aed", "#a855f7"),
        # 9. Warm Amber
        ("linear-gradient(135deg, #1a1005 0%, #2d1a0a 30%, #4a2810 60%, #6b3810 100%)",
         "#f97316", "#ea580c", "#fbbf24"),
        # 10. Cyber Pink
        ("linear-gradient(135deg, #1a0a1a 0%, #2d1030 30%, #4a1a4a 60%, #6b2060 100%)",
         "#ec4899", "#f472b6", "#db2777"),
        # 11. Arctic Night
        ("linear-gradient(135deg, #0a1520 0%, #0f2030 30%, #1a3a50 60%, #2a5a70 100%)",
         "#06b6d4", "#0ea5e9", "#22d3ee"),
        # 12. Volcano
        ("linear-gradient(135deg, #1a0505 0%, #2d0a0a 30%, #4a1010 50%, #6b1a1a 70%, #8b2020 100%)",
         "#ef4444", "#dc2626", "#f97316"),
        # 13. Mystic Violet
        ("linear-gradient(135deg, #0f0a20 0%, #1a1040 30%, #2a1a60 50%, #3a2480 70%, #4a2ea0 100%)",
         "#8b5cf6", "#a78bfa", "#7c3aed"),
        # 14. Teal Dreams
        ("linear-gradient(135deg, #021010 0%, #052020 30%, #0a3a3a 50%, #0f5050 70%, #147070 100%)",
         "#14b8a6", "#2dd4bf", "#0d9488"),
        # 15. Golden Hour
        ("linear-gradient(135deg, #1a1000 0%, #2d1a00 30%, #4a2a00 50%, #6b4000 70%, #8b5500 100%)",
         "#fbbf24", "#f59e0b", "#eab308"),
        # 16. Neon Night
        ("linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 30%, #16213e 60%, #0f3460 100%)",
         "#00ff88", "#00d4ff", "#ff006e"),
        # 17. Berry Bliss
        ("linear-gradient(135deg, #1a0520 0%, #2d0a3a 30%, #4a1050 60%, #6b1a70 100%)",
         "#e879f9", "#d946ef", "#a855f7"),
        # 18. Ocean Abyss
        ("linear-gradient(135deg, #000510 0%, #001020 30%, #002040 50%, #003060 70%, #004080 100%)",
         "#0284c7", "#0369a1", "#0ea5e9"),
        # 19. Crimson Dusk
        ("linear-gradient(135deg, #150505 0%, #2a0a0a 30%, #400f0f 50%, #5a1515 70%, #701a1a 100%)",
         "#dc2626", "#b91c1c", "#f87171"),
        # 20. Jade Garden
        ("linear-gradient(135deg, #001510 0%, #002a1a 30%, #004030 50%, #005a40 70%, #007a50 100%)",
         "#10b981", "#059669", "#34d399"),
    ]
    
    # Store background choice in session state (only changes on page reload/refresh)
    if "login_bg_index" not in st.session_state:
        st.session_state.login_bg_index = random.randint(0, len(LOGIN_BACKGROUNDS) - 1)
    
    bg_choice = LOGIN_BACKGROUNDS[st.session_state.login_bg_index]
    bg_gradient = bg_choice[0]
    orb1_color = bg_choice[1]
    orb2_color = bg_choice[2]
    orb3_color = bg_choice[3]
    
    # Centered Glass Login CSS
    st.markdown(f"""
        <style>
            /* ========== FULLSCREEN NO SCROLL ========== */
            html, body {{
                overflow: hidden !important;
                height: 100vh !important;
            }}
            .stApp {{
                overflow: hidden !important;
                background: {bg_gradient} !important;
                min-height: 100vh !important;
            }}
            header[data-testid="stHeader"],
            #MainMenu, footer, .stDeployButton,
            [data-testid="stSidebar"] {{
                display: none !important;
            }}
            .block-container {{
                padding: 0 !important;
                max-width: 100% !important;
            }}
            
            /* Floating Orbs - Static, optimized for performance */
            .orb {{
                position: fixed;
                border-radius: 50%;
                filter: blur(40px);
                opacity: 0.3;
                z-index: 0;
                pointer-events: none;
                will-change: auto;
            }}
            .orb-1 {{
                width: 250px; height: 250px;
                background: {orb1_color};
                bottom: -80px; left: -80px;
            }}
            .orb-2 {{
                width: 220px; height: 220px;
                background: {orb2_color};
                top: -60px; right: -60px;
            }}
            .orb-3 {{
                width: 180px; height: 180px;
                background: {orb3_color};
                top: 40%; left: 55%;
                opacity: 0.2;
            }}
            
            /* Sparkles removed for performance */
            
            /* ========== CENTER EVERYTHING ========== */
            [data-testid="stMainBlockContainer"] {{
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                align-items: center !important;
                min-height: 100vh !important;
                max-height: 100vh !important;
                padding: 0.5rem !important;
                position: relative;
                z-index: 10;
                overflow: hidden !important;
            }}
            [data-testid="stVerticalBlock"] {{
                width: 100% !important;
                max-width: 320px !important;
                display: flex !important;
                flex-direction: column !important;
                align-items: center !important;
                position: relative !important;
                z-index: 10 !important;
            }}
            
            /* Keep form elements within glass bounds */
            .stTextInput, .stCheckbox, .stButton {{
                width: 100% !important;
                max-width: 300px !important;
            }}
            
            /* Login header stays inside glass */
            .login-header {{
                text-align: center;
                margin-bottom: 0.8rem;
                padding: 0.8rem 1rem;
                background: linear-gradient(145deg, 
                    rgba(255, 255, 255, 0.12) 0%, 
                    rgba(255, 255, 255, 0.05) 50%,
                    rgba(255, 255, 255, 0.08) 100%);
                backdrop-filter: blur(16px) saturate(180%);
                -webkit-backdrop-filter: blur(16px) saturate(180%);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-top: 1px solid rgba(255, 255, 255, 0.4);
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                width: 100%;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                box-shadow:
                    0 4px 20px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
                position: relative;
                overflow: hidden;
            }}
            
            /* Static glass shine on header */
            .login-header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 50%);
                pointer-events: none;
            }}
            
            /* ========== MAIN GLASS LOGIN CARD ========== */
            /* Style the st.container(border=True) as glass */
            [data-testid="stVerticalBlockBorderWrapper"] {{
                background: rgba(180, 180, 180, 0.12) !important;
                backdrop-filter: blur(12px) saturate(150%) !important;
                -webkit-backdrop-filter: blur(12px) saturate(150%) !important;
                border: 1.5px solid rgba(255, 255, 255, 0.4) !important;
                border-top-color: rgba(255, 255, 255, 0.6) !important;
                border-left-color: rgba(255, 255, 255, 0.5) !important;
                border-radius: 24px !important;
                padding: 1.2rem !important;
                box-shadow: 
                    0 8px 32px rgba(0, 0, 0, 0.5),
                    0 20px 60px rgba(0, 0, 0, 0.4),
                    inset 0 1px 1px rgba(255, 255, 255, 0.1) !important;
                max-width: 360px !important;
                margin: 0 auto !important;
                position: relative !important;
                overflow: hidden !important;
                will-change: transform !important;
                transform: translateZ(0) !important;
            }}
            
            /* Inner container of bordered wrapper */
            [data-testid="stVerticalBlockBorderWrapper"] > div {{
                background: transparent !important;
            }}
            
            /* Static glass shine */
            [data-testid="stVerticalBlockBorderWrapper"]::before {{
                content: '' !important;
                position: absolute !important;
                top: 0 !important;
                left: 0 !important;
                width: 100% !important;
                height: 100% !important;
                background: linear-gradient(
                    135deg,
                    rgba(255, 255, 255, 0.12) 0%,
                    transparent 40%
                ) !important;
                pointer-events: none !important;
                z-index: 1 !important;
            }}
            
            /* Glass reflection at top */
            [data-testid="stVerticalBlockBorderWrapper"]::after {{
                content: '' !important;
                position: absolute !important;
                top: 0 !important;
                left: 10% !important;
                right: 10% !important;
                height: 1px !important;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(255, 255, 255, 0.6), 
                    transparent
                ) !important;
                pointer-events: none !important;
            }}
            
            /* ========== GLASS INNER ELEMENTS ========== */
            /* Glass effect for form field containers */
            [data-testid="stVerticalBlockBorderWrapper"] .stTextInput > div {{
                background: rgba(255, 255, 255, 0.15) !important;
                backdrop-filter: blur(4px) !important;
                -webkit-backdrop-filter: blur(4px) !important;
                border-radius: 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.25) !important;
                padding: 2px !important;
            }}
            
            /* Remember me checkbox glass effect */
            [data-testid="stVerticalBlockBorderWrapper"] .stCheckbox {{
                background: rgba(255, 255, 255, 0.08) !important;
                backdrop-filter: blur(4px) !important;
                -webkit-backdrop-filter: blur(4px) !important;
                border-radius: 8px !important;
                padding: 0.4rem 0.8rem !important;
                margin: 0.4rem 0 !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                transition: all 0.3s ease !important;
            }}
            
            [data-testid="stVerticalBlockBorderWrapper"] .stCheckbox:hover {{
                background: rgba(255, 255, 255, 0.15) !important;
                border-color: rgba(255, 255, 255, 0.3) !important;
            }}
            
            [data-testid="stVerticalBlockBorderWrapper"] .stCheckbox label,
            [data-testid="stVerticalBlockBorderWrapper"] .stCheckbox label p {{
                color: #ffffff !important;
                font-size: 0.8rem !important;
                font-weight: 500 !important;
            }}
            
            /* Dragon Logo Container */
            .dragon-logo-wrap {{
                position: relative;
                width: 70px;
                height: 70px;
                margin-bottom: 0.4rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .dragon-logo-ring {{
                position: absolute;
                width: 100%;
                height: 100%;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                animation: ringRotate 30s linear infinite;
                will-change: transform;
            }}
            
            .dragon-logo-ring::before {{
                content: '';
                position: absolute;
                top: -2px;
                left: 50%;
                transform: translateX(-50%);
                width: 8px;
                height: 8px;
                background: {accent};
                border-radius: 50%;
                box-shadow: 0 0 10px {accent}, 0 0 20px {accent};
            }}
            
            @keyframes ringRotate {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
            
            /* Dragon icon - stable in center */
            .dragon-icon {{
                font-size: 2.4rem;
                filter: drop-shadow(0 0 10px {accent}) drop-shadow(0 0 20px rgba(255,100,0,0.5));
                display: block;
                position: relative;
                z-index: 2;
            }}
            
            /* Fire glow effect behind dragon */
            .dragon-fire-glow {{
                position: absolute;
                width: 50px;
                height: 50px;
                background: radial-gradient(circle, rgba(255,100,0,0.4) 0%, rgba(255,50,0,0.2) 40%, transparent 70%);
                border-radius: 50%;
                animation: fireGlow 6s ease-in-out infinite;
                z-index: 1;
                will-change: transform, opacity;
            }}
            
            @keyframes fireGlow {{
                0%, 100% {{ transform: scale(1); opacity: 0.6; }}
                50% {{ transform: scale(1.15); opacity: 0.9; }}
            }}
            
            /* Title styling */
            .title-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0;
            }}
            
            .login-title {{
                font-size: 1.1rem;
                font-weight: 800;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                letter-spacing: 4px;
                text-transform: uppercase;
                color: #4ade80;
                margin: 0;
                text-shadow: 0 2px 15px rgba(74, 222, 128, 0.5), 0 0 30px rgba(34, 197, 94, 0.3);
                position: relative;
            }}
            
            .login-title-main {{
                font-size: 1.8rem;
                font-weight: 900;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                letter-spacing: 6px;
                text-transform: uppercase;
                background: linear-gradient(180deg, 
                    {orb1_color} 0%, 
                    {orb2_color} 50%,
                    {orb3_color} 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
                filter: drop-shadow(0 4px 8px rgba(255, 255, 255, 0.3));
            }}
            
            .title-divider {{
                width: 80%;
                height: 2px;
                background: linear-gradient(90deg, transparent, {orb1_color}, {orb2_color}, {orb1_color}, transparent);
                margin: 0.4rem 0;
                box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
            }}
            
            .login-subtitle {{
                color: #ffffff;
                font-size: 0.7rem;
                font-weight: 600;
                letter-spacing: 2px;
                text-transform: uppercase;
                text-shadow: 0 2px 10px rgba(255, 255, 255, 0.3);
            }}
            
            /* Form inputs styling */
            .stTextInput {{
                margin-bottom: 0.3rem !important;
            }}
            
            .stTextInput label, .stTextInput label p {{
                color: #ffffff !important;
                font-size: 0.8rem !important;
                font-weight: 600 !important;
                margin-bottom: 0.2rem !important;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
            }}
            
            /* Input wrapper - remove white background */
            .stTextInput [data-testid="stTextInputRootElement"],
            .stTextInput [data-baseweb="input"],
            .stTextInput [data-baseweb="base-input"] {{
                background: transparent !important;
                background-color: transparent !important;
                border: none !important;
            }}
            
            .stTextInput > div > div > input {{
                background: rgba(0, 0, 0, 0.25) !important;
                backdrop-filter: blur(20px) saturate(180%) !important;
                -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
                border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
                border-top-color: rgba(255, 255, 255, 0.5) !important;
                border-left-color: rgba(255, 255, 255, 0.4) !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                padding: 0.5rem 0.7rem !important;
                font-size: 0.9rem !important;
                height: 36px !important;
                min-height: unset !important;
                box-shadow: 
                    inset 0 1px 1px rgba(255, 255, 255, 0.1),
                    inset 0 -1px 1px rgba(0, 0, 0, 0.1) !important;
            }}
            .stTextInput > div > div > input:focus {{
                border-color: rgba(255, 255, 255, 0.6) !important;
                box-shadow: 
                    0 0 8px rgba(255, 255, 255, 0.2),
                    inset 0 1px 1px rgba(255, 255, 255, 0.1) !important;
                background: rgba(0, 0, 0, 0.2) !important;
            }}
            .stTextInput > div > div > input::placeholder {{
                color: rgba(255,255,255,0.7) !important;
                -webkit-text-fill-color: rgba(255,255,255,0.7) !important;
                opacity: 1 !important;
            }}
            .stTextInput input::placeholder {{
                color: rgba(255,255,255,0.7) !important;
                -webkit-text-fill-color: rgba(255,255,255,0.7) !important;
                opacity: 1 !important;
            }}
            
            /* Password eye icon button */
            .stTextInput button {{
                background: transparent !important;
                color: rgba(255,255,255,0.7) !important;
            }}
            .stTextInput button svg {{
                fill: rgba(255,255,255,0.7) !important;
            }}
            
            /* Buttons - base glass style */
            .stButton {{
                margin-top: 0.1rem !important;
            }}
            .stButton > button {{
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                border-radius: 8px !important;
                color: #fff !important;
                font-weight: 600 !important;
                padding: 0.4rem 0.8rem !important;
                font-size: 0.85rem !important;
                height: 36px !important;
                transition: all 0.25s !important;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
            }}
            
            /* Sign In button - GREEN glass (first column) */
            [data-testid="column"]:first-child .stButton > button,
            [data-testid="stHorizontalBlock"] > div:first-child .stButton > button {{
                background: rgba(100, 255, 100, 0.25) !important;
                border: 1.5px solid rgba(100, 255, 100, 0.5) !important;
                border-top-color: rgba(150, 255, 150, 0.7) !important;
                border-left-color: rgba(130, 255, 130, 0.6) !important;
                box-shadow: 
                    0 4px 15px rgba(100, 255, 100, 0.3),
                    inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
            }}
            [data-testid="column"]:first-child .stButton > button:hover,
            [data-testid="stHorizontalBlock"] > div:first-child .stButton > button:hover {{
                transform: translateY(-2px) !important;
                background: rgba(100, 255, 100, 0.35) !important;
                box-shadow: 
                    0 6px 25px rgba(100, 255, 100, 0.4),
                    inset 0 1px 1px rgba(255, 255, 255, 0.25) !important;
            }}
            
            /* Help button - RED glass (second column) */
            [data-testid="column"]:last-child .stButton > button,
            [data-testid="column"]:nth-child(2) .stButton > button,
            [data-testid="stHorizontalBlock"] > div:last-child .stButton > button {{
                background: rgba(255, 80, 80, 0.3) !important;
                border: 1.5px solid rgba(255, 100, 100, 0.5) !important;
                border-top-color: rgba(255, 150, 150, 0.6) !important;
                border-left-color: rgba(255, 130, 130, 0.55) !important;
                box-shadow: 
                    0 4px 15px rgba(255, 80, 80, 0.3),
                    inset 0 1px 1px rgba(255, 255, 255, 0.15) !important;
            }}
            [data-testid="column"]:last-child .stButton > button:hover,
            [data-testid="column"]:nth-child(2) .stButton > button:hover,
            [data-testid="stHorizontalBlock"] > div:last-child .stButton > button:hover {{
                transform: translateY(-2px) !important;
                background: rgba(255, 80, 80, 0.4) !important;
                box-shadow: 
                    0 6px 20px rgba(255, 80, 80, 0.4),
                    inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
            }}
            
            [data-testid="column"] {{ background: transparent !important; }}
            
            /* Help box - compact */
            .help-glass {{
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 0.7rem;
                margin-top: 0.5rem;
            }}
            .help-glass-title {{ color: {accent}; font-weight: 600; margin-bottom: 0.2rem; font-size: 0.75rem; }}
            .help-glass-text {{ color: rgba(255,255,255,0.6); font-size: 0.7rem; }}
            .help-glass-text code {{ background: rgba(255,255,255,0.1); padding: 0.1rem 0.3rem; border-radius: 4px; color: {accent}; font-size: 0.65rem; }}
            
            /* Alerts - compact */
            .stSuccess, .stError, .stWarning, .stInfo {{
                background: rgba(0,0,0,0.4) !important;
                backdrop-filter: blur(12px) !important;
                border-radius: 8px !important;
                padding: 0.5rem !important;
                font-size: 0.8rem !important;
            }}
            
            /* ========== FEATURE TILES - COMPACT GLASS ========== */
            .features-row {{
                display: flex;
                justify-content: center;
                gap: 0.3rem;
                margin-top: 0.6rem;
                width: 100%;
                max-width: 300px;
            }}
            .feature-glass {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 0.4rem 0.3rem;
                text-align: center;
                flex: 1;
                transition: all 0.3s ease;
            }}
            .feature-glass:hover {{
                background: rgba(255, 255, 255, 0.1);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }}
            .feature-icon {{ font-size: 0.9rem; margin-bottom: 0.1rem; }}
            .feature-text {{ color: rgba(255,255,255,0.5); font-size: 0.55rem; font-weight: 500; }}
            
            .version-text {{ color: rgba(255,255,255,0.15); font-size: 0.5rem; text-align: center; margin-top: 0.5rem; }}
        </style>
        
        <!-- Orbs -->
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("""
            <div class="login-header">
                <div class="dragon-logo-wrap">
                    <div class="dragon-logo-ring"></div>
                    <div class="dragon-fire-glow"></div>
                    <div class="dragon-icon">🐉</div>
                </div>
                <div class="title-container">
                    <span class="login-title">DRAGON</span>
                    <div class="title-divider"></div>
                    <span class="login-title-main">MAILER</span>
                </div>
                <p class="login-subtitle">Professional Email & SMS Platform</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login Form elements
        if multi_user:
            username = st.text_input("Username", key="login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            # Remember me checkbox
            remember_me = st.checkbox("🔐 Remember me", key="remember_me", value=st.session_state.get('remember_me', False))
            
            col1, col2 = st.columns([1.2, 0.8])
            with col1:
                login_clicked = st.button("🔓 Sign In", key="login_btn", use_container_width=True)
            with col2:
                help_clicked = st.button("🆘 Help", key="help_btn", use_container_width=True)
            
            if login_clicked:
                if username and password:
                    success, message, role = authenticate_user(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.user_role = role
                        st.success(f"✅ Welcome back, {username}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ Please enter both username and password")
            
            if help_clicked or st.session_state.get('show_help', False):
                st.session_state.show_help = True
                st.markdown(f"""
                    <div class="help-glass">
                        <div class="help-glass-title">💡 Need Assistance?</div>
                        <div class="help-glass-text">
                            <strong>Forgot your password?</strong> Contact support for help.<br>
                            <strong>New user?</strong> Ask your team lead for access.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            # Remember me checkbox
            remember_me = st.checkbox("🔐 Remember me", key="remember_me", value=st.session_state.get('remember_me', False))
            
            col1, col2 = st.columns([1.2, 0.8])
            with col1:
                login_clicked = st.button("🔓 Sign In", key="login_btn", use_container_width=True)
            with col2:
                help_clicked = st.button("🆘 Help", key="help_btn", use_container_width=True)
            
            if login_clicked:
                if verify_password(password, settings.get("password_hash", "")):
                    st.session_state.authenticated = True
                    st.session_state.current_user = "admin"
                    st.session_state.user_role = "admin"
                    st.success("✅ Login successful!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
            
            if help_clicked:
                st.markdown("""
                    <div class="help-glass">
                        <div class="help-glass-title">💡 Need Assistance?</div>
                        <div class="help-glass-text">
                            <strong>Forgot your password?</strong> Contact support for help.<br>
                            <strong>Having issues?</strong> Try refreshing the page.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Feature tiles with separate glass
    st.markdown(f"""
        <div class="features-row">
            <div class="feature-glass">
                <div class="feature-icon">📧</div>
                <div class="feature-text">Email</div>
            </div>
            <div class="feature-glass">
                <div class="feature-icon">📱</div>
                <div class="feature-text">SMS</div>
            </div>
            <div class="feature-glass">
                <div class="feature-icon">☁️</div>
                <div class="feature-text">Azure</div>
            </div>
            <div class="feature-glass">
                <div class="feature-icon">🔒</div>
                <div class="feature-text">Secure</div>
            </div>
        </div>
        <div class="version-text">Dragon Mailer v2.0 • © 2026</div>
    """, unsafe_allow_html=True)


# ============== SCHEDULED SENDING FUNCTIONS ==============

def load_scheduled_tasks() -> list:
    """Load scheduled tasks."""
    return load_json_file(SCHEDULED_FILE, [])


def save_scheduled_tasks(tasks: list):
    """Save scheduled tasks."""
    save_json_file(SCHEDULED_FILE, tasks)


def add_scheduled_task(task: dict):
    """Add a new scheduled task."""
    tasks = load_scheduled_tasks()
    task["id"] = str(uuid.uuid4())[:8]
    task["created"] = datetime.now().isoformat()
    task["status"] = "pending"
    tasks.append(task)
    save_scheduled_tasks(tasks)
    return task["id"]


def delete_scheduled_task(task_id: str):
    """Delete a scheduled task."""
    tasks = load_scheduled_tasks()
    tasks = [t for t in tasks if t.get("id") != task_id]
    save_scheduled_tasks(tasks)


def update_scheduled_task_status(task_id: str, status: str, result: str = None):
    """Update status of a scheduled task."""
    tasks = load_scheduled_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = status
            if result:
                task["result"] = result
            task["updated"] = datetime.now().isoformat()
            break
    save_scheduled_tasks(tasks)


def check_and_execute_scheduled_tasks():
    """Check for due tasks and execute them."""
    tasks = load_scheduled_tasks()
    now = datetime.now()
    
    for task in tasks:
        if task.get("status") != "pending":
            continue
            
        scheduled_time = datetime.fromisoformat(task.get("scheduled_time", ""))
        if now >= scheduled_time:
            # Mark as running
            update_scheduled_task_status(task["id"], "running")
            
            try:
                # Execute based on task type
                if task.get("type") == "email":
                    # Execute email task
                    result = execute_scheduled_email(task)
                elif task.get("type") == "sms":
                    # Execute SMS task
                    result = execute_scheduled_sms(task)
                else:
                    result = "Unknown task type"
                
                update_scheduled_task_status(task["id"], "completed", result)
            except Exception as e:
                update_scheduled_task_status(task["id"], "failed", str(e))


def execute_scheduled_email(task: dict) -> str:
    """Execute a scheduled email task."""
    smtp_configs = load_smtp_configs()
    smtp_name = task.get("smtp_config")
    
    if smtp_name not in smtp_configs:
        return f"SMTP config '{smtp_name}' not found"
    
    config = smtp_configs[smtp_name]
    results = send_email(
        smtp_server=config["server"],
        smtp_port=config["port"],
        sender_email=config.get("email", ""),
        sender_password=config.get("password", ""),
        recipient_emails=task.get("recipients", []),
        subject=task.get("subject", ""),
        message=task.get("message", ""),
        html_content=task.get("html_content"),
        use_tls=config.get("use_tls", True),
        use_ssl=config.get("use_ssl", False),
        no_auth=config.get("no_auth", False)
    )
    
    success_count = sum(1 for r in results if r.get("success"))
    return f"Sent {success_count}/{len(results)} emails"


def execute_scheduled_sms(task: dict) -> str:
    """Execute a scheduled SMS task."""
    smtp_configs = load_smtp_configs()
    smtp_name = task.get("smtp_config")
    
    if smtp_name not in smtp_configs:
        return f"SMTP config '{smtp_name}' not found"
    
    config = smtp_configs[smtp_name]
    phone_entries = task.get("phone_entries", [])
    
    results = send_sms_via_gateway(
        smtp_server=config["server"],
        smtp_port=config["port"],
        sender_email=config.get("email", ""),
        sender_password=config.get("password", ""),
        phone_entries=phone_entries,
        subject=task.get("subject", ""),
        message=task.get("message", ""),
        use_tls=config.get("use_tls", True),
        use_ssl=config.get("use_ssl", False)
    )
    
    success_count = sum(1 for r in results if r.get("success"))
    return f"Sent {success_count}/{len(results)} SMS"


# ============== JELLY PROGRESS WRAPPER ==============

def get_theme_accent_color() -> str:
    """Get the accent color for the current theme."""
    settings = load_settings()
    theme_name = settings.get("theme", "Dragon Dark")
    
    # Theme accent colors
    theme_accents = {
        "Dragon Dark": "#ff6b35",
        "Classic Light": "#2563eb",
        "Warm Ember": "#f97316",
        "Midnight Blue": "#3b82f6",
        "Ocean Breeze": "#0ea5e9",
        "Forest Green": "#22c55e",
        "Sunset Orange": "#f97316",
        "Purple Haze": "#a855f7",
        "Rose Gold": "#ec4899",
        "Cyber Neon": "#00ff88",
        "Arctic Ice": "#06b6d4",
        "Neon Jelly": "#c8ff00",
        "SecureMail Pro": "#fbbf24",
        "Glass": "#60a5fa",
    }
    return theme_accents.get(theme_name, "#ff6b35")


class JellyProgressBar:
    """
    Progress bar wrapper that uses Jelly components with animated effects.
    Adapts color based on current theme.
    """
    def __init__(self, label: str = "Progress", color: str = None):
        self.label = label
        self.color = color or get_theme_accent_color()
        self.value = 0.0
        self.placeholder = st.empty()
        self.use_jelly = JELLY_AVAILABLE
        
    def progress(self, value: float):
        """Update progress value (0.0 to 1.0)."""
        self.value = max(0.0, min(1.0, value))
        if self.use_jelly:
            with self.placeholder:
                jelly_progress(self.value, self.label, self.color)
        else:
            self.placeholder.progress(self.value)
    
    def empty(self):
        """Clear the progress bar."""
        self.placeholder.empty()


def show_jelly_metric(label: str, value: str, delta: str = None, color: str = None):
    """Show a metric using Jelly style with animated effects."""
    accent_color = color or get_theme_accent_color()
    
    if JELLY_AVAILABLE:
        jelly_metric(label, value, delta, accent_color)
    else:
        st.metric(label, value, delta)


def show_jelly_loading(text: str = "Loading...", color: str = None):
    """Show loading animation using Jelly style with animated effects."""
    accent_color = color or get_theme_accent_color()
    
    if JELLY_AVAILABLE:
        jelly_loading(text, accent_color)
    else:
        st.spinner(text)


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
    
    def connect_smtp():
        """Try primary port, fallback to 465 SSL if blocked."""
        try:
            if use_ssl:
                return smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                srv = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                if use_tls:
                    srv.starttls()
                return srv
        except (TimeoutError, OSError) as e:
            # Port 587 blocked? Try 465 with SSL as fallback
            if smtp_port == 587 and "office365" in smtp_server.lower():
                try:
                    return smtplib.SMTP_SSL(smtp_server, 465, timeout=30)
                except:
                    pass
            raise e
    
    try:
        # Connect once for all recipients (with fallback to port 465)
        server = connect_smtp()
        
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


# ============== PATTERN GENERATOR ==============

def generate_random_string(length: int = 8, chars: str = "aA0") -> str:
    """Generate random string based on character set.
    
    chars options:
    - 'a' = lowercase letters
    - 'A' = uppercase letters
    - '0' = digits
    - 'aA0' = all (default)
    """
    char_pool = ""
    if 'a' in chars:
        char_pool += string.ascii_lowercase
    if 'A' in chars:
        char_pool += string.ascii_uppercase
    if '0' in chars:
        char_pool += string.digits
    
    if not char_pool:
        char_pool = string.ascii_letters + string.digits
    
    return ''.join(random.choice(char_pool) for _ in range(length))


def apply_patterns(text: str, recipient_email: str = None) -> str:
    """
    Replace pattern variables in text.
    Supported patterns:
    - {random} - 8 char random alphanumeric
    - {random:N} - N char random alphanumeric
    - {random_lower} / {random_lower:N} - lowercase random
    - {random_upper} / {random_upper:N} - uppercase random
    - {random_digit} / {random_digit:N} - random digits
    - {date} - current date (YYYY-MM-DD)
    - {time} - current time (HH:MM)
    - {uuid} - unique identifier
    - {email} - recipient email
    - {name} - extracted name from email
    """
    if not text:
        return text
    
    # Random patterns with length
    text = re.sub(r'\{random:(\d+)\}', lambda m: generate_random_string(int(m.group(1)), "aA0"), text)
    text = re.sub(r'\{random_lower:(\d+)\}', lambda m: generate_random_string(int(m.group(1)), "a"), text)
    text = re.sub(r'\{random_upper:(\d+)\}', lambda m: generate_random_string(int(m.group(1)), "A"), text)
    text = re.sub(r'\{random_digit:(\d+)\}', lambda m: generate_random_string(int(m.group(1)), "0"), text)
    
    # Simple patterns
    text = text.replace('{random}', generate_random_string(8, "aA0"))
    text = text.replace('{random_lower}', generate_random_string(8, "a"))
    text = text.replace('{random_upper}', generate_random_string(8, "A"))
    text = text.replace('{random_digit}', generate_random_string(6, "0"))
    
    # Date/time patterns
    now = datetime.now()
    text = text.replace('{date}', now.strftime('%Y-%m-%d'))
    text = text.replace('{time}', now.strftime('%H:%M'))
    text = text.replace('{uuid}', str(uuid.uuid4())[:8])
    
    # Recipient-based patterns
    if recipient_email:
        text = text.replace('{email}', recipient_email)
        if '@' in recipient_email:
            name_part = recipient_email.split('@')[0]
            # Clean up common patterns like first.last
            name = name_part.replace('.', ' ').replace('_', ' ').replace('-', ' ').title()
            text = text.replace('{name}', name)
    
    return text


def send_bulk_email_advanced(
    smtp_configs: list[dict],  # List of SMTP configs for rotation
    recipient_emails: list[str],
    subject: str,
    message: str,
    html_content: str = None,
    attachments: list = None,
    use_bcc: bool = True,
    bcc_batch_size: int = 50,
    delay_seconds: float = 0,
    delay_every_n_emails: int = 0,
    rotate_after_n_emails: int = 0,
    enable_tracking: bool = False,
    enable_patterns: bool = False,
    progress_callback = None,
    sender_name: str = None
) -> list[dict]:
    """
    Advanced bulk email sending with BCC, delays, SMTP rotation, and patterns.
    """
    results = []
    total = len(recipient_emails)
    emails_sent = 0
    current_smtp_idx = 0
    current_server = None
    
    if not smtp_configs:
        return [{"recipient": r, "success": False, "message": "No SMTP configured", "timestamp": datetime.now().isoformat()}
                for r in recipient_emails]
    
    def get_smtp_connection(idx):
        """Get SMTP connection for the given config index with port 465 fallback."""
        cfg = smtp_configs[idx % len(smtp_configs)]
        try:
            if cfg.get('use_ssl'):
                srv = smtplib.SMTP_SSL(cfg['server'], cfg['port'], timeout=30)
            else:
                srv = smtplib.SMTP(cfg['server'], cfg['port'], timeout=30)
                if cfg.get('use_tls', True):
                    srv.starttls()
            
            if not cfg.get('no_auth', False):
                srv.login(cfg['email'], cfg['password'])
            return srv, cfg
        except (TimeoutError, OSError) as e:
            # Port 587 blocked? Try 465 with SSL as fallback
            if cfg['port'] == 587 and "office365" in cfg['server'].lower():
                try:
                    srv = smtplib.SMTP_SSL(cfg['server'], 465, timeout=30)
                    if not cfg.get('no_auth', False):
                        srv.login(cfg['email'], cfg['password'])
                    return srv, cfg
                except:
                    pass
            return None, cfg
        except Exception as e:
            return None, cfg
    
    try:
        current_server, current_config = get_smtp_connection(current_smtp_idx)
        if not current_server:
            return [{"recipient": r, "success": False, "message": "Failed to connect to SMTP", "timestamp": datetime.now().isoformat()}
                    for r in recipient_emails]
        
        tracking_id = str(uuid.uuid4()) if enable_tracking else None
        
        if use_bcc:
            # BCC MODE - Send in batches
            batches = [recipient_emails[i:i + bcc_batch_size] for i in range(0, total, bcc_batch_size)]
            
            for batch_idx, batch in enumerate(batches):
                # Check if we need to rotate SMTP
                if rotate_after_n_emails > 0 and emails_sent >= rotate_after_n_emails:
                    try:
                        current_server.quit()
                    except:
                        pass
                    current_smtp_idx += 1
                    current_server, current_config = get_smtp_connection(current_smtp_idx)
                    emails_sent = 0
                
                try:
                    # Apply patterns to subject and message for this batch
                    batch_subject = apply_patterns(subject, batch[0]) if enable_patterns else subject
                    batch_message = apply_patterns(message, batch[0]) if enable_patterns else message
                    batch_html = apply_patterns(html_content, batch[0]) if enable_patterns and html_content else html_content
                    
                    # Create message
                    msg = MIMEMultipart('alternative')
                    if sender_name:
                        msg['From'] = f"{sender_name} <{current_config['email']}>"
                    else:
                        msg['From'] = current_config['email']
                    msg['To'] = current_config['email']  # Send to self
                    msg['Bcc'] = ', '.join(batch)  # BCC all recipients
                    msg['Subject'] = batch_subject
                    msg['Date'] = formatdate(localtime=True)
                    msg['Message-ID'] = make_msgid(domain=current_config['email'].split('@')[-1])
                    
                    msg.attach(MIMEText(batch_message, 'plain'))
                    
                    if batch_html:
                        html_body = batch_html
                        if enable_tracking and tracking_id:
                            tracking_pixel = generate_tracking_pixel(tracking_id)
                            if '</body>' in html_body.lower():
                                html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
                                html_body = html_body.replace('</BODY>', f'{tracking_pixel}</BODY>')
                            else:
                                html_body += tracking_pixel
                        msg.attach(MIMEText(html_body, 'html'))
                    
                    # Add attachments
                    if attachments:
                        for att in attachments:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(att['data'])
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename="{att["name"]}"')
                            msg.attach(part)
                    
                    # Send to all BCC recipients
                    all_recipients = [current_config['email']] + batch
                    try:
                        current_server.sendmail(current_config['email'], all_recipients, msg.as_string())
                    except smtplib.SMTPServerDisconnected:
                        # Reconnect and retry
                        current_server, current_config = get_smtp_connection(current_smtp_idx)
                        current_server.sendmail(current_config['email'], all_recipients, msg.as_string())
                    
                    # Record success for all in batch
                    for recipient in batch:
                        result = {
                            "recipient": recipient,
                            "success": True,
                            "message": f"Sent via BCC (batch {batch_idx + 1})",
                            "tracking_id": tracking_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        results.append(result)
                        save_sent_message({
                            **result,
                            "subject": batch_subject,
                            "type": "email",
                            "smtp_server": current_config['server']
                        })
                    
                    emails_sent += len(batch)
                    
                except Exception as e:
                    for recipient in batch:
                        results.append({
                            "recipient": recipient,
                            "success": False,
                            "message": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
                
                if progress_callback:
                    progress_callback((batch_idx + 1) / len(batches))
                
                # Delay logic
                if delay_seconds > 0:
                    if delay_every_n_emails > 0:
                        if emails_sent % delay_every_n_emails == 0:
                            time.sleep(delay_seconds)
                    else:
                        time.sleep(delay_seconds)
        
        else:
            # INDIVIDUAL MODE - Send one by one with patterns
            for idx, recipient in enumerate(recipient_emails):
                recipient = recipient.strip()
                if not recipient or '@' not in recipient:
                    continue
                
                # Check for SMTP rotation
                if rotate_after_n_emails > 0 and emails_sent >= rotate_after_n_emails:
                    try:
                        current_server.quit()
                    except:
                        pass
                    current_smtp_idx += 1
                    current_server, current_config = get_smtp_connection(current_smtp_idx)
                    emails_sent = 0
                
                try:
                    # Apply patterns
                    email_subject = apply_patterns(subject, recipient) if enable_patterns else subject
                    email_message = apply_patterns(message, recipient) if enable_patterns else message
                    email_html = apply_patterns(html_content, recipient) if enable_patterns and html_content else html_content
                    
                    msg = MIMEMultipart('alternative')
                    if sender_name:
                        msg['From'] = f"{sender_name} <{current_config['email']}>"
                    else:
                        msg['From'] = current_config['email']
                    msg['To'] = recipient
                    msg['Subject'] = email_subject
                    msg['Date'] = formatdate(localtime=True)
                    msg['Message-ID'] = make_msgid(domain=current_config['email'].split('@')[-1])
                    
                    msg.attach(MIMEText(email_message, 'plain'))
                    
                    if email_html:
                        html_body = email_html
                        if enable_tracking and tracking_id:
                            tracking_pixel = generate_tracking_pixel(tracking_id)
                            if '</body>' in html_body.lower():
                                html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
                            else:
                                html_body += tracking_pixel
                        msg.attach(MIMEText(html_body, 'html'))
                    
                    if attachments:
                        for att in attachments:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(att['data'])
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename="{att["name"]}"')
                            msg.attach(part)
                    
                    current_server.sendmail(current_config['email'], recipient, msg.as_string())
                    
                    result = {
                        "recipient": recipient,
                        "success": True,
                        "message": "Sent successfully",
                        "tracking_id": tracking_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    results.append(result)
                    save_sent_message({
                        **result,
                        "subject": email_subject,
                        "type": "email",
                        "smtp_server": current_config['server']
                    })
                    
                    emails_sent += 1
                    
                except Exception as e:
                    results.append({
                        "recipient": recipient,
                        "success": False,
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                
                if progress_callback:
                    progress_callback((idx + 1) / total)
                
                # Delay logic
                if delay_seconds > 0:
                    if delay_every_n_emails > 0:
                        if emails_sent % delay_every_n_emails == 0:
                            time.sleep(delay_seconds)
                    else:
                        time.sleep(delay_seconds)
        
        current_server.quit()
        
    except Exception as e:
        return [{"recipient": r, "success": False, "message": f"Error: {str(e)}", "timestamp": datetime.now().isoformat()}
                for r in recipient_emails]
    
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
    
    def connect_smtp_sms():
        """Try primary port, fallback to 465 SSL if blocked."""
        try:
            if use_ssl:
                return smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                srv = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                if use_tls:
                    srv.starttls()
                return srv
        except (TimeoutError, OSError) as e:
            # Port 587 blocked? Try 465 with SSL as fallback
            if smtp_port == 587 and "office365" in smtp_server.lower():
                try:
                    return smtplib.SMTP_SSL(smtp_server, 465, timeout=30)
                except:
                    pass
            raise e
    
    try:
        server = connect_smtp_sms()
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
                
                # Handle Auto mode - try all major gateways
                if gateway_domain == "auto":
                    sent_successfully = False
                    tried_gateways = []
                    last_error = ""
                    
                    for auto_gateway in AUTO_SMS_GATEWAYS:
                        sms_email = f"{clean_number}@{auto_gateway}"
                        tried_gateways.append(auto_gateway)
                        
                        try:
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
                                "message": f"Sent via {auto_gateway} (auto-detected)",
                                "timestamp": datetime.now().isoformat()
                            }
                            results.append(result)
                            
                            save_sent_message({
                                **result,
                                "type": "sms",
                                "carrier": f"Auto ({auto_gateway})",
                                "smtp_server": smtp_server
                            })
                            
                            sent_successfully = True
                            break  # Stop trying other gateways
                            
                        except Exception as e:
                            last_error = str(e)
                            continue  # Try next gateway
                    
                    if not sent_successfully:
                        results.append({
                            "recipient": phone_number,
                            "success": False,
                            "message": f"Auto-detect failed. Tried: {', '.join(tried_gateways)}. Error: {last_error}",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    if progress_callback:
                        progress_callback((idx + 1) / total)
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


def get_theme_css(theme_name: str) -> str:
    """Get CSS for a specific theme."""
    
    # Theme color definitions
    theme_colors = {
        "Dragon Dark": {
            "bg": "#1f1f1f", "sidebar_bg": "#171717", "card_bg": "#262626", "border": "#3f3f46",
            "text": "#ffffff", "text_secondary": "#a1a1aa", "accent": "#f97316",
            "accent_light": "#fbbf24", "input_bg": "#262626", "select_bg": "#3d2b1f",
            "select_border": "#8b5a2b", "type": "dark"
        },
        "Dragon Light": {
            "bg": "#fafafa", "sidebar_bg": "#ffffff", "card_bg": "#ffffff", "border": "#e5e5e5",
            "text": "#1f1f1f", "text_secondary": "#737373", "accent": "#f97316",
            "accent_light": "#ea580c", "input_bg": "#ffffff", "select_bg": "#fff7ed",
            "select_border": "#fed7aa", "type": "light"
        },
        "Midnight Blue": {
            "bg": "#0f172a", "sidebar_bg": "#1e293b", "card_bg": "#1e293b", "border": "#334155",
            "text": "#f1f5f9", "text_secondary": "#94a3b8", "accent": "#3b82f6",
            "accent_light": "#60a5fa", "input_bg": "#1e293b", "select_bg": "#1e3a5f",
            "select_border": "#3b82f6", "type": "dark"
        },
        "Ocean Breeze": {
            "bg": "#f0f9ff", "sidebar_bg": "#ffffff", "card_bg": "#ffffff", "border": "#bae6fd",
            "text": "#0c4a6e", "text_secondary": "#0369a1", "accent": "#0ea5e9",
            "accent_light": "#0284c7", "input_bg": "#ffffff", "select_bg": "#e0f2fe",
            "select_border": "#7dd3fc", "type": "light"
        },
        "Forest Green": {
            "bg": "#0f1f0f", "sidebar_bg": "#1a2e1a", "card_bg": "#1a2e1a", "border": "#2d4a2d",
            "text": "#e8f5e8", "text_secondary": "#a3c9a3", "accent": "#22c55e",
            "accent_light": "#4ade80", "input_bg": "#1a2e1a", "select_bg": "#1f3d1f",
            "select_border": "#22c55e", "type": "dark"
        },
        "Sunset Orange": {
            "bg": "#fffbf5", "sidebar_bg": "#ffffff", "card_bg": "#ffffff", "border": "#fed7aa",
            "text": "#7c2d12", "text_secondary": "#c2410c", "accent": "#f97316",
            "accent_light": "#ea580c", "input_bg": "#ffffff", "select_bg": "#fff7ed",
            "select_border": "#fdba74", "type": "light"
        },
        "Purple Haze": {
            "bg": "#1a0a2e", "sidebar_bg": "#2d1b4e", "card_bg": "#2d1b4e", "border": "#4c2885",
            "text": "#f3e8ff", "text_secondary": "#c4b5fd", "accent": "#a855f7",
            "accent_light": "#c084fc", "input_bg": "#2d1b4e", "select_bg": "#3d2066",
            "select_border": "#8b5cf6", "type": "dark"
        },
        "Rose Gold": {
            "bg": "#fdf2f8", "sidebar_bg": "#ffffff", "card_bg": "#ffffff", "border": "#fbcfe8",
            "text": "#831843", "text_secondary": "#be185d", "accent": "#ec4899",
            "accent_light": "#db2777", "input_bg": "#ffffff", "select_bg": "#fce7f3",
            "select_border": "#f9a8d4", "type": "light"
        },
        "Cyber Neon": {
            "bg": "#0a0a0a", "sidebar_bg": "#111111", "card_bg": "#111111", "border": "#1f1f1f",
            "text": "#00ff88", "text_secondary": "#00cc6a", "accent": "#00ff88",
            "accent_light": "#00ffaa", "input_bg": "#111111", "select_bg": "#0d1f15",
            "select_border": "#00ff88", "type": "dark"
        },
        "Arctic Ice": {
            "bg": "#f8fafc", "sidebar_bg": "#ffffff", "card_bg": "#ffffff", "border": "#cbd5e1",
            "text": "#1e293b", "text_secondary": "#64748b", "accent": "#06b6d4",
            "accent_light": "#0891b2", "input_bg": "#ffffff", "select_bg": "#ecfeff",
            "select_border": "#67e8f9", "type": "light"
        },
        "Neon Jelly": {
            "bg": "#1a1a1a", "sidebar_bg": "#0d0d0d", "card_bg": "#242424", "border": "#3d3d3d",
            "text": "#c8ff00", "text_secondary": "#a8d900", "accent": "#c8ff00",
            "accent_light": "#e0ff66", "input_bg": "#1f1f1f", "select_bg": "#1a2a10",
            "select_border": "#c8ff00", "type": "dark"
        },
        "SecureMail Pro": {
            "bg": "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
            "sidebar_bg": "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
            "card_bg": "rgba(30, 41, 59, 0.8)", "border": "#334155",
            "text": "#e2e8f0", "text_secondary": "#94a3b8", "accent": "#fbbf24",
            "accent_light": "#f59e0b", "input_bg": "rgba(30, 41, 59, 0.6)",
            "select_bg": "#1e293b", "select_border": "#475569", "type": "dark",
            "gradient": True
        },
        "Glass": {
            "bg": "linear-gradient(135deg, #0f172a 0%, #1e293b 30%, #334155 50%, #1e293b 70%, #0f172a 100%)",
            "sidebar_bg": "rgba(15, 23, 42, 0.7)",
            "card_bg": "rgba(30, 41, 59, 0.4)", "border": "rgba(148, 163, 184, 0.2)",
            "text": "#e2e8f0", "text_secondary": "#94a3b8", "accent": "#60a5fa",
            "accent_light": "#3b82f6", "input_bg": "rgba(30, 41, 59, 0.5)",
            "select_bg": "rgba(59, 130, 246, 0.2)", "select_border": "rgba(96, 165, 250, 0.4)", "type": "dark",
            "gradient": True, "glass": True
        },
    }
    
    # Get theme or default to Dragon Dark
    colors = theme_colors.get(theme_name, theme_colors["Dragon Dark"])
    is_dark = colors["type"] == "dark"
    is_gradient = colors.get("gradient", False)
    
    # Handle gradient vs solid background
    bg_style = colors['bg'] if is_gradient or "linear-gradient" in str(colors['bg']) else colors['bg']
    sidebar_bg = colors['sidebar_bg']
    
    # Generate theme-specific CSS
    theme_css = f"""
        /* ========== {theme_name.upper()} THEME ========== */
        .stApp {{
            background: {bg_style};
        }}
        
        /* Sidebar - GLASS EFFECT */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(20px) saturate(150%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(150%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 4px 0 30px rgba(0, 0, 0, 0.15), inset -1px 0 0 rgba(255, 255, 255, 0.05) !important;
        }}
        section[data-testid="stSidebar"] > div {{
            background: transparent !important;
        }}
        section[data-testid="stSidebar"] .stMarkdown, 
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: {colors['text']} !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: {colors['border']};
        }}

        /* Headers */
        h2 {{
            color: {colors['text']} !important;
            font-weight: 700;
            font-size: 1.35rem;
            margin-top: 1.5rem;
        }}
        h3 {{
            color: {colors['accent_light']} !important;
            font-size: 1.05rem;
            font-weight: 600;
        }}
        
        /* Text */
        .stMarkdown, .stMarkdown p, .stMarkdown span {{
            color: {colors['text']} !important;
        }}
        .stMarkdown strong, .stMarkdown b {{
            color: {colors['accent_light']} !important;
        }}
        .tagline {{
            color: {colors['text_secondary']} !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background: {colors['sidebar_bg']};
            border: 1px solid {colors['border']};
            flex-wrap: wrap;
            gap: 4px;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: {colors['text_secondary']};
            white-space: nowrap;
            overflow: visible;
            font-size: 0.85rem;
            padding: 8px 12px;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            background-color: {colors['border']};
            color: {colors['text']};
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, {colors['accent']} 0%, {colors['accent_light']} 100%) !important;
            color: #FFFFFF !important;
        }}

        /* Inputs - COMPREHENSIVE TEXT COLOR FIX */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            border: 1.5px solid {colors['border']} !important;
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
            -webkit-text-fill-color: {colors['text']} !important;
        }}
        .stTextInput input, .stTextArea textarea {{
            color: {colors['text']} !important;
            -webkit-text-fill-color: {colors['text']} !important;
        }}
        .stTextInput [data-baseweb="input"] input,
        .stTextInput [data-baseweb="base-input"] input {{
            color: {colors['text']} !important;
            -webkit-text-fill-color: {colors['text']} !important;
        }}
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {{
            color: {colors['text_secondary']} !important;
            -webkit-text-fill-color: {colors['text_secondary']} !important;
            opacity: 0.7 !important;
        }}
        
        /* Select boxes */
        .stSelectbox > div > div {{
            background: {colors['select_bg']} !important;
            color: {colors['text']} !important;
            border: 1.5px solid {colors['select_border']} !important;
        }}
        .stSelectbox > div > div > div {{
            color: {colors['text']} !important;
        }}
        .stSelectbox [data-baseweb="select"] span {{
            color: {colors['text']} !important;
        }}
        .stSelectbox [data-baseweb="select"] {{
            background: {colors['select_bg']} !important;
        }}
        .stSelectbox svg {{
            fill: {colors['accent']} !important;
        }}
        
        /* Labels */
        .stTextInput label, .stSelectbox label, .stTextArea label {{
            color: {colors['text']} !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {colors['accent']} 0%, {colors['accent_light']} 100%);
        }}
        .stButton > button:hover {{
            box-shadow: 0 6px 20px {colors['accent']}80, 0 0 30px {colors['accent']}50;
        }}
        .stDownloadButton > button {{
            background: {colors['input_bg']};
            color: {colors['accent']};
            border: 1.5px solid {colors['border']};
        }}
        .stDownloadButton > button:hover {{
            background: {colors['border']};
            border-color: {colors['accent']};
        }}
        
        /* Expanders */
        .streamlit-expanderHeader {{
            background: {colors['input_bg']};
            border: 1px solid {colors['border']};
            color: {colors['text']} !important;
        }}
        .streamlit-expanderContent {{
            border: 1px solid {colors['border']};
            background: {colors['bg']};
        }}
        .streamlit-expanderContent p,
        .streamlit-expanderContent span,
        .streamlit-expanderContent label,
        .streamlit-expanderContent div {{
            color: {colors['text']} !important;
        }}
        /* EXPANDER INPUT FIX - Ensure inputs inside expanders have proper colors */
        .streamlit-expanderContent input,
        .streamlit-expanderContent textarea,
        [data-testid="stExpander"] input,
        [data-testid="stExpander"] textarea {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
            -webkit-text-fill-color: {colors['text']} !important;
            border: 1.5px solid {colors['border']} !important;
        }}
        [data-testid="stExpander"] .stTextInput input,
        [data-testid="stExpander"] .stTextArea textarea {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
            -webkit-text-fill-color: {colors['text']} !important;
        }}
        [data-testid="stExpander"] [data-baseweb="input"],
        [data-testid="stExpander"] [data-baseweb="base-input"] {{
            background: {colors['input_bg']} !important;
        }}
        [data-testid="stExpander"] [data-baseweb="input"] input {{
            color: {colors['text']} !important;
            -webkit-text-fill-color: {colors['text']} !important;
        }}
        
        /* Metrics */
        div[data-testid="metric-container"] {{
            background: {colors['input_bg']};
            border: 1px solid {colors['border']};
        }}
        div[data-testid="metric-container"] label {{
            color: {colors['text_secondary']} !important;
        }}
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
            color: {colors['accent']} !important;
        }}
        
        /* Alerts - GLASS EFFECT */
        .stSuccess {{
            background: rgba(34, 197, 94, 0.12) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: {'#86efac' if is_dark else '#166534'};
            border: 1px solid rgba(34, 197, 94, 0.4) !important;
            border-radius: 12px !important;
        }}
        .stError {{
            background: rgba(239, 68, 68, 0.12) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: {'#fca5a5' if is_dark else '#991b1b'};
            border: 1px solid rgba(239, 68, 68, 0.4) !important;
            border-radius: 12px !important;
        }}
        .stInfo {{
            background: rgba(59, 130, 246, 0.12) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: {'#7dd3fc' if is_dark else '#0369a1'};
            border: 1px solid rgba(59, 130, 246, 0.4) !important;
            border-radius: 12px !important;
        }}
        .stWarning {{
            background: rgba(245, 158, 11, 0.12) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            color: {'#fde68a' if is_dark else '#92400e'};
            border: 1px solid rgba(245, 158, 11, 0.4) !important;
            border-radius: 12px !important;
        }}
        
        /* Checkbox & Radio */
        .stCheckbox label span, .stRadio label span,
        .stCheckbox label, .stRadio label,
        .stCheckbox p, .stRadio p {{
            color: {colors['text']} !important;
        }}
        
        /* Dividers */
        hr {{
            background: {colors['border']};
        }}
        
        /* File Uploader - Complete Fix */
        .stFileUploader > div {{
            border: 2px dashed {colors['accent']} !important;
            background: {colors['input_bg']} !important;
        }}
        .stFileUploader > div:hover {{
            border-color: {colors['accent_light']} !important;
        }}
        .stFileUploader label, .stFileUploader p, .stFileUploader span, .stFileUploader div {{
            color: {colors['text']} !important;
        }}
        .stFileUploader button {{
            background: {colors['accent']} !important;
            color: #ffffff !important;
        }}
        /* File uploader inner box - override white background */
        .stFileUploader [class*="st-emotion-cache"] {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
        }}
        .stFileUploader section,
        .stFileUploader section > div,
        .stFileUploader section > div > div {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar-track {{
            background: {colors['input_bg']};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {colors['border']};
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {colors['accent']};
        }}
        
        /* Data Tables */
        .stDataFrame {{
            background: {colors['input_bg']} !important;
            border: 1px solid {colors['border']};
        }}
        .stDataFrame td, .stDataFrame th {{
            color: {colors['text']} !important;
        }}
        
        /* Number/Date/Time inputs */
        .stNumberInput label, .stDateInput label, .stTimeInput label {{
            color: {colors['text']} !important;
        }}
        .stNumberInput input, .stDateInput input, .stTimeInput input {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
            border: 1.5px solid {colors['border']} !important;
        }}
        
        /* Multiselect */
        .stMultiSelect label, .stMultiSelect span {{
            color: {colors['text']} !important;
        }}
        .stMultiSelect > div > div {{
            background: {colors['select_bg']} !important;
            color: {colors['text']} !important;
            border: 1.5px solid {colors['select_border']} !important;
        }}
        .stMultiSelect [data-baseweb="tag"] {{
            background: {colors['accent']}40 !important;
            color: {colors['text']} !important;
        }}
        
        /* Slider */
        .stSlider label, .stSlider p, .stSelectSlider label, .stColorPicker label {{
            color: {colors['text']} !important;
        }}
        
        /* Code/JSON */
        .stCodeBlock, .stJson {{
            background: {colors['input_bg']} !important;
        }}
        
        /* Tabs content */
        .stTabs [data-baseweb="tab-panel"] p,
        .stTabs [data-baseweb="tab-panel"] span,
        .stTabs [data-baseweb="tab-panel"] label {{
            color: {colors['text']} !important;
        }}
        
        /* Toast/Popover/Menu - FIXED DROPDOWN VISIBILITY */
        .stToast {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
            border: 1px solid {colors['border']} !important;
        }}
        [data-baseweb="popover"], 
        [data-baseweb="menu"],
        [data-baseweb="popover"] ul,
        [data-baseweb="menu"] ul {{
            background: {colors['select_bg']} !important;
            border: 1px solid {colors['select_border']} !important;
            border-radius: 10px !important;
        }}
        [data-baseweb="popover"] *, 
        [data-baseweb="menu"] li,
        [data-baseweb="menu"] li span,
        [data-baseweb="menu"] li div {{
            color: {colors['text']} !important;
            background: transparent !important;
        }}
        [data-baseweb="menu"] li {{
            background: {colors['select_bg']} !important;
            padding: 10px 14px !important;
        }}
        [data-baseweb="menu"] li:hover {{
            background: {colors['border']} !important;
        }}
        [data-baseweb="menu"] li[aria-selected="true"],
        [data-baseweb="menu"] li[data-highlighted="true"] {{
            background: {colors['accent']}40 !important;
        }}
        /* Dropdown list container */
        [data-baseweb="listbox"],
        [role="listbox"] {{
            background: {colors['select_bg']} !important;
            border: 1px solid {colors['select_border']} !important;
        }}
        [data-baseweb="listbox"] li,
        [role="option"] {{
            background: {colors['select_bg']} !important;
            color: {colors['text']} !important;
        }}
        [data-baseweb="listbox"] li:hover,
        [role="option"]:hover {{
            background: {colors['border']} !important;
        }}
        
        /* ENHANCED DROPDOWN VISIBILITY - Fix white dropdown issue */
        div[data-baseweb="select"] > div {{
            background: {colors['select_bg']} !important;
            color: {colors['text']} !important;
        }}
        div[data-baseweb="select"] > div > div {{
            background: {colors['select_bg']} !important;
            color: {colors['text']} !important;
        }}
        [data-baseweb="select"] input {{
            color: {colors['text']} !important;
            background: transparent !important;
        }}
        /* Dropdown popup container */
        div[data-baseweb="popover"] > div {{
            background: {colors['select_bg']} !important;
            border: 2px solid {colors['accent']} !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
        }}
        /* All dropdown options */
        ul[role="listbox"] {{
            background: {colors['select_bg']} !important;
            max-height: 300px !important;
        }}
        li[role="option"] {{
            background: {colors['select_bg']} !important;
            color: {colors['text']} !important;
            padding: 10px 12px !important;
            border-bottom: 1px solid {colors['border']}40 !important;
        }}
        li[role="option"]:hover,
        li[role="option"][aria-selected="true"] {{
            background: {colors['accent']}30 !important;
        }}
        li[role="option"] * {{
            color: {colors['text']} !important;
        }}
        
        /* Progress Bar */
        .stProgress > div > div {{
            background: linear-gradient(90deg, {colors['accent']} 0%, {colors['accent_light']} 100%);
        }}
        
        /* Links */
        a {{
            color: {colors['accent']} !important;
        }}
        a:hover {{
            color: {colors['accent_light']} !important;
        }}
        
        /* ===== COMPREHENSIVE TEXT VISIBILITY FIXES ===== */
        
        /* File Uploader - Force all text visible */
        .stFileUploader [class*="st-emotion-cache"] {{
            background: {colors['input_bg']} !important;
            color: {colors['text']} !important;
        }}
        .stFileUploader section {{
            background: {colors['input_bg']} !important;
            border: 2px dashed {colors['accent']} !important;
        }}
        .stFileUploader section > div {{
            background: {colors['input_bg']} !important;
        }}
        .stFileUploader section span,
        .stFileUploader section p,
        .stFileUploader section div {{
            color: {colors['text']} !important;
            background: transparent !important;
        }}
        
        /* All form labels - ensure visibility */
        label[data-testid],
        div[data-testid] label,
        .stTextInput label p,
        .stTextArea label p,
        .stSelectbox label p,
        .stMultiSelect label p,
        .stNumberInput label p,
        .stFileUploader label p {{
            color: {colors['text']} !important;
        }}
        
        /* Input placeholders */
        input::placeholder,
        textarea::placeholder {{
            color: {colors['text_secondary']} !important;
            opacity: 0.7 !important;
        }}
        
        /* All spans inside form controls */
        .stTextInput span,
        .stTextArea span,
        .stSelectbox span,
        .stNumberInput span,
        .stFileUploader span {{
            color: {colors['text']} !important;
        }}
        
        /* Expander headers and content */
        .streamlit-expanderHeader {{
            color: {colors['text']} !important;
            background: {colors['input_bg']} !important;
        }}
        .streamlit-expanderHeader p,
        .streamlit-expanderHeader span {{
            color: {colors['text']} !important;
        }}
        details summary {{
            color: {colors['text']} !important;
        }}
        details summary span {{
            color: {colors['text']} !important;
        }}
        
        /* Caption text */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {colors['text_secondary']} !important;
        }}
        
        /* Small/secondary text elements */
        small, .st-emotion-cache-18mdfce {{
            color: {colors['text_secondary']} !important;
        }}
        
        /* Widget container backgrounds */
        [data-testid="stWidgetLabel"] {{
            color: {colors['text']} !important;
        }}
        [data-testid="stWidgetLabel"] p {{
            color: {colors['text']} !important;
        }}
        
        /* Form submit button area - GLASS EFFECT */
        .stForm {{
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
        }}
        
        /* Column backgrounds - ensure they don't override */
        [data-testid="column"] {{
            background: transparent !important;
        }}
        
        /* Subheader text */
        .stSubheader {{
            color: {colors['text']} !important;
        }}
        
        /* Help tooltips */
        [data-testid="stTooltipIcon"] {{
            color: {colors['text_secondary']} !important;
        }}
        
        /* Element containers */
        .element-container {{
            color: {colors['text']} !important;
        }}
        
        /* Ensure all white backgrounds in dark theme are fixed */
        {''.join([f'''
        .st-emotion-cache-k2xjt {{
            background-color: {colors['input_bg']} !important;
        }}
        ''' if is_dark else ''])}
        
        /* ========== GLASSMORPHISM EFFECTS (ALL THEMES) ========== */
        
        /* Glass Cards/Containers */
        [data-testid="stExpander"],
        div[data-testid="metric-container"],
        .stAlert {{
            background: rgba({colors['accent']}, 0.03) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.05),
                0 4px 20px rgba(0, 0, 0, 0.15) !important;
        }}
        
        /* Glass Inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stMultiSelect > div > div,
        .stNumberInput > div > div > input {{
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        
        /* Glass Buttons */
        .stButton > button {{
            background: rgba(255, 255, 255, 0.04) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border: 1px solid {colors['accent']}50 !important;
            box-shadow: 0 4px 15px {colors['accent']}30, inset 0 1px 0 rgba(255,255,255,0.08) !important;
        }}
        .stButton > button:hover {{
            background: rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 6px 25px {colors['accent']}50, 0 0 30px {colors['accent']}25, inset 0 1px 0 rgba(255,255,255,0.12) !important;
        }}
        
        /* Glass Active Tab */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 20px {colors['accent']}35 !important;
            border-bottom: 3px solid {colors['accent']} !important;
        }}
        
        /* Glass Progress Bar */
        .stProgress > div > div {{
            background: rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(5px) !important;
        }}
        .stProgress > div > div > div {{
            box-shadow: 0 0 15px {colors['accent']}50, 0 0 30px {colors['accent']}25 !important;
        }}
        
        /* Glass Inputs on Focus */
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            background: rgba(255, 255, 255, 0.06) !important;
            border-color: {colors['accent']} !important;
            box-shadow: 0 0 0 3px {colors['accent']}25, 0 0 25px {colors['accent']}20 !important;
        }}
        
        /* Glass Sliders */
        .stSlider > div > div > div > div {{
            box-shadow: 0 0 10px {colors['accent']}40 !important;
        }}
        .stSlider > div > div > div > div[role="slider"]:hover {{
            box-shadow: 0 0 20px {colors['accent']}60 !important;
        }}
        
        /* Glass Expanders on Hover */
        [data-testid="stExpander"]:hover {{
            background: rgba(255, 255, 255, 0.05) !important;
            box-shadow: 0 8px 30px {colors['accent']}15, inset 0 1px 0 rgba(255,255,255,0.08) !important;
            border-color: {colors['accent']}40 !important;
        }}
        
        /* Glass Metrics */
        div[data-testid="metric-container"]:hover {{
            background: rgba(255, 255, 255, 0.06) !important;
            box-shadow: 0 10px 35px {colors['accent']}20, inset 0 1px 0 rgba(255,255,255,0.1) !important;
        }}
        
        /* Glass File Uploader */
        .stFileUploader > div {{
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(8px) !important;
            border: 1px dashed rgba(255, 255, 255, 0.15) !important;
        }}
        .stFileUploader > div:hover {{
            background: rgba(255, 255, 255, 0.05) !important;
            box-shadow: 0 5px 25px {colors['accent']}20 !important;
            border-color: {colors['accent']}60 !important;
        }}
        
        /* Glass Select Dropdowns */
        .stSelectbox > div > div:hover,
        .stMultiSelect > div > div:hover {{
            background: rgba(255, 255, 255, 0.05) !important;
            box-shadow: 0 0 15px {colors['accent']}20 !important;
        }}
        
        /* Glass Alerts */
        .stSuccess {{
            background: rgba(34, 197, 94, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 20px rgba(34, 197, 94, 0.25) !important;
        }}
        .stError {{
            box-shadow: 0 4px 20px rgba(239, 68, 68, 0.3) !important;
        }}
        .stWarning {{
            box-shadow: 0 4px 20px rgba(234, 179, 8, 0.3) !important;
        }}
        .stInfo {{
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3) !important;
        }}
        
        /* Glowing Sidebar Border */
        [data-testid="stSidebar"] {{
            box-shadow: 4px 0 25px {colors['accent']}10 !important;
        }}
        
        /* ========== END THEME-SPECIFIC GLOW ========== */
        
        /* Neon Jelly Theme Special Effects */
        {''.join([f'''
        /* Glowing progress bars */
        .stProgress > div > div > div {{
            background: linear-gradient(90deg, #4a4a4a 0%, #6b6b6b 40%, #c8ff00 70%, #e0ff66 100%) !important;
            box-shadow: 0 0 20px rgba(200, 255, 0, 0.6), 0 0 40px rgba(200, 255, 0, 0.3) !important;
            border-radius: 20px !important;
        }}
        .stProgress > div > div {{
            background: #3d3d3d !important;
            border-radius: 20px !important;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5) !important;
        }}
        
        /* Glowing buttons */
        .stButton > button {{
            background: linear-gradient(135deg, #1a2a10 0%, #2d4a15 50%, #c8ff00 100%) !important;
            border: 1px solid #c8ff00 !important;
            box-shadow: 0 0 15px rgba(200, 255, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
            transition: all 0.3s ease !important;
        }}
        .stButton > button:hover {{
            box-shadow: 0 0 25px rgba(200, 255, 0, 0.7), 0 0 50px rgba(200, 255, 0, 0.3) !important;
            transform: translateY(-2px) !important;
        }}
        
        /* Glowing cards/expanders */
        [data-testid="stExpander"] {{
            border: 1px solid rgba(200, 255, 0, 0.3) !important;
            box-shadow: 0 0 10px rgba(200, 255, 0, 0.1) !important;
        }}
        [data-testid="stExpander"]:hover {{
            box-shadow: 0 0 20px rgba(200, 255, 0, 0.2) !important;
        }}
        
        /* Glowing inputs */
        .stTextInput input:focus, .stTextArea textarea:focus {{
            border-color: #c8ff00 !important;
            box-shadow: 0 0 10px rgba(200, 255, 0, 0.3) !important;
        }}
        
        /* Glowing tabs */
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, #1a2a10, #2d4a15) !important;
            border-bottom: 3px solid #c8ff00 !important;
            box-shadow: 0 4px 15px rgba(200, 255, 0, 0.3) !important;
        }}
        
        /* Jelly slider animation */
        @keyframes jellyGlow {{
            0%, 100% {{ box-shadow: 0 0 15px rgba(200, 255, 0, 0.4); }}
            50% {{ box-shadow: 0 0 30px rgba(200, 255, 0, 0.7); }}
        }}
        .stSlider > div > div > div > div {{
            background: linear-gradient(90deg, #4a4a4a, #c8ff00) !important;
            animation: jellyGlow 2s ease-in-out infinite !important;
        }}
        ''' if theme_name == 'Neon Jelly' else ''])}
        
        {(''.join(['''
        /* ========== GLASS THEME SPECIAL EFFECTS ========== */
        
        /* Glassmorphism blur effect on all containers */
        .stApp {
            backdrop-filter: blur(20px) !important;
        }
        
        /* Glass sidebar */
        section[data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.7) !important;
            backdrop-filter: blur(20px) saturate(180%) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.15) !important;
        }
        
        /* Glass cards */
        .stMetric, .stExpander, [data-testid="stMetricValue"] {
            background: rgba(30, 41, 59, 0.4) !important;
            backdrop-filter: blur(15px) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            border-radius: 12px !important;
        }
        
        /* Glass buttons */
        .stButton > button {
            background: rgba(59, 130, 246, 0.2) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(96, 165, 250, 0.4) !important;
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2) !important;
            transition: all 0.3s ease !important;
        }
        .stButton > button:hover {
            background: rgba(59, 130, 246, 0.4) !important;
            box-shadow: 0 8px 30px rgba(59, 130, 246, 0.3) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Glass inputs - WITH TEXT COLOR FIX */
        input, textarea, select, [data-baseweb="select"] {
            background: rgba(30, 41, 59, 0.5) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            color: #e2e8f0 !important;
        }
        input::placeholder, textarea::placeholder {
            color: rgba(148, 163, 184, 0.7) !important;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox select {
            color: #e2e8f0 !important;
        }
        [data-baseweb="input"] input {
            color: #e2e8f0 !important;
        }
        [data-baseweb="select"] span, [data-baseweb="select"] div {
            color: #e2e8f0 !important;
        }
        }
        
        /* Glass tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(30, 41, 59, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 10px !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: rgba(59, 130, 246, 0.3) !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
        }
        
        /* Floating orbs for ambiance */
        .stApp::before {
            content: "";
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%);
            border-radius: 50%;
            top: -100px;
            right: -100px;
            z-index: -1;
            filter: blur(60px);
            pointer-events: none;
        }
        .stApp::after {
            content: "";
            position: fixed;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.25) 0%, transparent 70%);
            border-radius: 50%;
            bottom: -80px;
            left: -80px;
            z-index: -1;
            filter: blur(50px);
            pointer-events: none;
        }
        ''' if theme_name == 'Glass' else '']))}
    """
    
    return theme_css


def inject_custom_css(theme_name: str = "Dragon Dark"):
    """Inject custom CSS based on theme."""
    
    # Common CSS (shared between all themes)
    common_css = """
        /* Dragon Mailer - Premium Theme 2026 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Hide Streamlit Branding */
        #MainMenu, footer, header {visibility: hidden;}
        
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
        
        /* ========== MODERN SELECTION HIGHLIGHT ========== */
        ::selection {
            background: rgba(249, 115, 22, 0.4);
            color: #ffffff;
        }
        ::-moz-selection {
            background: rgba(249, 115, 22, 0.4);
            color: #ffffff;
        }
        
        /* ========== SMOOTH FOCUS RINGS ========== */
        *:focus {
            outline: none;
        }
        *:focus-visible {
            outline: 2px solid rgba(249, 115, 22, 0.6);
            outline-offset: 2px;
            border-radius: 8px;
        }
        
        /* ========== DRAGON LOGO ========== */
        
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
        
        .dragon-head { fill: #f97316; }
        .dragon-horn { fill: #ea580c; }
        .dragon-pupil { fill: #1f2937; }
        .dragon-fire { opacity: 1; }
        
        .dragon-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: #fbbf24;
            text-shadow: 0 2px 20px rgba(249, 115, 22, 0.5);
            letter-spacing: 0.02em;
        }
        
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
        
        .tagline strong {
            color: #fbbf24 !important;
        }
        
        /* ========== END DRAGON LOGO ========== */
        
        /* ========== HIDE "Press Enter to apply" HINT ========== */
        .stTextInput [data-testid="InputInstructions"],
        .stTextInput div[data-testid="InputInstructions"],
        .stTextArea [data-testid="InputInstructions"],
        .stTextArea div[data-testid="InputInstructions"],
        [data-testid="stTextInput"] [data-testid="InputInstructions"],
        [data-testid="stTextArea"] [data-testid="InputInstructions"],
        .stTextInput small,
        .stTextArea small {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            overflow: hidden !important;
        }
        /* Also hide the instruction text that says "Press Enter to apply" */
        div[class*="instructions"] {
            display: none !important;
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

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            padding: 8px;
            border-radius: 14px;
            flex-wrap: wrap;
        }
        .stTabs [data-baseweb="tab"] {
            height: auto;
            min-height: 40px;
            background-color: transparent;
            border-radius: 10px;
            border: none;
            font-weight: 500;
            font-size: 0.85rem;
            padding: 8px 12px;
            transition: all 0.2s ease;
            white-space: nowrap;
            overflow: visible;
        }

        /* Input Fields */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            border-radius: 10px !important;
            padding: 0.7rem 1rem !important;
            font-size: 0.95rem !important;
            transition: all 0.2s ease !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.3) !important;
        }
        
        /* UNIVERSAL INPUT TEXT VISIBILITY - Ensures text is always visible */
        .stTextInput input,
        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stTextArea > div > div > textarea,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
        }
        .stSelectbox [data-baseweb="select"] > div,
        .stSelectbox [data-baseweb="select"] span,
        .stMultiSelect [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] span {
            color: inherit !important;
        }
        
        /* Labels */
        .stTextInput label, .stSelectbox label, .stTextArea label {
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            margin-bottom: 0.4rem !important;
            letter-spacing: 0.01em;
        }

        /* Buttons - Modern glassmorphism */
        .stButton > button {
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.95rem;
            padding: 0.75rem 1.75rem;
            border: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            color: white;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            letter-spacing: 0.02em;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .stButton > button:active {
            transform: translateY(0) scale(0.98);
        }
        
        /* Primary action buttons (Send, Submit) glow */
        .stButton > button[kind="primary"],
        .stButton > button:first-of-type {
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.3);
        }
        
        /* Expanders - Modern card style */
        .streamlit-expanderHeader {
            border-radius: 12px;
            font-weight: 600;
            padding: 0.85rem 1.1rem;
        }
        .streamlit-expanderContent {
            border-top: none;
            border-radius: 0 0 10px 10px;
            padding: 1.25rem;
        }
        
        /* Metrics */
        div[data-testid="metric-container"] {
            padding: 1.5rem;
            border-radius: 12px;
        }
        div[data-testid="metric-container"] label {
            font-weight: 500 !important;
            font-size: 0.85rem !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-weight: 700 !important;
            font-size: 2rem !important;
        }
        
        /* Alerts - Modern styling */
        .stAlert {
            border-radius: 12px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }
        
        /* Dividers - Gradient effect */
        hr {
            border: none;
            height: 1px;
            margin: 1.5rem 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        }
        
        /* File Uploader */
        .stFileUploader > div {
            border-radius: 12px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Progress Bar */
        .stProgress > div > div {
            border-radius: 999px;
            overflow: hidden;
        }
        
        /* Modern Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, rgba(255,255,255,0.3), rgba(255,255,255,0.1));
            border-radius: 10px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, rgba(255,255,255,0.5), rgba(255,255,255,0.2));
        }
        
        /* Firefox Scrollbar */
        * {
            scrollbar-width: thin;
            scrollbar-color: rgba(255,255,255,0.3) rgba(0,0,0,0.1);
        }
        
        /* Data Tables - Modern card style */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        /* Column styling - Better spacing */
        div[data-testid="column"] {
            padding: 0.5rem;
        }
        
        /* Column gaps on mobile */
        @media (max-width: 768px) {
            div[data-testid="column"] {
                padding: 0.25rem 0;
            }
        }
        
        /* Number/Date/Time inputs */
        .stNumberInput input, .stDateInput input, .stTimeInput input {
            border-radius: 12px !important;
        }
        
        /* Tooltips - Modern style */
        [data-baseweb="tooltip"] {
            background: rgba(15, 23, 42, 0.95) !important;
            backdrop-filter: blur(10px) !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3) !important;
        }
        
        /* Popover menus */
        [data-baseweb="popover"] {
            background: rgba(15, 23, 42, 0.95) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4) !important;
            overflow: hidden;
        }
        
        /* Dropdown menus */
        [data-baseweb="menu"], [data-baseweb="select"] ul {
            background: rgba(15, 23, 42, 0.95) !important;
            backdrop-filter: blur(15px) !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            box-shadow: 0 15px 50px rgba(0,0,0,0.35) !important;
            padding: 6px !important;
        }
        
        /* Dropdown options */
        [data-baseweb="menu"] li, [role="option"] {
            border-radius: 8px !important;
            margin: 2px 0 !important;
            transition: all 0.2s ease !important;
        }
        [data-baseweb="menu"] li:hover, [role="option"]:hover {
            background: rgba(249, 115, 22, 0.2) !important;
        }
        
        /* Multiselect */
        .stMultiSelect > div > div {
            border-radius: 10px !important;
        }
        
        /* Empty state text */
        .stEmpty {
            color: #d4d4d4 !important;
        }
        
        /* ========== UNIVERSAL MOTION & GLOW EFFECTS ========== */
        
        /* Keyframe Animations */
        @keyframes subtleGlow {
            0%, 100% { filter: brightness(1); }
            50% { filter: brightness(1.05); }
        }
        
        @keyframes pulseGlow {
            0%, 100% { box-shadow: 0 0 5px currentColor; }
            50% { box-shadow: 0 0 15px currentColor, 0 0 25px currentColor; }
        }
        
        @keyframes floatUp {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }
        
        @keyframes shimmer {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }
        
        @keyframes borderGlow {
            0%, 100% { border-color: rgba(255, 255, 255, 0.1); }
            50% { border-color: rgba(255, 255, 255, 0.3); }
        }
        
        @keyframes scalePress {
            0% { transform: scale(1); }
            50% { transform: scale(0.97); }
            100% { transform: scale(1); }
        }
        
        /* Animated Buttons */
        .stButton > button {
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3), 0 0 20px rgba(255, 255, 255, 0.1) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) scale(0.98) !important;
            transition: transform 0.1s !important;
        }
        
        /* Animated Input Fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stMultiSelect > div > div,
        .stNumberInput > div > div > input {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            transform: scale(1.01) !important;
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1), 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Animated Tabs */
        .stTabs [data-baseweb="tab"] {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative;
            overflow: hidden;
        }
        
        .stTabs [data-baseweb="tab"]::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            width: 0;
            height: 2px;
            background: currentColor;
            transition: all 0.3s ease;
            transform: translateX(-50%);
        }
        
        .stTabs [data-baseweb="tab"]:hover::after {
            width: 80%;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-2px) !important;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            animation: subtleGlow 3s ease-in-out infinite !important;
        }
        
        /* Animated Expanders */
        [data-testid="stExpander"] {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        [data-testid="stExpander"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2) !important;
        }
        
        .streamlit-expanderHeader {
            transition: all 0.3s ease !important;
        }
        
        .streamlit-expanderHeader:hover {
            padding-left: 1.3rem !important;
        }
        
        /* Animated Metrics */
        div[data-testid="metric-container"] {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            animation: subtleGlow 4s ease-in-out infinite;
        }
        
        div[data-testid="metric-container"]:hover {
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25) !important;
        }
        
        /* Animated Progress Bar */
        .stProgress > div > div > div {
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
            animation: subtleGlow 2s ease-in-out infinite !important;
            position: relative;
            overflow: hidden;
        }
        
        .stProgress > div > div > div::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
            background-size: 200% 100%;
        }
        
        /* Animated Sliders */
        .stSlider > div > div > div > div {
            transition: all 0.3s ease !important;
        }
        
        .stSlider > div > div > div > div[role="slider"] {
            transition: transform 0.2s ease, box-shadow 0.3s ease !important;
        }
        
        .stSlider > div > div > div > div[role="slider"]:hover {
            transform: scale(1.2) !important;
            box-shadow: 0 0 15px currentColor !important;
        }
        
        /* Animated Checkboxes & Radio */
        .stCheckbox > label,
        .stRadio > div > label {
            transition: all 0.2s ease !important;
        }
        
        .stCheckbox > label:hover,
        .stRadio > div > label:hover {
            transform: translateX(3px) !important;
        }
        
        /* Animated File Uploader */
        .stFileUploader > div {
            transition: all 0.3s ease !important;
        }
        
        .stFileUploader > div:hover {
            transform: scale(1.01) !important;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Animated Alerts */
        .stAlert {
            animation: floatUp 0.5s ease-out;
            transition: all 0.3s ease !important;
        }
        
        .stAlert:hover {
            transform: translateX(5px) !important;
        }
        
        /* Animated Sidebar */
        [data-testid="stSidebar"] {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        [data-testid="stSidebar"] > div:first-child {
            transition: all 0.3s ease !important;
        }
        
        /* Animated Data Tables */
        .stDataFrame {
            transition: all 0.3s ease !important;
        }
        
        .stDataFrame:hover {
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Animated Select Options */
        [data-baseweb="select"] [role="option"] {
            transition: all 0.15s ease !important;
        }
        
        [data-baseweb="select"] [role="option"]:hover {
            transform: translateX(5px) !important;
        }
        
        /* Smooth Page Transitions */
        .main .block-container {
            animation: fadeIn 0.4s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* ========== END UNIVERSAL MOTION EFFECTS ========== */
    """
    
    theme_css = get_theme_css(theme_name)
    st.markdown(f"<style>{common_css}{theme_css}</style>", unsafe_allow_html=True)


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
    
    # Load settings
    settings = load_settings()
    current_theme = settings.get("theme", "Dragon Dark")
    
    # Initialize session states
    if 'sending_results' not in st.session_state:
        st.session_state.sending_results = []
    if 'current_smtp' not in st.session_state:
        st.session_state.current_smtp = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_theme' not in st.session_state:
        st.session_state.current_theme = current_theme
    
    # Inject Custom CSS with current theme
    inject_custom_css(st.session_state.current_theme)
    
    # Check for scheduled tasks (background check)
    check_and_execute_scheduled_tasks()
    
    # Login Protection
    if not check_login():
        show_login_page()
        return
    
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
        
        # 🎨 Theme Selector Dropdown
        theme_names = list(THEMES.keys())
        theme_icons = [f"{THEMES[t]['icon']} {t}" for t in theme_names]
        current_idx = theme_names.index(st.session_state.current_theme) if st.session_state.current_theme in theme_names else 0
        
        selected_theme_display = st.selectbox(
            "🎨 Theme",
            theme_icons,
            index=current_idx,
            key="theme_selector"
        )
        
        # Extract theme name from display string
        selected_theme = selected_theme_display.split(" ", 1)[1] if " " in selected_theme_display else selected_theme_display
        
        if selected_theme != st.session_state.current_theme:
            st.session_state.current_theme = selected_theme
            settings["theme"] = selected_theme
            save_settings(settings)
            st.rerun()
        
        st.markdown("---")
        
        # Stats
        history = load_sent_messages()
        today = datetime.now().strftime("%Y-%m-%d")
        today_msgs = [m for m in history if m.get('timestamp', '').startswith(today)]
        
        col1, col2 = st.columns(2)
        col1.metric("Total Sent", len(history))
        col2.metric("Today", len(today_msgs))
        
        # Scheduled tasks count
        scheduled = load_scheduled_tasks()
        pending_tasks = [t for t in scheduled if t.get("status") == "pending"]
        if pending_tasks:
            st.metric("⏰ Scheduled", len(pending_tasks))
        
        st.markdown("---")
        st.info("**Quick Tip:**\nUse the 'SMTP Settings' tab to configure your email providers before sending.")
        
        st.markdown("---")
        
        # User info and Logout button (if login is enabled)
        if settings.get("login_enabled", False) and st.session_state.get("authenticated", False):
            current_user = st.session_state.get("current_user", "User")
            user_role = st.session_state.get("user_role", "user")
            role_icon = "👑" if user_role == "admin" else "👤"
            
            st.markdown(f"**{role_icon} Logged in as:**")
            st.markdown(f"**{current_user}**")
            
            if st.button("🚪 Logout"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.user_role = None
                st.rerun()
        
        st.caption(f"v2.0 | {datetime.now().year}")

    # Tagline only - logo is in sidebar
    st.markdown("<p class='tagline'>🔥 <strong>Powerful Bulk Messaging Suite</strong> - Breathe fire into your email campaigns.</p>", unsafe_allow_html=True)
    
    # Create tabs
    tabs = st.tabs([
        "📤 Send Email",
        "📱 Send SMS",
        "☁️ Azure SMS",
        "⏰ Scheduled",
        "⚙️ SMTP Settings", 
        "👥 Recipients",
        "📊 History",
        "📈 Tracking",
        "🔧 Settings",
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
            
            # Email Templates with auto-fill
            st.markdown("**📝 Quick Templates**")
            
            email_templates = {
                "-- Select Template --": {"subject": "", "body": ""},
                "🔐 Verification Code": {
                    "subject": "Your Verification Code",
                    "body": "Your verification code is {random_digit:6}.\n\nThis code expires in 10 minutes.\nDo not share this code with anyone.\n\nIf you didn't request this, please ignore this email."
                },
                "🔐 OTP Code": {
                    "subject": "Your One-Time Password",
                    "body": "Your OTP is {random_digit:6}.\n\nUse this code to complete your login.\nExpires in 5 minutes.\n\nIf this wasn't you, secure your account immediately."
                },
                "📦 Order Confirmation": {
                    "subject": "Order Confirmed - #{random_upper:8}",
                    "body": "Thank you for your order!\n\nOrder ID: #{random_upper:8}\nDate: {date}\n\nTrack your order: {link}\n\nThank you for shopping with us!"
                },
                "📦 Shipping Notification": {
                    "subject": "Your Order Has Been Shipped!",
                    "body": "Great news! Your order is on its way!\n\nTracking Number: {random_upper:12}\nTrack here: {link}\n\nEstimated delivery: 3-5 business days."
                },
                "💳 Transaction Alert": {
                    "subject": "Transaction Alert - Action Required",
                    "body": "A transaction was made on your account.\n\nAmount: ${random_digit:3}.{random_digit:2}\nDate: {date}\nTime: {time}\n\nIf you didn't make this transaction, secure your account: {link}"
                },
                "🔔 Appointment Reminder": {
                    "subject": "Reminder: Your Appointment Tomorrow",
                    "body": "This is a reminder for your upcoming appointment.\n\nDate: {date}\n\nPlease arrive 15 minutes early.\n\nNeed to reschedule? Click here: {link}"
                },
                "🎁 Promo Code": {
                    "subject": "Special Offer Just For You! 🎉",
                    "body": "Exclusive offer!\n\nUse code: {random_upper:8}\nGet 20% off your next order!\n\nShop now: {link}\n\nHurry, offer expires soon!"
                },
                "🔑 Password Reset": {
                    "subject": "Password Reset Request",
                    "body": "We received a request to reset your password.\n\nReset Code: {random_digit:6}\n\nClick here to reset: {link}\n\nThis link expires in 1 hour.\n\nIf you didn't request this, please ignore this email."
                },
                "✅ Account Verified": {
                    "subject": "Welcome! Your Account is Verified",
                    "body": "Congratulations! Your account has been verified.\n\nYou now have full access to all features.\n\nGet started: {link}\n\nWelcome aboard!"
                },
                "⚠️ Security Alert": {
                    "subject": "Security Alert: New Login Detected",
                    "body": "A new login was detected on your account.\n\nTime: {time}\nDate: {date}\n\nIf this was you, you can ignore this message.\nIf not, secure your account immediately: {link}"
                },
                "📧 Email Verification": {
                    "subject": "Verify Your Email Address",
                    "body": "Please verify your email address.\n\nVerification Code: {random_digit:6}\n\nOr click here: {link}\n\nThis code expires in 24 hours."
                },
                "🎉 Welcome Email": {
                    "subject": "Welcome to Our Platform!",
                    "body": "Welcome!\n\nWe're excited to have you on board.\n\nHere's what you can do next:\n- Complete your profile\n- Explore features\n- Get help: {link}\n\nBest regards,\nThe Team"
                },
                "💰 Payment Confirmation": {
                    "subject": "Payment Received - Thank You!",
                    "body": "We've received your payment!\n\nAmount: ${random_digit:3}.{random_digit:2}\nTransaction ID: {random_upper:10}\nDate: {date}\n\nView receipt: {link}"
                },
                "📢 Newsletter": {
                    "subject": "This Week's Updates",
                    "body": "Here's what's new this week!\n\n• New features released\n• Exciting announcements\n• Tips and tricks\n\nRead more: {link}\n\nStay tuned for more updates!"
                },
                "🔗 Custom Link Only": {
                    "subject": "Check This Out!",
                    "body": "We thought you might find this interesting:\n\n{link}\n\nLet us know what you think!"
                },
                "📲 Account Activation": {
                    "subject": "Activate Your Account",
                    "body": "Your account is almost ready!\n\nActivation Code: {random_digit:6}\n\nActivate now: {link}\n\nThis link expires in 48 hours."
                },
                "🎫 Event Registration": {
                    "subject": "Registration Confirmed!",
                    "body": "You're registered!\n\nConfirmation #: {random_upper:8}\nDate: {date}\n\nView your ticket: {link}\n\nWe look forward to seeing you!"
                },
                "💼 Invoice": {
                    "subject": "Invoice #{random_digit:6}",
                    "body": "Your invoice is ready.\n\nInvoice #: {random_digit:6}\nAmount Due: ${random_digit:3}.{random_digit:2}\nDue Date: {date}\n\nPay now: {link}"
                },
                "📱 2FA Setup": {
                    "subject": "Two-Factor Authentication Setup",
                    "body": "Set up 2FA to secure your account.\n\nSetup Code: {random_digit:6}\n\nOr scan the QR code: {link}\n\nThis code expires in 15 minutes."
                },
                "🏆 Reward Earned": {
                    "subject": "Congratulations! You Earned a Reward!",
                    "body": "You've earned a reward!\n\nReward Code: {random_upper:10}\n\nRedeem now: {link}\n\nValid until: {date}"
                },
                "📋 Survey Request": {
                    "subject": "We'd Love Your Feedback!",
                    "body": "Help us improve!\n\nTake our quick survey: {link}\n\nYour feedback is valuable to us.\n\nThank you!"
                },
                "🔄 Subscription Renewal": {
                    "subject": "Subscription Renewal Notice",
                    "body": "Your subscription is up for renewal.\n\nRenewal Date: {date}\nAmount: ${random_digit:2}.99\n\nManage subscription: {link}"
                },
                "📤 File Shared": {
                    "subject": "A File Has Been Shared With You",
                    "body": "Someone shared a file with you!\n\nAccess it here: {link}\n\nThis link expires in 7 days."
                },
                "🎂 Birthday Greeting": {
                    "subject": "Happy Birthday! 🎉",
                    "body": "Happy Birthday!\n\nWishing you a wonderful day!\n\nHere's a special gift: {link}\n\nCelebrate with us!"
                },
                "📅 Meeting Invitation": {
                    "subject": "You're Invited to a Meeting",
                    "body": "You've been invited to a meeting.\n\nDate: {date}\nTime: {time}\n\nJoin here: {link}\n\nSee you there!"
                }
            }
            
            # Initialize session state for email template tracking
            if 'email_subject_text' not in st.session_state:
                st.session_state.email_subject_text = ""
            if 'email_body_text' not in st.session_state:
                st.session_state.email_body_text = ""
            
            # Short link input for email templates
            email_custom_link = st.text_input(
                "🔗 Short Link (replaces {link} in template)",
                placeholder="https://yoursite.com/link",
                key="email_custom_link"
            )
            
            selected_email_template = st.selectbox(
                "Quick Templates (auto-fills subject & body)",
                options=list(email_templates.keys()),
                key="email_template_select"
            )
            
            # Update fields when template is selected
            if selected_email_template != "-- Select Template --":
                template_data = email_templates[selected_email_template]
                template_subject = template_data["subject"]
                template_body = template_data["body"]
                
                # Replace {link} if provided
                if email_custom_link:
                    template_subject = template_subject.replace("{link}", email_custom_link)
                    template_body = template_body.replace("{link}", email_custom_link)
                
                # Only update if template changed
                if st.session_state.get('last_email_template') != selected_email_template:
                    st.session_state.email_subject_text = template_subject
                    st.session_state.email_body_text = template_body
                    st.session_state.last_email_template = selected_email_template
                    st.session_state.email_original_subject = template_data["subject"]
                    st.session_state.email_original_body = template_data["body"]
            
            # Auto-replace {link} when user enters a link
            if email_custom_link and '{link}' in st.session_state.email_subject_text:
                st.session_state.email_subject_text = st.session_state.email_subject_text.replace("{link}", email_custom_link)
            if email_custom_link and '{link}' in st.session_state.email_body_text:
                st.session_state.email_body_text = st.session_state.email_body_text.replace("{link}", email_custom_link)
            
            # If link changed and we have original template, re-apply with new link
            if email_custom_link and st.session_state.get('last_email_link') != email_custom_link:
                if st.session_state.get('email_original_subject'):
                    st.session_state.email_subject_text = st.session_state.email_original_subject.replace("{link}", email_custom_link)
                if st.session_state.get('email_original_body'):
                    st.session_state.email_body_text = st.session_state.email_original_body.replace("{link}", email_custom_link)
                st.session_state.last_email_link = email_custom_link
            
            st.markdown("---")
            
            subject = st.text_input(
                "Subject",
                value=st.session_state.email_subject_text,
                placeholder="Enter email subject",
                key="email_subject"
            )
            st.session_state.email_subject_text = subject
            
            # Show link warning if {link} in subject/body but no link provided
            if ("{link}" in subject or "{link}" in st.session_state.email_body_text) and not email_custom_link:
                st.warning("⚠️ Your template contains `{link}` but no short link is provided above!")
            
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
                    value=st.session_state.email_body_text,
                    height=200,
                    placeholder="Type your plain text message here or select a template above...",
                    label_visibility="collapsed"
                )
                st.session_state.email_body_text = plain_message
            
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
            
            # Advanced Options Expander
            with st.expander("⚙️ Advanced Bulk Options", expanded=False):
                st.markdown("### 📦 BCC Batch Mode")
                col1, col2 = st.columns(2)
                with col1:
                    use_bcc_mode = st.checkbox(
                        "Enable BCC Mode",
                        key="use_bcc_mode",
                        value=False,
                        help="Send to multiple recipients via BCC (faster, fewer connections)"
                    )
                with col2:
                    bcc_batch_size = st.number_input(
                        "Recipients per batch",
                        min_value=1,
                        max_value=100,
                        value=50,
                        key="bcc_batch_size",
                        help="Number of recipients per BCC batch"
                    )
                
                st.markdown("### ⏱️ Send Delay (Anti-Rate Limit)")
                col1, col2 = st.columns(2)
                with col1:
                    delay_seconds = st.number_input(
                        "Delay (seconds)",
                        min_value=0.0,
                        max_value=60.0,
                        value=0.0,
                        step=0.5,
                        key="delay_seconds",
                        help="Pause between sends to avoid rate limits"
                    )
                with col2:
                    delay_every_n = st.number_input(
                        "Delay every N emails",
                        min_value=0,
                        max_value=1000,
                        value=0,
                        key="delay_every_n",
                        help="Apply delay every N emails (0 = after each batch/email)"
                    )
                
                st.markdown("### 🔄 SMTP Rotation")
                rotate_smtp = st.checkbox(
                    "Enable SMTP Rotation",
                    key="rotate_smtp",
                    value=False,
                    help="Rotate between multiple SMTP servers"
                )
                if rotate_smtp:
                    col1, col2 = st.columns(2)
                    with col1:
                        rotate_after_n = st.number_input(
                            "Rotate after N emails",
                            min_value=1,
                            max_value=10000,
                            value=100,
                            key="rotate_after_n",
                            help="Switch to next SMTP after sending N emails"
                        )
                    with col2:
                        all_smtp_names = list(load_smtp_configs().keys())
                        selected_smtps = st.multiselect(
                            "SMTP servers to rotate",
                            options=all_smtp_names,
                            default=[all_smtp_names[0]] if all_smtp_names else [],
                            key="rotation_smtps"
                        )
                else:
                    rotate_after_n = 0
                    selected_smtps = []
                
                st.markdown("### 🎲 Pattern Variables")
                enable_patterns = st.checkbox(
                    "Enable Pattern Replacement",
                    key="enable_patterns",
                    value=False,
                    help="Replace variables like {random}, {date}, {email} in your message"
                )
                if enable_patterns:
                    st.info("""
**Available Patterns:**
- `{random}` - 8 char random alphanumeric
- `{random:N}` - N char random (e.g., `{random:12}`)
- `{random_lower}` / `{random_upper}` / `{random_digit}`
- `{random_digit:N}` - N random digits (great for codes!)
- `{date}` - Current date (YYYY-MM-DD)
- `{time}` - Current time (HH:MM)
- `{uuid}` - Unique identifier
- `{email}` - Recipient's email
- `{name}` - Name extracted from email
                    """)
            
            # Send Button
            st.markdown("---")
            if st.button("📤 Send Emails", key="send_email_btn"):
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
                    
                    # Progress bar - uses Jelly style for Neon Jelly theme
                    progress_bar = JellyProgressBar(label="Sending Emails")
                    status_text = st.empty()
                    
                    def update_progress(pct):
                        progress_bar.progress(pct)
                        status_text.text(f"Sending... {int(pct * 100)}% ({int(pct * len(all_recipients))}/{len(all_recipients)})")
                    
                    status_text.text(f"Sending to {len(all_recipients)} recipients...")
                    
                    # Check if advanced mode should be used
                    use_advanced = use_bcc_mode or delay_seconds > 0 or rotate_smtp or enable_patterns
                    
                    if use_advanced:
                        # Build SMTP configs for rotation
                        if rotate_smtp and selected_smtps:
                            smtp_config_list = []
                            all_configs = load_smtp_configs()
                            for smtp_name in selected_smtps:
                                if smtp_name in all_configs:
                                    cfg = all_configs[smtp_name].copy()
                                    cfg['email'] = sender_email
                                    cfg['password'] = sender_password
                                    smtp_config_list.append(cfg)
                        else:
                            smtp_config_list = [{
                                'server': config['server'],
                                'port': config['port'],
                                'email': sender_email,
                                'password': sender_password,
                                'use_tls': config.get('use_tls', True),
                                'use_ssl': config.get('use_ssl', False),
                                'no_auth': config.get('no_auth', False)
                            }]
                        
                        results = send_bulk_email_advanced(
                            smtp_configs=smtp_config_list,
                            recipient_emails=all_recipients,
                            subject=subject,
                            message=plain_message or "This email requires an HTML-capable email client.",
                            html_content=final_html,
                            attachments=attachments if attachments else None,
                            use_bcc=use_bcc_mode,
                            bcc_batch_size=bcc_batch_size,
                            delay_seconds=delay_seconds,
                            delay_every_n_emails=delay_every_n,
                            rotate_after_n_emails=rotate_after_n if rotate_smtp else 0,
                            enable_tracking=enable_tracking,
                            enable_patterns=enable_patterns,
                            progress_callback=update_progress,
                            sender_name=sender_name
                        )
                    else:
                        # Standard send
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
            
            # Quick paste option - PRIMARY method
            st.markdown("**📝 Quick Paste (Just Numbers)**")
            quick_paste = st.text_area(
                "Paste phone numbers (one per line)",
                height=120,
                key="sms_quick_paste",
                placeholder="5551234567\n5559876543\n(555) 111-2222\n+1 555-333-4444",
                help="Just paste numbers - carrier will be auto-detected!"
            )
            
            # Default carrier for quick paste
            default_carrier = st.selectbox(
                "Default Carrier",
                options=list(SMS_GATEWAYS.keys()),
                index=0,  # "Auto (Try All)" is first
                key="sms_default_carrier",
                help="'Auto (Try All)' will try Verizon, T-Mobile, AT&T, Sprint until one works"
            )
            
            st.markdown("---")
            
            # Advanced options - Upload or Manual
            with st.expander("📁 Advanced: Upload CSV or Manual Entry", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Upload Recipients (CSV/TXT)**")
                    st.caption("Format: phone_number OR phone_number,carrier")
                    uploaded_sms = st.file_uploader(
                        "Upload File",
                        type=['csv', 'txt'],
                        key="upload_sms_recipients"
                    )
                
                with col2:
                    st.markdown("**Manual Entry**")
                    if 'sms_entries' not in st.session_state:
                        st.session_state.sms_entries = [{"phone": "", "carrier": "Auto (Try All)"}]
                    
                    for i, entry in enumerate(st.session_state.sms_entries):
                        c1, c2, c3 = st.columns([3, 2, 1])
                        with c1:
                            phone = st.text_input(
                                f"Phone #{i+1}",
                                value=entry["phone"],
                                placeholder="(555) 123-4567",
                                key=f"sms_phone_{i}"
                            )
                        with c2:
                            carrier_list = list(SMS_GATEWAYS.keys())
                            default_idx = carrier_list.index(entry.get("carrier", "Auto (Try All)")) if entry.get("carrier", "Auto (Try All)") in carrier_list else 0
                            carrier = st.selectbox(
                                f"Carrier #{i+1}",
                                carrier_list,
                                index=default_idx,
                                key=f"sms_carrier_{i}"
                            )
                        with c3:
                            if i > 0:
                                if st.button("🗑️", key=f"sms_remove_{i}"):
                                    st.session_state.sms_entries.pop(i)
                                    st.rerun()
                        
                        if phone:
                            st.session_state.sms_entries[i] = {"phone": phone, "carrier": carrier}
                    
                    if st.button("➕ Add Another"):
                        st.session_state.sms_entries.append({"phone": "", "carrier": "Auto (Try All)"})
                        st.rerun()
            
            # Collect all recipients
            sms_recipients = []
            
            # First check quick paste (primary method)
            if quick_paste and quick_paste.strip():
                lines = quick_paste.strip().split('\n')
                for line in lines:
                    phone = line.strip()
                    if phone:
                        # Clean the number
                        clean = ''.join(filter(str.isdigit, phone))
                        if len(clean) >= 10:
                            sms_recipients.append((phone, default_carrier))
                if sms_recipients:
                    st.success(f"📱 Found {len(sms_recipients)} phone numbers (using {default_carrier})")
            
            # Then check uploaded file
            if uploaded_sms:
                uploaded_recipients = parse_sms_recipients_file(uploaded_sms)
                # Use default carrier for entries without valid carrier
                for phone, carrier in uploaded_recipients:
                    if carrier not in SMS_GATEWAYS:
                        carrier = default_carrier
                    sms_recipients.append((phone, carrier))
                st.success(f"📁 Loaded {len(uploaded_recipients)} recipients from file")
            
            # Then add manual entries
            for entry in st.session_state.sms_entries:
                if entry.get("phone"):
                    sms_recipients.append((entry["phone"], entry.get("carrier", default_carrier)))
            
            # Remove duplicates based on phone number
            seen = set()
            unique_recipients = []
            for phone, carrier in sms_recipients:
                clean = ''.join(filter(str.isdigit, phone))[-10:]
                if clean and clean not in seen:
                    seen.add(clean)
                    unique_recipients.append((phone, carrier))
            sms_recipients = unique_recipients
            
            st.caption(f"📱 **{len(sms_recipients)} unique recipient(s)**")
            
            # Message with Templates
            st.markdown("---")
            st.markdown("### 📝 Message Templates")
            
            # Custom short link input
            col1, col2 = st.columns([2, 1])
            with col1:
                custom_link = st.text_input(
                    "🔗 Your Short Link (optional)",
                    placeholder="https://bit.ly/yourlink",
                    key="sms_custom_link",
                    help="Enter your link - it will replace {link} in templates"
                )
            with col2:
                st.caption("Use `{link}` in your message to insert this URL")
            
            sms_templates = {
                "-- Select Template --": "",
                "🔐 Verification Code": "Your verification code is {random_digit:6}. Valid for 10 minutes. Do not share this code.",
                "🔐 OTP Code": "Your OTP is {random_digit:4}. Use this to complete your login. Expires in 5 mins.",
                "📦 Order Shipped": "Your order has been shipped! Track: {link}",
                "📦 Delivery Update": "Your package is out for delivery! Track here: {link}",
                "💳 Transaction Alert": "Alert: Transaction of ${random_digit:3}.{random_digit:2} on your account. Review: {link}",
                "🔔 Reminder": "Reminder: Your appointment is tomorrow. Details: {link}",
                "🎁 Promo Code": "Special offer! {random_upper:6} for 20% off! Shop: {link}",
                "🔑 Password Reset": "Reset your password here: {link} Code: {random_digit:6}",
                "📱 2FA Code": "Your 2FA code is {random_digit:6}. Expires in 60 sec.",
                "✅ Account Verified": "Account verified! Get started: {link}",
                "⚠️ Security Alert": "New login detected at {time}. Secure your account: {link}",
                "📧 Email Verification": "Verify your email: {link} Code: {random_digit:6}",
                "🎉 Welcome": "Welcome! Get started now: {link}",
                "📅 Appointment": "Appointment confirmed for {date}. Details: {link}",
                "🔗 Custom Link Only": "Check this out: {link}",
                "💰 Payment Link": "Complete your payment: {link} Amount: ${random_digit:2}.99",
                "📲 Download App": "Download our app: {link}",
                "🎫 Ticket/QR": "Your ticket: {link} ID: {random_upper:8}",
                "📢 Announcement": "Important update! Read more: {link}",
                "🏆 Reward Code": "Congrats! Your reward code: {random_upper:8}. Redeem: {link}",
                "📊 Survey": "Take our quick survey: {link} Thanks for your feedback!",
                "🔄 Renewal": "Subscription renewal: {date}. Manage: {link}",
                "📤 File Shared": "A file was shared with you: {link}",
                "🎂 Birthday": "Happy Birthday! Here's a gift: {link}",
                "📞 Call Request": "Please call us regarding your account. Details: {link}",
                "🚚 Pickup Ready": "Your order is ready for pickup! Details: {link}",
                "💼 Job Update": "Application update! Check status: {link}",
                "🏠 Property Alert": "New listing matches your search: {link}",
                "✈️ Travel Update": "Your flight status has changed. Details: {link}"
            }
            
            selected_template = st.selectbox(
                "Quick Templates (auto-fills message)",
                options=list(sms_templates.keys()),
                key="sms_template_select"
            )
            
            # Initialize session state for SMS message if not exists
            if 'sms_message_text' not in st.session_state:
                st.session_state.sms_message_text = ""
            
            # Update message when template is selected
            if selected_template != "-- Select Template --":
                template_message = sms_templates[selected_template]
                if custom_link:
                    template_message = template_message.replace("{link}", custom_link)
                # Only update if different template selected
                if st.session_state.get('last_sms_template') != selected_template:
                    st.session_state.sms_message_text = template_message
                    st.session_state.last_sms_template = selected_template
                    st.session_state.sms_original_template = sms_templates[selected_template]
            
            # Auto-replace {link} when user enters a link (even after template selection)
            if custom_link and '{link}' in st.session_state.sms_message_text:
                st.session_state.sms_message_text = st.session_state.sms_message_text.replace("{link}", custom_link)
            
            # If link changed and we have original template, re-apply with new link
            if custom_link and st.session_state.get('last_sms_link') != custom_link and st.session_state.get('sms_original_template'):
                template_with_link = st.session_state.sms_original_template.replace("{link}", custom_link)
                st.session_state.sms_message_text = template_with_link
                st.session_state.last_sms_link = custom_link
            
            sms_message = st.text_area(
                "Message (160 chars max)",
                value=st.session_state.sms_message_text,
                max_chars=160,
                height=100,
                placeholder="Type your SMS message or select a template above..."
            )
            
            # Sync widget value back to session state for user edits
            st.session_state.sms_message_text = sms_message
            
            st.caption(f"Characters: {len(sms_message)}/160")
            
            # Show link warning if {link} is in message but no link provided
            if "{link}" in sms_message and not custom_link:
                st.warning("⚠️ Your message contains `{link}` but no short link is provided above!")
            
            # Advanced Options for SMS
            with st.expander("⚙️ Advanced SMS Options", expanded=False):
                st.markdown("### ⏱️ Send Delay (Anti-Rate Limit)")
                col1, col2 = st.columns(2)
                with col1:
                    sms_delay_seconds = st.number_input(
                        "Delay (seconds)",
                        min_value=0.0,
                        max_value=60.0,
                        value=0.0,
                        step=0.5,
                        key="sms_delay_seconds",
                        help="Pause between sends to avoid rate limits"
                    )
                with col2:
                    sms_delay_every_n = st.number_input(
                        "Delay every N messages",
                        min_value=0,
                        max_value=1000,
                        value=0,
                        key="sms_delay_every_n",
                        help="Apply delay every N SMS (0 = after each)"
                    )
                
                st.markdown("### 🔄 SMTP Rotation")
                sms_rotate_smtp = st.checkbox(
                    "Enable SMTP Rotation",
                    key="sms_rotate_smtp",
                    value=False,
                    help="Rotate between multiple SMTP servers"
                )
                if sms_rotate_smtp:
                    col1, col2 = st.columns(2)
                    with col1:
                        sms_rotate_after_n = st.number_input(
                            "Rotate after N messages",
                            min_value=1,
                            max_value=10000,
                            value=50,
                            key="sms_rotate_after_n"
                        )
                    with col2:
                        all_smtp_names = list(load_smtp_configs().keys())
                        sms_selected_smtps = st.multiselect(
                            "SMTP servers to rotate",
                            options=all_smtp_names,
                            default=[all_smtp_names[0]] if all_smtp_names else [],
                            key="sms_rotation_smtps"
                        )
                else:
                    sms_rotate_after_n = 0
                    sms_selected_smtps = []
                
                st.markdown("### 🎲 Pattern Variables")
                sms_enable_patterns = st.checkbox(
                    "Enable Pattern Replacement",
                    key="sms_enable_patterns",
                    value=False,
                    help="Replace variables in your SMS message"
                )
                if sms_enable_patterns:
                    st.info("""
**Available Patterns:**
- `{random}` - 8 char random alphanumeric
- `{random:N}` - N char random (e.g., `{random:6}`)
- `{random_digit:N}` - N random digits (great for codes!)
- `{date}` - Current date
- `{time}` - Current time
- `{uuid}` - Unique ID
                    """)
            
            # Send
            if st.button("📤 Send SMS", key="send_sms_btn"):
                if not sender_email or not sender_password:
                    st.error("Please enter sender credentials.")
                elif not sms_recipients:
                    st.error("Please add at least one recipient.")
                elif not sms_message:
                    st.error("Please enter a message.")
                else:
                    # Progress bar - uses Jelly style for Neon Jelly theme
                    progress_bar = JellyProgressBar(label="Sending SMS")
                    status_text = st.empty()
                    
                    def update_progress(pct):
                        progress_bar.progress(pct)
                        status_text.text(f"Sending... {int(pct * 100)}%")
                    
                    # Apply patterns if enabled
                    final_sms_message = apply_patterns(sms_message) if sms_enable_patterns else sms_message
                    
                    # Add delay between sends if configured
                    total_sms = len(sms_recipients)
                    results = []
                    
                    # Use standard send with pattern application
                    results = send_sms_via_gateway(
                        smtp_server=config['server'],
                        smtp_port=config['port'],
                        sender_email=sender_email,
                        sender_password=sender_password,
                        phone_entries=sms_recipients,
                        message=final_sms_message,
                        use_tls=config.get('use_tls', True),
                        use_ssl=config.get('use_ssl', False),
                        progress_callback=update_progress
                    )
                    
                    progress_bar.progress(1.0)
                    status_text.text("Complete!")
                    
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
    
    # ============== AZURE SMS TAB ==============
    with tabs[2]:
        st.subheader("☁️ Azure Communication Services SMS")
        
        if not AZURE_SMS_AVAILABLE:
            st.error("""
            ⚠️ **Azure Communication Services not installed**
            
            To use Azure SMS, install the required package:
            ```
            pip install azure-communication-sms
            ```
            """)
        else:
            st.success("✅ Azure Communication Services SDK is available")
        
        st.markdown("""
        Send SMS using Azure Communication Services phone numbers.
        
        **Requirements:**
        - Azure account with Communication Services resource
        - Phone number purchased from Azure
        - Connection string from Azure Portal
        """)
        
        # Azure SMS Configuration
        st.markdown("### 🔧 Azure Configuration")
        
        # Load saved Azure config
        azure_config = load_json_file(AZURE_SMS_CONFIG_FILE, {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            azure_connection_string = st.text_input(
                "Azure Connection String",
                value=azure_config.get("connection_string", ""),
                type="password",
                help="Get this from Azure Portal > Communication Services > Keys"
            )
        
        with col2:
            azure_from_number = st.text_input(
                "Your Azure Phone Number",
                value=azure_config.get("from_number", ""),
                placeholder="+15551234567",
                help="The phone number you purchased from Azure"
            )
        
        # Save config button
        if st.button("💾 Save Azure Configuration", key="save_azure_config"):
            new_config = {
                "connection_string": azure_connection_string,
                "from_number": azure_from_number
            }
            save_json_file(AZURE_SMS_CONFIG_FILE, new_config)
            st.success("✅ Azure configuration saved!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📱 Send Azure SMS")
        
        # Recipients
        azure_recipients = st.text_area(
            "Recipients (one per line or comma-separated)",
            height=100,
            placeholder="+15559876543\n+15551112222",
            help="Enter phone numbers with country code (e.g., +1 for US)"
        )
        
        # Message
        azure_message = st.text_area(
            "Message",
            height=150,
            max_chars=1600,
            placeholder="Enter your SMS message here...",
            key="azure_sms_message"
        )
        
        # Character count
        if azure_message:
            char_count = len(azure_message)
            segments = (char_count // 160) + 1
            st.caption(f"📊 {char_count}/1600 characters | {segments} SMS segment(s)")
        
        # Enable delivery reports
        enable_delivery_report = st.checkbox("Enable Delivery Reports", value=True)
        
        # Send button
        if st.button("🚀 Send Azure SMS"):
            if not AZURE_SMS_AVAILABLE:
                st.error("Azure Communication Services SDK not installed!")
            elif not azure_connection_string:
                st.error("Please enter your Azure connection string")
            elif not azure_from_number:
                st.error("Please enter your Azure phone number")
            elif not azure_recipients.strip():
                st.error("Please enter at least one recipient")
            elif not azure_message.strip():
                st.error("Please enter a message")
            else:
                # Parse recipients
                recipients = []
                for line in azure_recipients.replace(',', '\n').split('\n'):
                    num = line.strip()
                    if num:
                        recipients.append(num)
                
                if not recipients:
                    st.error("No valid recipients found")
                else:
                    try:
                        with st.spinner(f"Sending to {len(recipients)} recipient(s)..."):
                            from azure.communication.sms import SmsClient
                            
                            sms_client = SmsClient.from_connection_string(azure_connection_string)
                            
                            # Format phone numbers
                            formatted_recipients = []
                            for num in recipients:
                                clean = ''.join(c for c in num if c.isdigit() or c == '+')
                                if not clean.startswith('+'):
                                    if len(clean) == 10:
                                        clean = '+1' + clean
                                    elif len(clean) == 11 and clean.startswith('1'):
                                        clean = '+' + clean
                                formatted_recipients.append(clean)
                            
                            # Format from number
                            from_clean = ''.join(c for c in azure_from_number if c.isdigit() or c == '+')
                            if not from_clean.startswith('+'):
                                if len(from_clean) == 10:
                                    from_clean = '+1' + from_clean
                                elif len(from_clean) == 11 and from_clean.startswith('1'):
                                    from_clean = '+' + from_clean
                            
                            # Send SMS
                            responses = sms_client.send(
                                from_=from_clean,
                                to=formatted_recipients,
                                message=azure_message,
                                enable_delivery_report=enable_delivery_report
                            )
                            
                            # Show results
                            success_count = 0
                            for response in responses:
                                if response.successful:
                                    success_count += 1
                                    st.success(f"✅ Sent to {response.to} - ID: {response.message_id[:8]}...")
                                else:
                                    st.error(f"❌ Failed to {response.to}: {response.error_message if hasattr(response, 'error_message') else 'Unknown error'}")
                            
                            st.info(f"📊 Sent {success_count}/{len(formatted_recipients)} messages successfully")
                            
                            # Save to history
                            save_sent_message({
                                "type": "azure_sms",
                                "to": formatted_recipients,
                                "message": azure_message,
                                "from": from_clean,
                                "success_count": success_count,
                                "total_count": len(formatted_recipients),
                                "timestamp": datetime.now().isoformat()
                            })
                            
                    except Exception as e:
                        st.error(f"❌ Azure SMS Error: {str(e)}")
        
        # Azure SMS Help
        with st.expander("ℹ️ Azure SMS Setup Guide"):
            st.markdown("""
            ### Setting up Azure Communication Services SMS
            
            1. **Create Azure Account**: Go to [Azure Portal](https://portal.azure.com)
            2. **Create Communication Services Resource**:
               - Search for "Communication Services"
               - Click "Create"
               - Fill in resource details and create
            3. **Get Connection String**:
               - Go to your Communication Services resource
               - Click "Keys" in the left menu
               - Copy the "Connection string"
            4. **Get a Phone Number**:
               - In Communication Services, click "Phone Numbers"
               - Click "Get a number"
               - Choose your country and number type
               - Complete the purchase
            5. **Start Sending**: Enter your connection string and phone number above!
            
            **Pricing**: Azure SMS is pay-as-you-go. See [Azure pricing](https://azure.microsoft.com/pricing/details/communication-services/)
            """)
    
    # ============== SCHEDULED TAB ==============
    with tabs[3]:
        st.subheader("⏰ Scheduled Messages")
        
        st.markdown("""
        Schedule emails and SMS to be sent automatically at a specific time. 
        **Note:** The app must be running for scheduled messages to be sent.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 Schedule New Message")
            
            schedule_type = st.radio("Message Type", ["Email", "SMS"], horizontal=True, key="schedule_type")
            
            # SMTP Selection
            smtp_configs = load_smtp_configs()
            smtp_names = list(smtp_configs.keys())
            schedule_smtp = st.selectbox("SMTP Configuration", smtp_names, key="schedule_smtp")
            
            if schedule_type == "Email":
                # Email scheduling
                schedule_recipients = st.text_area(
                    "Recipients (one per line or comma-separated)",
                    placeholder="email1@example.com\nemail2@example.com",
                    key="schedule_recipients"
                )
                schedule_subject = st.text_input("Subject", key="schedule_subject")
                schedule_message = st.text_area("Message", key="schedule_message", height=150)
                
            else:
                # SMS scheduling
                schedule_phones = st.text_area(
                    "Phone Numbers (one per line, format: phone,carrier)",
                    placeholder="5551234567,AT&T\n5559876543,T-Mobile",
                    key="schedule_phones"
                )
                schedule_subject = st.text_input("Subject (optional)", key="schedule_sms_subject")
                schedule_message = st.text_area("SMS Message", key="schedule_sms_message", height=100)
            
            # Date and time selection
            st.markdown("#### ⏱️ Schedule Time")
            col_date, col_time = st.columns(2)
            with col_date:
                schedule_date = st.date_input("Date", key="schedule_date")
            with col_time:
                schedule_time = st.time_input("Time", key="schedule_time")
            
            if st.button("📅 Schedule Message", key="btn_schedule"):
                try:
                    scheduled_datetime = datetime.combine(schedule_date, schedule_time)
                    
                    if scheduled_datetime <= datetime.now():
                        st.error("Please select a future date and time")
                    else:
                        if schedule_type == "Email":
                            # Parse email recipients
                            recipients = []
                            for line in schedule_recipients.split('\n'):
                                for email in line.split(','):
                                    email = email.strip()
                                    if email and '@' in email:
                                        recipients.append(email)
                            
                            if recipients:
                                task = {
                                    "type": "email",
                                    "smtp_config": schedule_smtp,
                                    "recipients": recipients,
                                    "subject": schedule_subject,
                                    "message": schedule_message,
                                    "scheduled_time": scheduled_datetime.isoformat()
                                }
                                task_id = add_scheduled_task(task)
                                st.success(f"✅ Scheduled email for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
                                st.info(f"Task ID: {task_id}")
                                st.rerun()
                            else:
                                st.error("Please enter at least one recipient")
                        else:
                            # Parse phone entries
                            phone_entries = []
                            for line in schedule_phones.split('\n'):
                                line = line.strip()
                                if ',' in line:
                                    parts = line.split(',')
                                    phone = parts[0].strip()
                                    carrier = parts[1].strip() if len(parts) > 1 else "AT&T"
                                    if phone:
                                        phone_entries.append((phone, carrier))
                            
                            if phone_entries:
                                task = {
                                    "type": "sms",
                                    "smtp_config": schedule_smtp,
                                    "phone_entries": phone_entries,
                                    "subject": schedule_subject,
                                    "message": schedule_message,
                                    "scheduled_time": scheduled_datetime.isoformat()
                                }
                                task_id = add_scheduled_task(task)
                                st.success(f"✅ Scheduled SMS for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
                                st.info(f"Task ID: {task_id}")
                                st.rerun()
                            else:
                                st.error("Please enter at least one phone number")
                except Exception as e:
                    st.error(f"Error scheduling: {str(e)}")
        
        with col2:
            st.markdown("### 📋 Scheduled Tasks")
            
            scheduled_tasks = load_scheduled_tasks()
            
            if scheduled_tasks:
                # Sort by scheduled time
                scheduled_tasks.sort(key=lambda x: x.get("scheduled_time", ""), reverse=True)
                
                for task in scheduled_tasks:
                    task_id = task.get("id", "?")
                    task_type = task.get("type", "unknown").upper()
                    status = task.get("status", "unknown")
                    scheduled_time = task.get("scheduled_time", "Unknown")
                    
                    # Status icons
                    status_icons = {
                        "pending": "⏳",
                        "running": "🔄",
                        "completed": "✅",
                        "failed": "❌"
                    }
                    status_icon = status_icons.get(status, "❓")
                    
                    # Format scheduled time
                    try:
                        dt = datetime.fromisoformat(scheduled_time)
                        time_str = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        time_str = scheduled_time
                    
                    with st.expander(f"{status_icon} {task_type} - {time_str} ({task_id})"):
                        st.markdown(f"**Status:** {status}")
                        st.markdown(f"**Type:** {task_type}")
                        st.markdown(f"**SMTP:** {task.get('smtp_config', 'N/A')}")
                        st.markdown(f"**Scheduled:** {time_str}")
                        
                        if task_type == "EMAIL":
                            recipients = task.get("recipients", [])
                            st.markdown(f"**Recipients:** {len(recipients)}")
                            st.markdown(f"**Subject:** {task.get('subject', 'N/A')}")
                        else:
                            phones = task.get("phone_entries", [])
                            st.markdown(f"**Phone Numbers:** {len(phones)}")
                        
                        if task.get("result"):
                            st.markdown(f"**Result:** {task.get('result')}")
                        
                        if status == "pending":
                            if st.button(f"🗑️ Cancel", key=f"cancel_{task_id}"):
                                delete_scheduled_task(task_id)
                                st.success("Task cancelled")
                                st.rerun()
            else:
                st.info("No scheduled tasks. Create one using the form on the left.")
            
            st.markdown("---")
            if st.button("🔄 Refresh Tasks"):
                st.rerun()
    
    # ============== SMTP SETTINGS TAB ==============
    with tabs[4]:
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
            
            if st.button("💾 Save Configuration"):
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
    with tabs[5]:
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
            
            if st.button("💾 Save Recipient List"):
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
    with tabs[6]:
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
    with tabs[7]:
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
    
    # ============== SETTINGS TAB ==============
    with tabs[8]:
        st.subheader("🔧 App Settings")
        
        settings = load_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎨 Appearance")
            
            current_theme = settings.get("theme", "Dragon Dark")
            st.info(f"Current theme: **{current_theme}**")
            
            # Theme preview info
            theme_info = THEMES.get(current_theme, {"icon": "🐉", "type": "dark"})
            st.caption(f"Type: {theme_info['type'].title()} theme")
            st.caption("Use the dropdown in the sidebar to change themes.")
            
            # Show all available themes
            with st.expander("📋 Available Themes"):
                for theme_name, theme_data in THEMES.items():
                    theme_type = "🌙 Dark" if theme_data["type"] == "dark" else "☀️ Light"
                    st.markdown(f"- {theme_data['icon']} **{theme_name}** ({theme_type})")
            
            st.markdown("---")
            st.markdown("### 🔐 Login Protection")
            
            login_enabled = settings.get("login_enabled", False)
            multi_user_enabled = settings.get("multi_user_enabled", False)
            
            # Choose protection mode
            protection_mode = st.radio(
                "Protection Mode",
                ["Disabled", "Single Password", "Multi-User"],
                index=2 if multi_user_enabled else (1 if login_enabled else 0),
                help="Single Password: One password for all users. Multi-User: Different usernames and passwords.",
                horizontal=True,
                key="protection_mode"
            )
            
            if protection_mode == "Disabled":
                if login_enabled or multi_user_enabled:
                    settings["login_enabled"] = False
                    settings["multi_user_enabled"] = False
                    save_settings(settings)
                    st.success("Login protection disabled")
                    st.rerun()
                st.info("⚠️ Anyone can access the app without a password")
                
            elif protection_mode == "Single Password":
                if multi_user_enabled:
                    settings["multi_user_enabled"] = False
                    settings["login_enabled"] = True
                    save_settings(settings)
                    st.rerun()
                
                st.markdown("#### Set Password")
                
                if settings.get("password_hash"):
                    st.success("✅ Password is currently set")
                    
                    # Option to change password
                    with st.expander("🔄 Change Password"):
                        current_pass = st.text_input("Current Password", type="password", key="current_pass")
                        new_pass = st.text_input("New Password", type="password", key="new_pass")
                        confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm_pass")
                        
                        if st.button("Update Password", key="btn_update_pass"):
                            if verify_password(current_pass, settings.get("password_hash", "")):
                                if new_pass == confirm_pass and len(new_pass) >= 4:
                                    settings["password_hash"] = hash_password(new_pass)
                                    settings["login_enabled"] = True
                                    save_settings(settings)
                                    st.success("✅ Password updated!")
                                    st.rerun()
                                elif new_pass != confirm_pass:
                                    st.error("Passwords don't match")
                                else:
                                    st.error("Password must be at least 4 characters")
                            else:
                                st.error("Current password is incorrect")
                else:
                    # Set new password
                    new_pass = st.text_input("New Password", type="password", key="settings_new_pass")
                    confirm_pass = st.text_input("Confirm Password", type="password", key="settings_confirm_pass")
                    
                    if st.button("Set Password", key="btn_set_pass"):
                        if new_pass == confirm_pass and len(new_pass) >= 4:
                            settings["password_hash"] = hash_password(new_pass)
                            settings["login_enabled"] = True
                            save_settings(settings)
                            st.success("✅ Password set! Login protection enabled.")
                            st.rerun()
                        elif new_pass != confirm_pass:
                            st.error("Passwords don't match")
                        else:
                            st.error("Password must be at least 4 characters")
                            
            elif protection_mode == "Multi-User":
                if not multi_user_enabled:
                    settings["multi_user_enabled"] = True
                    settings["login_enabled"] = True
                    save_settings(settings)
                    # Initialize default admin user if not exists
                    users = load_users()
                    if "admin" not in users:
                        users["admin"] = {
                            "password_hash": hash_password("WelcomePassword1@"),
                            "role": "admin",
                            "created": datetime.now().isoformat(),
                            "last_login": None
                        }
                        save_users(users)
                    st.rerun()
                
                st.markdown("#### 👥 User Management")
                st.warning("⚠️ **First time?** Login with admin account, then change the password immediately!")
                
                # Only admins can manage users
                current_role = st.session_state.get("user_role", "admin")
                if current_role == "admin":
                    users = load_users()
                    
                    # Display existing users
                    st.markdown("**Current Users:**")
                    for username, user_data in users.items():
                        role_icon = "👑" if user_data.get("role") == "admin" else "👤"
                        last_login = user_data.get("last_login", "Never")
                        if last_login and last_login != "Never":
                            try:
                                last_login = datetime.fromisoformat(last_login).strftime("%Y-%m-%d %H:%M")
                            except:
                                pass
                        
                        with st.expander(f"{role_icon} {username} ({user_data.get('role', 'user')})"):
                            st.caption(f"Last login: {last_login}")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                # Change password
                                new_pw = st.text_input(f"New password for {username}", type="password", key=f"pw_{username}")
                                if st.button("Update Password", key=f"btn_pw_{username}"):
                                    if new_pw:
                                        success, msg = change_user_password(username, new_pw)
                                        if success:
                                            st.success(msg)
                                        else:
                                            st.error(msg)
                                    else:
                                        st.error("Enter a password")
                            
                            with col_b:
                                # Delete user
                                if username != "admin":
                                    if st.button(f"🗑️ Delete {username}", key=f"btn_del_{username}"):
                                        current_user = st.session_state.get("current_user", "admin")
                                        success, msg = delete_user(username, current_user)
                                        if success:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)
                    
                    # Add new user
                    st.markdown("---")
                    st.markdown("**➕ Add New User:**")
                    col_u1, col_u2, col_u3 = st.columns(3)
                    with col_u1:
                        new_username = st.text_input("Username", key="new_username")
                    with col_u2:
                        new_user_pass = st.text_input("Password", type="password", key="new_user_pass")
                    with col_u3:
                        new_user_role = st.selectbox("Role", ["user", "admin"], key="new_user_role")
                    
                    if st.button("➕ Create User", key="btn_create_user"):
                        if new_username and new_user_pass:
                            success, msg = create_user(new_username, new_user_pass, new_user_role)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("Enter username and password")
                else:
                    st.warning("Only admins can manage users")
        
        with col2:
            st.markdown("### 📊 Data Management")
            
            st.markdown("#### Export All Data")
            if st.button("📥 Export All Data", key="btn_export_all"):
                all_data = {
                    "smtp_configs": load_json_file(SMTP_CONFIG_FILE, {}),
                    "recipients": load_recipient_lists(),
                    "sent_messages": load_sent_messages(),
                    "tracking": load_tracking_data(),
                    "scheduled_tasks": load_scheduled_tasks(),
                    "settings": load_settings()
                }
                st.download_button(
                    "💾 Download Backup",
                    data=json.dumps(all_data, indent=2, default=str),
                    file_name=f"dragon_mailer_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            st.markdown("---")
            st.markdown("#### Clear Data")
            
            with st.expander("⚠️ Danger Zone"):
                st.warning("These actions cannot be undone!")
                
                if st.button("🗑️ Clear All Scheduled Tasks", key="btn_clear_scheduled"):
                    save_scheduled_tasks([])
                    st.success("All scheduled tasks cleared")
                    st.rerun()
                
                if st.button("🗑️ Clear Message History", key="btn_clear_history_settings"):
                    save_json_file(SENT_MESSAGES_FILE, [])
                    st.success("Message history cleared")
                    st.rerun()
                
                if st.button("🗑️ Clear Tracking Data", key="btn_clear_tracking"):
                    save_json_file(TRACKING_FILE, {})
                    st.success("Tracking data cleared")
                    st.rerun()
                
                st.markdown("---")
                
                if st.button("🔥 Reset All Settings", key="btn_reset_settings"):
                    save_settings(DEFAULT_SETTINGS.copy())
                    st.session_state.current_theme = DEFAULT_SETTINGS["theme"]
                    st.success("Settings reset to defaults")
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ App Information")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Version", "2.0")
        with col_b:
            history = load_sent_messages()
            st.metric("Total Messages", len(history))
        with col_c:
            scheduled = load_scheduled_tasks()
            pending = len([t for t in scheduled if t.get("status") == "pending"])
            st.metric("Pending Tasks", pending)
    
    # ============== HELP TAB ==============
    with tabs[9]:
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

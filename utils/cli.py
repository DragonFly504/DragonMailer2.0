"""
Command-Line Email & SMS Messenger
Send emails and SMS via SMTP from the terminal
"""

import smtplib
import argparse
import getpass
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Config file path - use the main app's config folder
CONFIG_DIR = Path(__file__).parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "smtp_configs.json"

# SMS Gateway domains for major carriers
SMS_GATEWAYS = {
    "att": "txt.att.net",
    "tmobile": "tmomail.net",
    "verizon": "vtext.com",
    "sprint": "messaging.sprintpcs.com",
    "uscellular": "email.uscc.net",
    "metropcs": "mymetropcs.com",
    "boost": "sms.myboostmobile.com",
    "cricket": "sms.cricketwireless.net",
    "virgin": "vmobl.com",
    "googlefi": "msg.fi.google.com",
    "mint": "tmomail.net",
}

# Default SMTP presets
SMTP_PRESETS = {
    "gmail": ("smtp.gmail.com", 587, True, False),
    "outlook": ("smtp.office365.com", 587, True, False),
    "yahoo": ("smtp.mail.yahoo.com", 587, True, False),
    "icloud": ("smtp.mail.me.com", 587, True, False),
    "zoho": ("smtp.zoho.com", 587, True, False),
    "sendgrid": ("smtp.sendgrid.net", 587, True, False),
}


def load_config():
    """Load saved SMTP configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(name, server, port, use_tls, use_ssl):
    """Save SMTP configuration."""
    configs = load_config()
    configs[name] = {
        "server": server,
        "port": port,
        "use_tls": use_tls,
        "use_ssl": use_ssl
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=2)
    print(f"✅ Saved configuration '{name}'")


def send_email(smtp_server, smtp_port, sender_email, sender_password, 
               recipients, subject, message, use_tls=True, use_ssl=False):
    """Send email to multiple recipients."""
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        server.login(sender_email, sender_password)
        
        success_count = 0
        for recipient in recipients:
            recipient = recipient.strip()
            if not recipient:
                continue
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                
                server.sendmail(sender_email, recipient, msg.as_string())
                print(f"  ✅ Sent to {recipient}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Failed to send to {recipient}: {e}")
        
        server.quit()
        print(f"\n📧 Sent {success_count}/{len(recipients)} emails successfully")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your email and app password.")
    except Exception as e:
        print(f"❌ Error: {e}")


def send_sms(smtp_server, smtp_port, sender_email, sender_password,
             phone_numbers, carriers, message, use_tls=True, use_ssl=False):
    """Send SMS via email gateway."""
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        server.login(sender_email, sender_password)
        
        success_count = 0
        for i, phone in enumerate(phone_numbers):
            phone = phone.strip()
            if not phone:
                continue
            
            carrier = carriers[i] if i < len(carriers) else carriers[0]
            
            # Clean phone number
            clean_number = ''.join(filter(str.isdigit, phone))[-10:]
            
            if len(clean_number) < 10:
                print(f"  ❌ Invalid phone number: {phone}")
                continue
            
            gateway = SMS_GATEWAYS.get(carrier.lower())
            if not gateway:
                print(f"  ❌ Unknown carrier: {carrier}")
                continue
            
            sms_email = f"{clean_number}@{gateway}"
            
            try:
                msg = MIMEText(message, 'plain')
                msg['From'] = sender_email
                msg['To'] = sms_email
                msg['Subject'] = ""
                
                server.sendmail(sender_email, sms_email, msg.as_string())
                print(f"  ✅ Sent to {phone} via {sms_email}")
                success_count += 1
            except Exception as e:
                print(f"  ❌ Failed to send to {phone}: {e}")
        
        server.quit()
        print(f"\n📱 Sent {success_count}/{len(phone_numbers)} SMS successfully")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your email and app password.")
    except Exception as e:
        print(f"❌ Error: {e}")


def interactive_mode():
    """Run in interactive mode."""
    print("\n" + "="*50)
    print("📧 Email & SMS Messenger - Interactive Mode")
    print("="*50)
    
    # SMTP Setup
    print("\n📌 SMTP Configuration")
    print("Available presets: " + ", ".join(SMTP_PRESETS.keys()))
    
    preset = input("Enter preset name or 'custom': ").strip().lower()
    
    if preset in SMTP_PRESETS:
        smtp_server, smtp_port, use_tls, use_ssl = SMTP_PRESETS[preset]
        print(f"Using {preset}: {smtp_server}:{smtp_port}")
    else:
        smtp_server = input("SMTP Server: ").strip()
        smtp_port = int(input("SMTP Port [587]: ").strip() or "587")
        use_tls = input("Use TLS? (y/n) [y]: ").strip().lower() != 'n'
        use_ssl = input("Use SSL? (y/n) [n]: ").strip().lower() == 'y'
    
    # Credentials
    print("\n🔐 Credentials")
    sender_email = input("Your email: ").strip()
    sender_password = getpass.getpass("App password: ")
    
    # Message type
    print("\n📨 What do you want to send?")
    print("1. Email")
    print("2. SMS")
    print("3. Both")
    choice = input("Choose (1/2/3): ").strip()
    
    message = input("\n✉️ Enter your message:\n> ")
    
    if choice in ['1', '3']:
        print("\n📧 Email Recipients (comma-separated)")
        recipients = input("> ").split(',')
        subject = input("Subject: ")
        
        print("\nSending emails...")
        send_email(smtp_server, smtp_port, sender_email, sender_password,
                  recipients, subject, message, use_tls, use_ssl)
    
    if choice in ['2', '3']:
        print("\n📱 SMS Recipients")
        print(f"Available carriers: {', '.join(SMS_GATEWAYS.keys())}")
        phones = input("Phone numbers (comma-separated): ").split(',')
        carrier = input("Carrier (same for all): ").strip()
        carriers = [carrier] * len(phones)
        
        print("\nSending SMS...")
        send_sms(smtp_server, smtp_port, sender_email, sender_password,
                phones, carriers, message, use_tls, use_ssl)


def main():
    parser = argparse.ArgumentParser(
        description="Send emails and SMS via SMTP from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send email
  python cli.py email -p gmail -e you@gmail.com -t user@example.com -s "Hello" -m "Message"
  
  # Send SMS
  python cli.py sms -p gmail -e you@gmail.com -n 5551234567 -c att -m "Hello!"
  
  # Send to multiple recipients
  python cli.py email -p gmail -e you@gmail.com -t user1@example.com,user2@example.com -m "Hi all"
  
  # Interactive mode
  python cli.py interactive
  
  # List carriers
  python cli.py carriers
  
  # List SMTP presets
  python cli.py presets

Carriers: """ + ", ".join(SMS_GATEWAYS.keys())
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Email command
    email_parser = subparsers.add_parser('email', help='Send email')
    email_parser.add_argument('-p', '--preset', help='SMTP preset (gmail, outlook, yahoo, etc.)')
    email_parser.add_argument('--server', help='Custom SMTP server')
    email_parser.add_argument('--port', type=int, default=587, help='SMTP port')
    email_parser.add_argument('--ssl', action='store_true', help='Use SSL instead of TLS')
    email_parser.add_argument('-e', '--email', required=True, help='Your email address')
    email_parser.add_argument('-w', '--password', help='App password (will prompt if not provided)')
    email_parser.add_argument('-t', '--to', required=True, help='Recipients (comma-separated)')
    email_parser.add_argument('-s', '--subject', default='', help='Email subject')
    email_parser.add_argument('-m', '--message', required=True, help='Message to send')
    
    # SMS command
    sms_parser = subparsers.add_parser('sms', help='Send SMS via gateway')
    sms_parser.add_argument('-p', '--preset', help='SMTP preset (gmail, outlook, yahoo, etc.)')
    sms_parser.add_argument('--server', help='Custom SMTP server')
    sms_parser.add_argument('--port', type=int, default=587, help='SMTP port')
    sms_parser.add_argument('--ssl', action='store_true', help='Use SSL instead of TLS')
    sms_parser.add_argument('-e', '--email', required=True, help='Your email address')
    sms_parser.add_argument('-w', '--password', help='App password (will prompt if not provided)')
    sms_parser.add_argument('-n', '--numbers', required=True, help='Phone numbers (comma-separated)')
    sms_parser.add_argument('-c', '--carrier', required=True, help='Carrier(s) (comma-separated)')
    sms_parser.add_argument('-m', '--message', required=True, help='Message to send (max 160 chars)')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Interactive mode')
    
    # List carriers
    subparsers.add_parser('carriers', help='List available carriers')
    
    # List presets
    subparsers.add_parser('presets', help='List SMTP presets')
    
    args = parser.parse_args()
    
    if args.command == 'carriers':
        print("\n📱 Available SMS Carriers:")
        print("-" * 40)
        for name, gateway in SMS_GATEWAYS.items():
            print(f"  {name:12} → {gateway}")
        return
    
    if args.command == 'presets':
        print("\n📧 Available SMTP Presets:")
        print("-" * 50)
        for name, (server, port, tls, ssl) in SMTP_PRESETS.items():
            print(f"  {name:10} → {server}:{port}")
        return
    
    if args.command == 'interactive':
        interactive_mode()
        return
    
    if args.command == 'email':
        # Get SMTP settings
        if args.preset and args.preset.lower() in SMTP_PRESETS:
            smtp_server, smtp_port, use_tls, use_ssl = SMTP_PRESETS[args.preset.lower()]
        elif args.server:
            smtp_server = args.server
            smtp_port = args.port
            use_tls = not args.ssl
            use_ssl = args.ssl
        else:
            print("❌ Please provide --preset or --server")
            return
        
        password = args.password or getpass.getpass("App password: ")
        recipients = [r.strip() for r in args.to.split(',')]
        
        print(f"\n📧 Sending email to {len(recipients)} recipient(s)...")
        send_email(smtp_server, smtp_port, args.email, password,
                  recipients, args.subject, args.message, use_tls, use_ssl)
    
    elif args.command == 'sms':
        # Get SMTP settings
        if args.preset and args.preset.lower() in SMTP_PRESETS:
            smtp_server, smtp_port, use_tls, use_ssl = SMTP_PRESETS[args.preset.lower()]
        elif args.server:
            smtp_server = args.server
            smtp_port = args.port
            use_tls = not args.ssl
            use_ssl = args.ssl
        else:
            print("❌ Please provide --preset or --server")
            return
        
        password = args.password or getpass.getpass("App password: ")
        phones = [p.strip() for p in args.numbers.split(',')]
        carriers = [c.strip() for c in args.carrier.split(',')]
        
        # If only one carrier provided, use it for all
        if len(carriers) == 1:
            carriers = carriers * len(phones)
        
        if len(args.message) > 160:
            print(f"⚠️ Warning: Message is {len(args.message)} chars (max 160 for SMS)")
        
        print(f"\n📱 Sending SMS to {len(phones)} recipient(s)...")
        send_sms(smtp_server, smtp_port, args.email, password,
                phones, carriers, args.message, use_tls, use_ssl)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

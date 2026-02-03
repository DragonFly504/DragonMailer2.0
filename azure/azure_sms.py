"""
Azure Communication Services SMS Sender
Send SMS using Azure phone numbers
"""

import argparse
import getpass

try:
    from azure.communication.sms import SmsClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


def send_azure_sms(connection_string: str, from_number: str, to_numbers: list[str], 
                   message: str, enable_delivery_report: bool = True) -> list[dict]:
    """
    Send SMS using Azure Communication Services.
    
    Args:
        connection_string: Azure ACS connection string
        from_number: Your Azure phone number (e.g., +15551234567)
        to_numbers: List of recipient phone numbers (e.g., ["+15559876543"])
        message: Message to send
        enable_delivery_report: Whether to enable delivery reports
    
    Returns:
        List of send results
    """
    if not AZURE_AVAILABLE:
        raise ImportError("azure-communication-sms not installed. Run: pip install azure-communication-sms")
    
    sms_client = SmsClient.from_connection_string(connection_string)
    
    # Ensure phone numbers start with +
    formatted_numbers = []
    for num in to_numbers:
        num = num.strip()
        if not num:
            continue
        # Remove any non-digit chars except +
        clean = ''.join(c for c in num if c.isdigit() or c == '+')
        if not clean.startswith('+'):
            # Assume US number if no country code
            if len(clean) == 10:
                clean = '+1' + clean
            elif len(clean) == 11 and clean.startswith('1'):
                clean = '+' + clean
        formatted_numbers.append(clean)
    
    # Format from number
    from_clean = ''.join(c for c in from_number if c.isdigit() or c == '+')
    if not from_clean.startswith('+'):
        if len(from_clean) == 10:
            from_clean = '+1' + from_clean
        elif len(from_clean) == 11 and from_clean.startswith('1'):
            from_clean = '+' + from_clean
    
    # Send SMS
    sms_responses = sms_client.send(
        from_=from_clean,
        to=formatted_numbers,
        message=message,
        enable_delivery_report=enable_delivery_report
    )
    
    results = []
    for response in sms_responses:
        results.append({
            'to': response.to,
            'message_id': response.message_id,
            'success': response.successful,
            'error': response.error_message if hasattr(response, 'error_message') else None
        })
    
    return results


def interactive_mode():
    """Run Azure SMS in interactive mode."""
    print("\n" + "="*50)
    print("📱 Azure Communication Services SMS")
    print("="*50)
    
    if not AZURE_AVAILABLE:
        print("❌ azure-communication-sms not installed.")
        print("Run: pip install azure-communication-sms")
        return
    
    print("\n📌 Azure Configuration")
    print("Get your connection string from Azure Portal > Communication Services > Keys")
    
    connection_string = getpass.getpass("Connection String: ")
    from_number = input("Your Azure Phone Number (e.g., +15551234567): ").strip()
    
    print("\n📱 Recipients (comma-separated phone numbers)")
    to_input = input("> ").strip()
    to_numbers = [n.strip() for n in to_input.split(',')]
    
    message = input("\n✉️ Message:\n> ")
    
    print("\nSending SMS via Azure...")
    try:
        results = send_azure_sms(connection_string, from_number, to_numbers, message)
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n📱 Sent {success_count}/{len(results)} messages")
        
        for result in results:
            if result['success']:
                print(f"  ✅ {result['to']}: Message ID {result['message_id']}")
            else:
                print(f"  ❌ {result['to']}: {result['error']}")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Send SMS using Azure Communication Services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Send SMS
  python azure_sms.py send -c "endpoint=...;accesskey=..." -f +15551234567 -t +15559876543 -m "Hello!"
  
  # Send to multiple recipients
  python azure_sms.py send -c "..." -f +15551234567 -t +15551111111,+15552222222 -m "Group message"
  
  # Interactive mode
  python azure_sms.py interactive

Setup:
  1. Create Azure Communication Services resource in Azure Portal
  2. Buy a phone number (Telephony > Phone numbers)
  3. Get connection string (Keys > Connection string)
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send SMS')
    send_parser.add_argument('-c', '--connection', required=True, help='Azure ACS connection string')
    send_parser.add_argument('-f', '--from', dest='from_number', required=True, help='Your Azure phone number')
    send_parser.add_argument('-t', '--to', required=True, help='Recipient phone numbers (comma-separated)')
    send_parser.add_argument('-m', '--message', required=True, help='Message to send')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Interactive mode')
    
    args = parser.parse_args()
    
    if args.command == 'interactive':
        interactive_mode()
        return
    
    if args.command == 'send':
        if not AZURE_AVAILABLE:
            print("❌ azure-communication-sms not installed.")
            print("Run: pip install azure-communication-sms")
            return
        
        to_numbers = [n.strip() for n in args.to.split(',')]
        
        print(f"\n📱 Sending SMS to {len(to_numbers)} recipient(s)...")
        try:
            results = send_azure_sms(
                args.connection,
                args.from_number,
                to_numbers,
                args.message
            )
            
            success_count = sum(1 for r in results if r['success'])
            print(f"\n📱 Sent {success_count}/{len(results)} messages")
            
            for result in results:
                if result['success']:
                    print(f"  ✅ {result['to']}: Message ID {result['message_id']}")
                else:
                    print(f"  ❌ {result['to']}: {result['error']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

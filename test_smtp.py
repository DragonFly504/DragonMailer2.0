#!/usr/bin/env python3
"""
Test SMTP connection to Office 365
Run on VPS: python3 test_smtp.py
"""
import smtplib
import sys

def test_smtp():
    server_address = "smtp.office365.com"
    port = 587
    
    print(f"Testing connection to {server_address}:{port}...")
    
    try:
        server = smtplib.SMTP(server_address, port, timeout=15)
        server.starttls()
        print("✅ SUCCESS: SMTP connection works!")
        print("   Your VPS can send emails via Office 365")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_smtp()
    sys.exit(0 if success else 1)

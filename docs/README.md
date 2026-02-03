# 🐉 Dragon Mailer v2.0

A powerful Python application to send bulk emails and SMS messages. Includes a beautiful **Streamlit web UI** with themes, multi-user support, and scheduling.

## ✨ Features

- ✉️ **Bulk Email Sending** - Send to hundreds of recipients
- 📱 **SMS via Carrier Gateways** - Free SMS through email-to-SMS
- ☁️ **Azure SMS Integration** - Professional SMS via Azure Communication Services
- 👥 **Multi-User System** - Create accounts for different users
- 🔐 **Password Protection** - Secure your app with login
- 🎨 **11 Beautiful Themes** - Dark and light modes
- ⏰ **Scheduled Sending** - Queue messages for later
- 📊 **Message History** - Track all sent messages
- 📈 **Email Tracking** - Track email opens
- 🌐 **Network Access** - Use from any PC on your network

## 🚀 Quick Start (Windows)

### After Cloning:

```bash
# Clone the repository
git clone https://github.com/DragonFly504/DragonMailer2.0.git
cd DragonMailer2.0

# Run setup (creates desktop shortcut + installs packages)
SETUP.bat
```

**That's it!** Double-click the "Dragon Mailer" shortcut on your desktop.

### Manual Start:

```bash
# Start the app
Start_Dragon_Mailer.bat

# Or for network access (other PCs):
Start_Network_Mode.bat
```

## 🔐 Login System

The app supports:
- **Single Password Mode** - One password for everyone
- **Multi-User Mode** - Separate accounts for each user

Each user gets their own isolated workspace. Enable Multi-User mode in Settings after first launch.

## 📁 Files Included

| File | Purpose |
|------|---------|
| `SETUP.bat` | First-time setup (run after clone) |
| `Start_Dragon_Mailer.bat` | Start app (local only) |
| `Start_Network_Mode.bat` | Start app (network access) |
| `Allow_Firewall.bat` | Allow through Windows Firewall |
| `app.py` | Main application |
| `cli.py` | Command-line interface |

## 🎨 Available Themes

- 🐉 Dragon Dark / Light
- 🔒 SecureMail Pro
- 🌙 Midnight Blue
- 🌊 Ocean Breeze
- 🌲 Forest Green
- 🌅 Sunset Orange
- 💜 Purple Haze
- 🌸 Rose Gold
- 💚 Cyber Neon
- ❄️ Arctic Ice

## 💻 Command Line Interface

```bash
# Send email
python cli.py email -p gmail -e you@gmail.com -t recipient@example.com -s "Subject" -m "Message"

# Send SMS
python cli.py sms -p gmail -e you@gmail.com -n 5551234567 -c att -m "Hello!"

# Interactive mode
python cli.py interactive

# List available carriers
python cli.py carriers

# List SMTP presets
python cli.py presets
```

## SMS Carriers Supported

| Carrier | Gateway |
|---------|---------|
| AT&T | txt.att.net |
| T-Mobile | tmomail.net |
| Verizon | vtext.com |
| Sprint | messaging.sprintpcs.com |
| US Cellular | email.uscc.net |
| Metro PCS | mymetropcs.com |
| Boost Mobile | sms.myboostmobile.com |
| Cricket | sms.cricketwireless.net |
| Virgin Mobile | vmobl.com |
| Google Fi | msg.fi.google.com |
| Mint Mobile | tmomail.net |

## SMTP Presets

- **Gmail** - smtp.gmail.com:587
- **Outlook/Hotmail** - smtp.office365.com:587
- **Yahoo** - smtp.mail.yahoo.com:587
- **iCloud** - smtp.mail.me.com:587
- **Zoho** - smtp.zoho.com:587
- **SendGrid** - smtp.sendgrid.net:587
- **Mailgun** - smtp.mailgun.org:587
- **Amazon SES** - email-smtp.us-east-1.amazonaws.com:587

## ⚠️ Important Notes

### Gmail App Password
For Gmail, you must use an **App Password** instead of your regular password:
1. Enable 2-Factor Authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this 16-character password in the app

### Security
- Never commit your credentials to git
- The `smtp_configs.json` file is gitignored
- Use environment variables for production deployments

## License

MIT License

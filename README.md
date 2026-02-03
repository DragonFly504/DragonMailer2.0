# 🐉 Dragon Mailer v2.0

A powerful Python application to send bulk emails and SMS messages with a beautiful **Streamlit web UI**.

## ✨ Features

- ✉️ **Bulk Email Sending** - Send to hundreds of recipients
- 📱 **SMS via Carrier Gateways** - Free SMS through email-to-SMS
- ☁️ **Azure SMS Integration** - Professional SMS via Azure Communication Services
- 👥 **Multi-User System** - Create accounts for different users
- 🔐 **Password Protection** - Secure your app with login
- 🎨 **20+ Beautiful Themes** - Glass effects with rotating backgrounds
- ⏰ **Scheduled Sending** - Queue messages for later
- 📊 **Message History** - Track all sent messages

## 🚀 Quick Start (Windows)

### Option 1: Double-Click Setup
```bash
# Clone the repository
git clone https://github.com/DragonFly504/DragonMailer2.0.git
cd DragonMailer2.0

# Run setup (creates desktop shortcut + installs packages)
SETUP.bat
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python -m streamlit run app.py --server.port 8503
```

### Option 3: Network Mode (Access from other PCs)
```bash
Start_Network_Mode.bat
```

## 🔐 Default Login

- **Username:** `admin`
- **Password:** `WelcomePassword1@`

*Change the password after first login!*

## 📁 Project Structure

```
DragonMailer2.0/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── SETUP.bat          # Windows setup script
├── Start_Dragon_Mailer.bat  # Quick start
├── config/            # User settings & configs
├── docs/              # Documentation
├── azure/             # Azure SMS integration
├── utils/             # Utility scripts
└── Scripts/           # PowerShell helper scripts
```

## 🎨 Glass Theme UI

The login page features:
- Beautiful gradient backgrounds (20 rotating themes)
- Glass morphism effects with blur
- Dragon logo with fire animation
- Responsive design optimized for all screen sizes

## ⚙️ Configuration

Settings are stored in `config/settings.json`:
- SMTP server configuration
- Theme preferences
- Multi-user toggle
- Email tracking options

## 📚 Documentation

See the `docs/` folder for:
- [User Guide](docs/USER_GUIDE.md)
- [Azure SMS Setup](docs/AZURE_SMS_SETUP.md)
- [VPS Deployment](docs/VPS_DEPLOYMENT.md)
- [Troubleshooting](docs/troubleshoot.md)

## 🐳 Docker Support

```bash
docker build -t dragon-mailer .
docker run -p 8503:8503 dragon-mailer
```

## 📜 License

MIT License - Use freely for personal or commercial projects.

---

Made with ❤️ by DragonFly504

#!/bin/bash
# Azure VM Deployment Script for Messenger App
# Run this script on your Azure VM

set -e

echo "🚀 Starting Messenger App deployment on Azure VM..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python..."
sudo apt install -y python3 python3-pip python3-venv git curl

# Create app directory
echo "📁 Creating application directory..."
mkdir -p ~/messaging_app
cd ~/messaging_app

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
streamlit>=1.53.0
azure-communication-sms>=1.1.0
azure-core>=1.38.0
EOF

# Install Python packages
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create Streamlit config directory
mkdir -p .streamlit

# Create Streamlit config
cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#4F46E5"
backgroundColor = "#F9FAFB"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1F2937"
font = "sans serif"
EOF

echo "✅ Base setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Upload your app.py file to ~/messaging_app/"
echo "   2. Run: cd ~/messaging_app && source venv/bin/activate"
echo "   3. Run: streamlit run app.py"
echo ""
echo "🔥 Don't forget to open port 8501 in Azure Network Security Group!"

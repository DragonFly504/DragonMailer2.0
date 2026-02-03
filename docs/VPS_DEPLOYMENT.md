# VPS Deployment Guide

## Quick Start

### 1. Upload to VPS
```bash
scp -r messaging_app/ user@your-vps-ip:~/
```

### 2. SSH into VPS
```bash
ssh user@your-vps-ip
cd messaging_app
```

### 3. Install Python & Dependencies
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip -y

# Install app dependencies
pip3 install -r requirements.txt
```

### 4. Start the Server
```bash
chmod +x start_server.sh
./start_server.sh
```

### 5. Access Your App
Open in browser: `http://YOUR_VPS_IP:8501`

---

## Production Setup (Recommended)

### Using systemd (Auto-restart on reboot)

Create `/etc/systemd/system/messenger.service`:
```ini
[Unit]
Description=Streamlit Messenger App
After=network.target

[Service]
User=your-username
WorkingDirectory=/home/your-username/messaging_app
ExecStart=/usr/bin/python3 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable messenger
sudo systemctl start messenger
```

### Using Nginx (HTTPS & Domain)

Install Nginx:
```bash
sudo apt install nginx -y
```

Create `/etc/nginx/sites-available/messenger`:
```nginx
server {
    listen 80;
    server_name onlinefcu.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/messenger /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Add SSL (Free with Certbot)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d onlinefcu.com
```

---

## Firewall Setup
```bash
# Allow Streamlit port
sudo ufw allow 8501

# Or if using Nginx
sudo ufw allow 80
sudo ufw allow 443
```

---

## Stop Server
```bash
# If using nohup
pkill -f streamlit

# If using systemd
sudo systemctl stop messenger
```

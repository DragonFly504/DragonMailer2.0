# Virtual Machine Installation Guide

## Quick Install (Any Linux VM)

### 1-Command Install:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y python3 python3-pip git
git clone https://github.com/Dragon504/messaging_app.git
cd messaging_app
pip3 install -r requirements.txt
python3 -m streamlit run app.py --server.address 0.0.0.0
```

---

## Step-by-Step Installation

### Step 1: Create a VM

#### Option A: VirtualBox (Free)
1. Download [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
2. Download [Ubuntu Server ISO](https://ubuntu.com/download/server)
3. Create New VM:
   - Name: `messenger-server`
   - Type: Linux, Ubuntu 64-bit
   - RAM: 2048 MB (minimum 1024)
   - Disk: 20 GB
4. Start VM → Select ISO → Install Ubuntu

#### Option B: VMware Workstation
1. Download [VMware Workstation Player](https://www.vmware.com/products/workstation-player.html) (free)
2. Create New VM → Select Ubuntu ISO
3. Follow installation wizard

#### Option C: Hyper-V (Windows Pro/Enterprise)
```powershell
# Enable Hyper-V
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All

# Create VM via Hyper-V Manager or PowerShell:
New-VM -Name "messenger-server" -MemoryStartupBytes 2GB -NewVHDPath "C:\VMs\messenger.vhdx" -NewVHDSizeBytes 20GB
```

#### Option D: WSL2 (Windows - Easiest)
```powershell
# Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# Open Ubuntu terminal and continue with Linux steps
```

---

### Step 2: Configure VM Networking

#### VirtualBox - Port Forwarding:
1. VM Settings → Network → Advanced → Port Forwarding
2. Add rule:
   - Name: `streamlit`
   - Host Port: `8501`
   - Guest Port: `8501`

#### VMware - NAT:
1. VM Settings → Network Adapter → NAT
2. Edit → Virtual Network Editor → NAT Settings → Port Forwarding
3. Add: Host `8501` → Guest `8501`

#### Hyper-V - External Switch:
```powershell
# Create external switch
New-VMSwitch -Name "External" -NetAdapterName "Ethernet" -AllowManagementOS $true

# Connect VM to switch
Connect-VMNetworkAdapter -VMName "messenger-server" -SwitchName "External"
```

---

### Step 3: Install on Linux VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install -y python3 python3-pip python3-venv

# Create app directory
mkdir -p ~/messaging_app
cd ~/messaging_app

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Streamlit and dependencies
pip install streamlit

# Create requirements.txt
cat > requirements.txt << 'EOF'
streamlit>=1.53.0
azure-communication-sms>=1.1.0
azure-core>=1.38.0
EOF

pip install -r requirements.txt
```

---

### Step 4: Upload App Files

#### Option A: SCP from Windows
```powershell
# From Windows PowerShell
scp -r C:\Users\Public\messaging_app\* user@VM_IP:~/messaging_app/
```

#### Option B: Git Clone
```bash
# On VM
cd ~/messaging_app
git clone https://github.com/YOUR_REPO.git .
```

#### Option C: Copy-Paste Files
Create files manually on VM using nano/vim:
```bash
nano app.py
# Paste content, Ctrl+X, Y, Enter
```

---

### Step 5: Run the App

```bash
cd ~/messaging_app
source venv/bin/activate  # If using venv

# Run (foreground)
streamlit run app.py --server.address 0.0.0.0 --server.port 8501

# Or run in background
nohup streamlit run app.py --server.address 0.0.0.0 --server.port 8501 > app.log 2>&1 &
```

---

### Step 6: Access the App

| Setup | Access URL |
|-------|------------|
| VirtualBox (port forward) | http://localhost:8501 |
| VMware NAT | http://localhost:8501 |
| Bridged/External | http://VM_IP:8501 |
| WSL2 | http://localhost:8501 |

Find VM IP:
```bash
ip addr show | grep inet
# or
hostname -I
```

---

## Auto-Start on Boot (Systemd)

```bash
# Create service file
sudo nano /etc/systemd/system/messenger.service
```

Paste:
```ini
[Unit]
Description=Streamlit Messenger App
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/messaging_app
Environment="PATH=/home/YOUR_USERNAME/messaging_app/venv/bin"
ExecStart=/home/YOUR_USERNAME/messaging_app/venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable messenger
sudo systemctl start messenger

# Check status
sudo systemctl status messenger
```

---

## Firewall Configuration

```bash
# Ubuntu UFW
sudo ufw allow 8501/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload
```

---

## Windows VM Installation

### Using Windows Server or Windows 10/11 VM:

```powershell
# Install Python
winget install Python.Python.3.11

# Or download from python.org

# Create folder
mkdir C:\messenger_app
cd C:\messenger_app

# Install dependencies
pip install streamlit azure-communication-sms azure-core

# Copy your app.py file here

# Run
streamlit run app.py --server.address 0.0.0.0
```

### Windows Firewall:
```powershell
New-NetFirewallRule -DisplayName "Streamlit" -Direction Inbound -Port 8501 -Protocol TCP -Action Allow
```

---

## Cloud VM Quick Setup

### Azure VM:
```bash
# Create Ubuntu VM
az vm create \
  --resource-group myResourceGroup \
  --name messenger-vm \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username azureuser \
  --generate-ssh-keys

# Open port
az vm open-port --port 8501 --resource-group myResourceGroup --name messenger-vm

# SSH in and install
ssh azureuser@<public-ip>
```

### AWS EC2:
1. Launch EC2 → Ubuntu 22.04 → t2.micro
2. Security Group: Allow TCP 8501
3. SSH in and install

### Google Cloud:
```bash
gcloud compute instances create messenger-vm \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-micro

gcloud compute firewall-rules create allow-streamlit --allow tcp:8501
```

---

## Troubleshooting

### Can't access from host machine:
1. Check VM IP: `hostname -I`
2. Check app is running: `curl localhost:8501`
3. Check firewall: `sudo ufw status`
4. Check port forwarding settings

### Permission denied:
```bash
chmod +x start_server.sh
sudo chown -R $USER:$USER ~/messaging_app
```

### Module not found:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Port already in use:
```bash
# Find what's using port
sudo lsof -i :8501

# Kill it
sudo kill -9 <PID>
```

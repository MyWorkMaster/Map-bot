# Deployment Guide for Ubuntu

This guide will help you deploy the Anomonus Telegram Bot on an Ubuntu server.

## Prerequisites

- Ubuntu 20.04 or later
- Python 3.8 or later
- Root or sudo access
- Domain/server with public IP (for production)

---

## Step 1: Server Setup

### Update System
```bash
sudo apt update
sudo apt upgrade -y
```

### Install Python and pip
```bash
sudo apt install python3 python3-pip python3-venv -y
```

### Install Git (if needed)
```bash
sudo apt install git -y
```

---

## Step 2: Upload Bot Files

### Option A: Using Git
```bash
cd /opt
sudo git clone <your-repo-url> anomonus-bot
cd anomonus-bot
```

### Option B: Using SCP (from your local machine)
```bash
scp -r /Users/macbookpro/Desktop/ANOMONUS-MAP-BOT user@your-server-ip:/opt/anomonus-bot
```

### Option C: Manual Upload
1. Create directory: `sudo mkdir -p /opt/anomonus-bot`
2. Upload files via SFTP/FTP
3. Extract if needed

---

## Step 3: Create Virtual Environment

```bash
cd /opt/anomonus-bot
python3 -m venv venv
source venv/bin/activate
```

---

## Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 5: Configure Environment

### Create Environment File
```bash
nano .env
```

Add your configuration:
```bash
# Bot Tokens
TEST_BOT_TOKEN=8164339923:AAHw-wqosK75xbNs8_SRexwp3HTE4bRoq4w
REAL_BOT_TOKEN=7837025186:AAH4SKBBwBsf9mc4XZVJ4sN_ksCSCKSrxSw

# Map Website API URL
MAP_API_URL=http://localhost:4000
# Or for production:
# MAP_API_URL=https://your-domain.com

# Flask API Port (optional, defaults to 5000)
API_PORT=5000
```

### Update bot.py to use environment variables (optional)
You can modify bot.py to read from .env file using `python-dotenv`:

```bash
pip install python-dotenv
```

Then add to bot.py:
```python
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('REAL_BOT_TOKEN', REAL_BOT_TOKEN)
MAP_API_URL = os.getenv('MAP_API_URL', 'http://localhost:4000')
```

---

## Step 6: Test Run

### Test the bot manually first
```bash
cd /opt/anomonus-bot
source venv/bin/activate
python bot.py
```

Press `Ctrl+C` to stop. If it works, proceed to next step.

---

## Step 7: Create Systemd Service (Recommended)

### Create service file
```bash
sudo nano /etc/systemd/system/anomonus-bot.service
```

Add the following content:
```ini
[Unit]
Description=Anomonus Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/anomonus-bot
Environment="PATH=/opt/anomonus-bot/venv/bin"
ExecStart=/opt/anomonus-bot/venv/bin/python /opt/anomonus-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `your-username` with your actual Ubuntu username.

### Enable and start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable anomonus-bot
sudo systemctl start anomonus-bot
```

### Check status
```bash
sudo systemctl status anomonus-bot
```

### View logs
```bash
sudo journalctl -u anomonus-bot -f
```

---

## Step 8: Using Screen (Alternative Method)

If you prefer using screen instead of systemd:

```bash
# Install screen
sudo apt install screen -y

# Create a screen session
screen -S anomonus-bot

# Navigate to bot directory
cd /opt/anomonus-bot
source venv/bin/activate

# Run the bot
python bot.py

# Detach from screen: Press Ctrl+A then D
# Reattach: screen -r anomonus-bot
```

---

## Step 9: Firewall Configuration

### Allow API port (if needed)
```bash
sudo ufw allow 5000/tcp
sudo ufw allow 4000/tcp  # If map website is on same server
sudo ufw reload
```

---

## Step 10: Production Considerations

### 1. Use Production Bot Token
Update `bot.py` to use `REAL_BOT_TOKEN`:
```python
BOT_TOKEN = REAL_BOT_TOKEN  # Change from TEST_BOT_TOKEN
```

### 2. Set Map API URL
```python
MAP_API_URL = "https://your-domain.com"  # Production URL
```

### 3. Enable HTTPS (if exposing API)
Use Nginx as reverse proxy:
```bash
sudo apt install nginx -y
```

Create Nginx config:
```bash
sudo nano /etc/nginx/sites-available/anomonus-bot
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/anomonus-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## Step 11: Monitoring and Maintenance

### View Bot Logs
```bash
# Systemd
sudo journalctl -u anomonus-bot -f

# Screen
screen -r anomonus-bot
```

### Restart Bot
```bash
# Systemd
sudo systemctl restart anomonus-bot

# Screen
screen -r anomonus-bot
# Press Ctrl+C, then run: python bot.py
```

### Stop Bot
```bash
# Systemd
sudo systemctl stop anomonus-bot

# Screen
screen -r anomonus-bot
# Press Ctrl+C
```

### Check if Bot is Running
```bash
# Systemd
sudo systemctl status anomonus-bot

# Screen
screen -ls
```

---

## Step 12: File Permissions

```bash
cd /opt/anomonus-bot
sudo chown -R your-username:your-username .
chmod +x bot.py
```

---

## Troubleshooting

### Bot not starting
1. Check logs: `sudo journalctl -u anomonus-bot -n 50`
2. Check Python version: `python3 --version`
3. Check dependencies: `pip list`
4. Test manually: `python bot.py`

### Connection errors
1. Check internet: `ping api.telegram.org`
2. Check firewall: `sudo ufw status`
3. Check bot token is correct
4. Verify API URL is accessible

### Permission errors
```bash
sudo chown -R your-username:your-username /opt/anomonus-bot
```

### Port already in use
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Kill the process or change port in bot.py
```

---

## Quick Start Commands

```bash
# Navigate to bot directory
cd /opt/anomonus-bot

# Activate virtual environment
source venv/bin/activate

# Run bot (for testing)
python bot.py

# Start as service
sudo systemctl start anomonus-bot

# Check status
sudo systemctl status anomonus-bot

# View logs
sudo journalctl -u anomonus-bot -f

# Restart
sudo systemctl restart anomonus-bot

# Stop
sudo systemctl stop anomonus-bot
```

---

## Directory Structure

```
/opt/anomonus-bot/
├── bot.py
├── requirements.txt
├── venv/
├── subscribed_users.json
├── user_hashes.json
└── .env (optional)
```

---

## Security Best Practices

1. **Don't commit tokens** - Use environment variables
2. **Use firewall** - Only open necessary ports
3. **Regular updates** - Keep system and dependencies updated
4. **Backup data** - Backup `subscribed_users.json` and `user_hashes.json`
5. **Monitor logs** - Check logs regularly for errors
6. **Use HTTPS** - For production API endpoints

---

## Backup

### Backup important files
```bash
# Create backup directory
mkdir -p ~/backups/anomonus-bot

# Backup subscription data
cp /opt/anomonus-bot/subscribed_users.json ~/backups/anomonus-bot/
cp /opt/anomonus-bot/user_hashes.json ~/backups/anomonus-bot/

# Or use cron for automatic backups
```

---

## Update Bot

```bash
cd /opt/anomonus-bot
source venv/bin/activate

# Pull latest changes (if using git)
git pull

# Or upload new files manually

# Restart service
sudo systemctl restart anomonus-bot
```

---

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u anomonus-bot -n 100`
2. Verify all dependencies are installed
3. Check network connectivity
4. Verify bot token is correct
5. Check API URL is accessible


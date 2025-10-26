# Quick Start Guide - 15 Minutes Setup

Get your Nail Lux Telegram bot running in 15 minutes!

## Prerequisites Checklist

Before starting, have these ready:
- [ ] VPS or server with Ubuntu/Debian
- [ ] Root or sudo access
- [ ] Telegram account

## Step 1: Get API Keys (5 minutes)

### 1.1 Telegram Bot Token
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose bot name: `Nail Lux Studio`
4. Choose username: `naillux_studio_bot` (or similar)
5. **Copy the token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 1.2 OpenAI API Key
1. Visit https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. **Copy the key** (starts with `sk-`)

### 1.3 Google Gemini API Key
1. Visit https://ai.google.dev/
2. Click "Get API key"
3. **Copy the key**

### 1.4 Google Sheets Credentials
1. Go to https://console.cloud.google.com/
2. Create new project: "Nail Lux Bot"
3. Enable "Google Sheets API" and "Google Drive API"
4. Create credentials → Service Account
5. Create key → JSON
6. **Download the JSON file**

### 1.5 Get Your Telegram User ID
1. Open Telegram, search for `@userinfobot`
2. Send `/start`
3. **Copy your user ID** (e.g., `123456789`)

## Step 2: Server Setup (5 minutes)

### 2.1 Connect to Server
```bash
ssh root@your-server-ip
```

### 2.2 Install Dependencies
```bash
# Update system
apt update && apt upgrade -y

# Install Python and pip
apt install -y python3 python3-pip python3-venv

# Install git (optional)
apt install -y git
```

### 2.3 Create Project Directory
```bash
mkdir -p /opt/salon-bot
cd /opt/salon-bot
```

### 2.4 Upload Files

**Option A: Using git**
```bash
# If you have files in git repository
git clone your-repo-url .
```

**Option B: Manual upload**
Upload these files to `/opt/salon-bot/`:
- `bot.py`
- `requirements.txt`
- `salon-bot.service`
- `credentials.json` (the Google Service Account file you downloaded)

**Using scp from your local machine:**
```bash
scp bot.py root@your-server-ip:/opt/salon-bot/
scp requirements.txt root@your-server-ip:/opt/salon-bot/
scp salon-bot.service root@your-server-ip:/opt/salon-bot/
scp credentials.json root@your-server-ip:/opt/salon-bot/
```

### 2.5 Install Python Dependencies
```bash
cd /opt/salon-bot

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Step 3: Configuration (3 minutes)

### 3.1 Create .env File
```bash
nano /opt/salon-bot/.env
```

### 3.2 Add Your API Keys
Paste this and replace with your actual keys:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
```

**Replace:**
- `BOT_TOKEN`: Your Telegram bot token from Step 1.1
- `ADMIN_IDS`: Your Telegram user ID from Step 1.5
- `OPENAI_API_KEY`: Your OpenAI key from Step 1.2
- `GEMINI_API_KEY`: Your Gemini key from Step 1.3

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

### 3.3 Verify Files
```bash
ls -la /opt/salon-bot/
```

You should see:
- `bot.py`
- `requirements.txt`
- `.env`
- `credentials.json`
- `venv/` (directory)
- `salon-bot.service`

## Step 4: Test the Bot (1 minute)

### 4.1 Run Bot Manually
```bash
cd /opt/salon-bot
source venv/bin/activate
python bot.py
```

### 4.2 Test on Telegram
1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. You should see the welcome message!

### 4.3 Stop Test
Press `Ctrl+C` to stop the bot

## Step 5: Setup Auto-Start (1 minute)

### 5.1 Install systemd Service
```bash
# Copy service file
cp /opt/salon-bot/salon-bot.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service (auto-start on boot)
systemctl enable salon-bot

# Start service
systemctl start salon-bot
```

### 5.2 Check Status
```bash
systemctl status salon-bot
```

You should see `active (running)` in green.

### 5.3 View Logs
```bash
journalctl -u salon-bot -f
```

Press `Ctrl+C` to exit logs view.

## Step 6: Final Testing (2 minutes)

### 6.1 Test Client Features
1. Send `/start` to bot
2. Click "📅 Записаться на услугу"
3. Select: Маникюр → Any service → Tomorrow → Any time
4. Confirm booking
5. Check "📋 Мои записи"
6. Test cancel or reschedule

### 6.2 Test Voice Messages
1. Send a voice message: "Хочу записаться на маникюр"
2. Bot should transcribe and respond naturally

### 6.3 Test Admin Panel
1. Click "👑 Админ-панель" (should appear since you're admin)
2. Click "📈 Статистика" - should show your user count
3. Click "📊 Записи на сегодня" - should show bookings

### 6.4 Check Google Sheets
1. Go to https://docs.google.com/spreadsheets/
2. Look for "Nail Lux - Записи" spreadsheet
3. Should see your test booking

## Troubleshooting

### Bot not responding?
```bash
# Check if running
systemctl status salon-bot

# Restart
systemctl restart salon-bot

# Check logs
journalctl -u salon-bot -n 50
```

### "Module not found" error?
```bash
# Activate venv and reinstall
cd /opt/salon-bot
source venv/bin/activate
pip install -r requirements.txt
systemctl restart salon-bot
```

### Voice messages not working?
1. Check OpenAI API key in `.env`
2. Check balance: https://platform.openai.com/usage
3. Make sure you have credits ($5+ recommended)

### Google Sheets not syncing?
1. Check `credentials.json` exists in `/opt/salon-bot/`
2. The spreadsheet will be auto-created on first booking
3. Check logs: `journalctl -u salon-bot -n 100 | grep -i sheets`

### Admin panel not showing?
1. Verify your user ID in `.env` under `ADMIN_IDS`
2. Make sure there are no spaces: `ADMIN_IDS=123456789`
3. Restart bot: `systemctl restart salon-bot`

## Useful Commands

```bash
# Start bot
systemctl start salon-bot

# Stop bot
systemctl stop salon-bot

# Restart bot
systemctl restart salon-bot

# Check status
systemctl status salon-bot

# View logs (real-time)
journalctl -u salon-bot -f

# View last 100 log lines
journalctl -u salon-bot -n 100
```

## Next Steps

### Customize Your Bot

1. **Edit Services** (prices, durations):
   ```bash
   nano /opt/salon-bot/bot.py
   # Find SERVICES dictionary around line 85
   # Edit and save
   systemctl restart salon-bot
   ```

2. **Change Work Hours**:
   ```bash
   nano /opt/salon-bot/bot.py
   # Find WORK_HOURS around line 60
   # Edit and save
   systemctl restart salon-bot
   ```

3. **Change Reminder Time**:
   ```bash
   nano /opt/salon-bot/bot.py
   # Find REMINDER_TIME around line 75
   # Edit and save
   systemctl restart salon-bot
   ```

### Setup Backup

```bash
# Create backup directory
mkdir -p /root/backups

# Manual backup
cp /opt/salon-bot/salon_bot.db /root/backups/backup_$(date +%Y%m%d).db

# Automatic daily backup (cron)
crontab -e
# Add this line:
0 2 * * * cp /opt/salon-bot/salon_bot.db /root/backups/backup_$(date +\%Y\%m\%d).db
```

### Monitor Your Bot

```bash
# Create monitoring script
nano /root/check_bot.sh
```

Add:
```bash
#!/bin/bash
if ! systemctl is-active --quiet salon-bot; then
    systemctl start salon-bot
    echo "Bot was down, restarted at $(date)" >> /root/bot_restarts.log
fi
```

Save and:
```bash
chmod +x /root/check_bot.sh

# Add to cron (check every 5 minutes)
crontab -e
# Add:
*/5 * * * * /root/check_bot.sh
```

## Security Checklist

- [ ] Keep `.env` file secure (don't share it)
- [ ] Never commit credentials to git
- [ ] Regularly update dependencies: `pip install -r requirements.txt --upgrade`
- [ ] Monitor API usage and costs
- [ ] Setup firewall on VPS
- [ ] Regular database backups

## Cost Estimate

Monthly costs:
- VPS: $5-10
- OpenAI Whisper: $5-15 (varies with usage)
- Google Gemini: Free (up to 1,500 requests/day)
- Total: ~$10-25/month

## Support

If you encounter issues:

1. **Check logs first**: `journalctl -u salon-bot -n 100`
2. **Common solutions**: See Troubleshooting section above
3. **Review full docs**: See [README.md](README.md)

---

## Success Checklist

- [ ] Bot responds to `/start`
- [ ] Can create booking
- [ ] Booking shows in "Мои записи"
- [ ] Voice messages work
- [ ] AI assistant responds
- [ ] Admin panel accessible
- [ ] Google Sheets syncing
- [ ] Bot auto-starts on server reboot
- [ ] Logs accessible
- [ ] Backup configured

If all checked ✓ - **Congratulations!** Your bot is ready for production! 🎉

---

**Need help?** Review the full [README.md](README.md) for detailed documentation.

**Ready to go live?** Share your bot with clients and start taking bookings! 💅✨

# Nail Lux Studio - Telegram Bot

Production-ready Telegram bot for nail salon with voice message support, AI assistant, Google Sheets integration, and automated reminders.

## Features

### Client Features
- **Booking System**: Easy booking flow with 22 services across 4 categories
- **Voice Support**: Send voice messages - bot transcribes and responds naturally
- **AI Assistant**: Powered by Google Gemini for natural conversations
- **Booking Management**: View, cancel, and reschedule appointments
- **Automated Reminders**: Get reminders 24 hours before appointments
- **Multi-language Support**: Russian language interface

### Admin Features
- **Separate Admin Bot**: Dedicated Telegram bot for administrators ([@naillux_admin_bot](ADMIN_SETUP.md))
- **Web Admin Panel**: Full-featured dashboard with statistics and charts
- **Group Notifications**: Automatic alerts to private Telegram group
- **Today's Bookings**: View all bookings for the day with revenue
- **Weekly/Monthly Stats**: Financial reports and analytics
- **Client Database**: Track all clients and their visit history
- **Broadcast**: Send messages to all users
- **Google Sheets Sync**: All bookings automatically synced to spreadsheet

**→ [Admin Panel Setup Guide](ADMIN_SETUP.md)** - Complete instructions for admin system

### Services Catalog

#### Маникюр (Manicure)
- Маникюр с гель-лаком - 3,900₽ (90 min)
- Маникюр с гель-лаком (френч) - 4,600₽ (100 min)
- Маникюр без покрытия - 2,600₽ (60 min)
- Маникюр с лаком - 3,100₽ (70 min)
- Мужской маникюр - 2,600₽ (60 min)
- Детский маникюр - 1,900₽ (45 min)
- Снятие гель-лака - 700₽ (30 min)

#### Педикюр (Pedicure)
- Педикюр Golden Trace с гель-лаком - 4,100₽ (120 min)
- Педикюр Golden Trace без покрытия - 3,500₽ (90 min)
- Педикюр Golden Trace с лаком - 4,100₽ (120 min)
- Экспресс педикюр + гель-лак - 3,800₽ (90 min)
- Экспресс педикюр - 2,800₽ (60 min)
- Мужской педикюр Golden Trace - 3,500₽ (90 min)

#### Моделирование (Modeling & Extensions)
- Наращивание с гель-лаком - 4,900₽ (150 min)
- Наращивание френч - 5,600₽ (160 min)
- Укрепление с гель-лаком - 4,300₽ (100 min)
- Укрепление с гель-лаком (френч) - 5,000₽ (110 min)
- Коррекция с гель-лаком - 4,300₽ (100 min)
- Коррекция с гель-лаком (френч) - 5,000₽ (110 min)

#### Уход (Treatment & Care)
- IBX System - 700₽ (30 min)
- SPA-программа для рук - 1,300₽ (45 min)
- SPA-программа для ног - 1,500₽ (60 min)

## Technology Stack

- **Python**: 3.8+
- **Framework**: python-telegram-bot 20.7
- **Database**: SQLite (local) + Google Sheets (cloud sync)
- **AI Services**:
  - OpenAI Whisper API (voice-to-text)
  - Google Gemini API (AI assistant, free tier)
- **Infrastructure**: systemd service

## Installation

### Prerequisites

1. **VPS or Server** with Ubuntu/Debian
2. **Python 3.8+** installed
3. **API Keys**:
   - Telegram Bot Token (from @BotFather)
   - OpenAI API Key (for Whisper)
   - Google Gemini API Key (free tier)
   - Google Service Account credentials (for Sheets)

### Quick Setup (15 minutes)

See [QUICKSTART.md](QUICKSTART.md) for detailed step-by-step guide.

### Detailed Installation

#### 1. Get API Keys

**Telegram Bot:**
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to get bot token

**OpenAI API:**
1. Visit https://platform.openai.com/api-keys
2. Create new API key
3. Copy the key

**Google Gemini API:**
1. Visit https://ai.google.dev/
2. Get API key (free tier available)

**Google Sheets API:**
1. Go to https://console.cloud.google.com/
2. Create new project
3. Enable Google Sheets API
4. Create Service Account
5. Download JSON credentials file

#### 2. Server Setup

```bash
# Create directory
mkdir -p /opt/salon-bot
cd /opt/salon-bot

# Clone or upload files
# Upload: bot.py, requirements.txt

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configuration

**Create .env file:**
```bash
nano .env
```

**Add your credentials:**
```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456789,987654321
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Upload Google credentials:**
- Upload your `credentials.json` file to `/opt/salon-bot/`

#### 4. Test the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run bot
python bot.py
```

Test by sending `/start` to your bot on Telegram.

#### 5. Setup systemd Service

```bash
# Copy service file
cp salon-bot.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable salon-bot
systemctl start salon-bot

# Check status
systemctl status salon-bot
```

#### 6. View Logs

```bash
# Real-time logs
journalctl -u salon-bot -f

# Last 100 lines
journalctl -u salon-bot -n 100
```

## Usage

### For Clients

1. **Start**: Send `/start` to the bot
2. **Book**: Click "📅 Записаться на услугу"
3. **Select**: Choose category → service → date → time
4. **Confirm**: Review and confirm booking
5. **Manage**: View/cancel/reschedule in "📋 Мои записи"
6. **Ask Questions**: Send text or voice messages

### For Admins

1. Click "👑 Админ-панель"
2. **Today's Bookings**: View all bookings with revenue
3. **Broadcast**: Send message to all users
4. **Statistics**: View user and booking stats

## Configuration

### Business Hours

Edit in `bot.py`:
```python
WORK_HOURS = {
    'start': 9,      # 9:00 AM
    'end': 20,       # 8:00 PM
    'lunch_start': 13,  # 1:00 PM
    'lunch_end': 14     # 2:00 PM
}
```

### Reminders

Edit in `bot.py`:
```python
REMINDER_TIME = time(hour=18, minute=0)  # Send at 18:00
```

### Services

Edit the `SERVICES` dictionary in `bot.py` to add/modify services.

## Database

### SQLite Structure

**users table:**
- `user_id` - Telegram user ID (primary key)
- `username` - Telegram username
- `first_name` - User's first name
- `phone` - Phone number (optional)
- `created_at` - Registration timestamp

**bookings table:**
- `id` - Booking ID (auto-increment)
- `user_id` - Foreign key to users
- `service_id` - Service identifier
- `date` - Booking date
- `time` - Booking time
- `status` - 'active' or 'cancelled'
- `created_at` - Creation timestamp
- `reminder_sent` - Boolean flag

### Database Backup

```bash
# Create backup
cp /opt/salon-bot/salon_bot.db /root/backups/backup_$(date +%Y%m%d).db

# Automate with cron (daily at 2 AM)
0 2 * * * cp /opt/salon-bot/salon_bot.db /root/backups/backup_$(date +\%Y\%m\%d).db
```

## Google Sheets Integration

### Setup

1. Upload `credentials.json` to project directory
2. Share spreadsheet with service account email
3. Bot will auto-create "Nail Lux - Записи" sheet

### Sheet Structure

| ID | Клиент | Username | Телефон | Услуга | Дата | Время | Статус | Создано |
|----|--------|----------|---------|--------|------|-------|--------|---------|

All bookings are automatically synced in real-time.

## Troubleshooting

### Bot Not Responding

```bash
# Check if running
systemctl status salon-bot

# Check logs
journalctl -u salon-bot -n 50

# Restart
systemctl restart salon-bot
```

### Voice Messages Not Working

1. Check OpenAI API key in `.env`
2. Check API balance: https://platform.openai.com/usage
3. View error logs: `journalctl -u salon-bot -n 100 | grep -i whisper`

### AI Assistant Not Responding

1. Check Gemini API key in `.env`
2. Check API quota: https://ai.google.dev/
3. View error logs: `journalctl -u salon-bot -n 100 | grep -i gemini`

### Google Sheets Not Syncing

1. Check `credentials.json` exists
2. Check service account has access to sheet
3. View error logs: `journalctl -u salon-bot -n 100 | grep -i sheets`

### Database Locked

```bash
# Check if multiple instances running
ps aux | grep bot.py

# Kill duplicate processes
killall -9 python
systemctl restart salon-bot
```

## Security

### API Keys
- Never commit `.env` to version control
- Rotate keys if compromised
- Use environment variables only

### Admin Access
- Add admin user IDs in `.env`
- Admin commands check permissions
- All admin actions are logged

### Data Privacy
- Minimal user data stored
- No sensitive information in logs
- GDPR-compliant data handling

## Performance

### Response Times
- Message response: < 2 seconds
- Voice processing: < 10 seconds
- Booking creation: < 1 second

### Scalability
- Supports up to 1,000 users
- 500 bookings per day
- 100 concurrent users

### Resource Usage
- RAM: ~100-200 MB
- Disk: ~100 MB per year
- CPU: Minimal (<5% average)

## Maintenance

### Regular Tasks

**Daily:**
- Check logs for errors
- Verify reminders sent

**Weekly:**
- Review booking statistics
- Check API usage/costs

**Monthly:**
- Database backup
- Update dependencies if needed
- Review and optimize performance

### Updates

```bash
# Backup database first
cp salon_bot.db salon_bot.db.backup

# Update code
# (upload new bot.py)

# Restart service
systemctl restart salon-bot

# Monitor logs
journalctl -u salon-bot -f
```

## Cost Estimate

### Monthly Costs
- **VPS**: $5-10 (basic)
- **OpenAI Whisper**: $5-15 (depending on voice usage)
- **Google Gemini**: Free tier (up to 1,500 requests/day)
- **Google Sheets**: Free
- **Telegram Bot**: Free

**Total**: ~$10-25/month

## Support

### Documentation
- [QUICKSTART.md](QUICKSTART.md) - 15-minute setup guide
- [Technical Specification](SPEC.md) - Full technical details

### Logs
```bash
# Real-time logs
journalctl -u salon-bot -f

# Error logs only
journalctl -u salon-bot -p err

# Last hour
journalctl -u salon-bot --since "1 hour ago"
```

### Common Commands
```bash
# Start bot
systemctl start salon-bot

# Stop bot
systemctl stop salon-bot

# Restart bot
systemctl restart salon-bot

# Status
systemctl status salon-bot

# Logs
journalctl -u salon-bot -f
```

## License

MIT License - feel free to use and modify for your nail salon!

## Credits

Built with:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [OpenAI Whisper](https://openai.com/research/whisper)
- [Google Gemini](https://ai.google.dev/)
- [gspread](https://github.com/burnash/gspread)

---

**Nail Lux Studio** - Your beauty at your fingertips! 💅✨

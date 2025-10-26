#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nail Lux Studio - Telegram Bot
Production-ready bot for nail salon with voice support, AI assistant, and automated reminders
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime, timedelta, time
from typing import Dict, List, Tuple, Optional
import asyncio

from dotenv import load_dotenv
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# OpenAI for Whisper
import openai

# Google Gemini
import google.generativeai as genai

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
NOTIFICATION_GROUP_ID = os.getenv('NOTIFICATION_GROUP_ID', '')  # Telegram group for notifications

# Configure APIs
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

# Timezone
TIMEZONE = pytz.timezone('Europe/Moscow')

# Database
DB_PATH = 'salon_bot.db'

# Work hours
WORK_HOURS = {
    'start': 9,
    'end': 20,
    'lunch_start': 13,
    'lunch_end': 14
}

# Reminder settings
REMINDER_TIME = time(hour=18, minute=0)

# Conversation states
SELECT_CATEGORY = 0
SELECT_SERVICE = 1
SELECT_DATE = 2
SELECT_TIME = 3
CONFIRM_BOOKING = 4
CANCEL_SELECT = 5
CANCEL_CONFIRM = 6
RESCHEDULE_SELECT = 7
RESCHEDULE_DATE = 8
RESCHEDULE_TIME = 9
RESCHEDULE_CONFIRM = 10
ADMIN_BROADCAST = 11

# ============================================================================
# SERVICE CATALOG
# ============================================================================

SERVICES = {
    # Manicure (7 services)
    'manicure_gel': {
        'name': '💅 Маникюр с гель-лаком',
        'duration': 90,
        'price': 3900,
        'category': 'Маникюр'
    },
    'manicure_gel_french': {
        'name': '💅 Маникюр с гель-лаком (френч)',
        'duration': 100,
        'price': 4600,
        'category': 'Маникюр'
    },
    'manicure_no_coat': {
        'name': '💅 Маникюр без покрытия',
        'duration': 60,
        'price': 2600,
        'category': 'Маникюр'
    },
    'manicure_regular': {
        'name': '💅 Маникюр с лаком',
        'duration': 70,
        'price': 3100,
        'category': 'Маникюр'
    },
    'manicure_men': {
        'name': '👔 Мужской маникюр',
        'duration': 60,
        'price': 2600,
        'category': 'Маникюр'
    },
    'manicure_kids': {
        'name': '👧 Детский маникюр',
        'duration': 45,
        'price': 1900,
        'category': 'Маникюр'
    },
    'gel_removal': {
        'name': '🔧 Снятие гель-лака',
        'duration': 30,
        'price': 700,
        'category': 'Маникюр'
    },

    # Pedicure (6 services)
    'pedicure_gel': {
        'name': '👣 Педикюр Golden Trace с гель-лаком',
        'duration': 120,
        'price': 4100,
        'category': 'Педикюр'
    },
    'pedicure_no_coat': {
        'name': '👣 Педикюр Golden Trace без покрытия',
        'duration': 90,
        'price': 3500,
        'category': 'Педикюр'
    },
    'pedicure_regular': {
        'name': '👣 Педикюр Golden Trace с лаком',
        'duration': 120,
        'price': 4100,
        'category': 'Педикюр'
    },
    'pedicure_express_gel': {
        'name': '⚡ Экспресс педикюр + гель-лак',
        'duration': 90,
        'price': 3800,
        'category': 'Педикюр'
    },
    'pedicure_express': {
        'name': '⚡ Экспресс педикюр',
        'duration': 60,
        'price': 2800,
        'category': 'Педикюр'
    },
    'pedicure_men': {
        'name': '👔 Мужской педикюр Golden Trace',
        'duration': 90,
        'price': 3500,
        'category': 'Педикюр'
    },

    # Extensions & Modeling (6 services)
    'extension_gel': {
        'name': '💎 Наращивание с гель-лаком',
        'duration': 150,
        'price': 4900,
        'category': 'Моделирование'
    },
    'extension_french': {
        'name': '💎 Наращивание френч',
        'duration': 160,
        'price': 5600,
        'category': 'Моделирование'
    },
    'strengthening': {
        'name': '💪 Укрепление с гель-лаком',
        'duration': 100,
        'price': 4300,
        'category': 'Моделирование'
    },
    'strengthening_french': {
        'name': '💪 Укрепление с гель-лаком (френч)',
        'duration': 110,
        'price': 5000,
        'category': 'Моделирование'
    },
    'correction': {
        'name': '🔄 Коррекция с гель-лаком',
        'duration': 100,
        'price': 4300,
        'category': 'Моделирование'
    },
    'correction_french': {
        'name': '🔄 Коррекция с гель-лаком (френч)',
        'duration': 110,
        'price': 5000,
        'category': 'Моделирование'
    },

    # Treatment & Care (3 services)
    'ibx_system': {
        'name': '💊 IBX System',
        'duration': 30,
        'price': 700,
        'category': 'Уход'
    },
    'spa_hands': {
        'name': '🌸 SPA-программа для рук',
        'duration': 45,
        'price': 1300,
        'category': 'Уход'
    },
    'spa_feet': {
        'name': '🌸 SPA-программа для ног',
        'duration': 60,
        'price': 1500,
        'category': 'Уход'
    },
}

# AI System Prompt
SYSTEM_PROMPT = """Ты — AI помощник студии маникюра "Nail Lux".

ТВОЯ РОЛЬ:
- Ты дружелюбный и профессиональный администратор студии
- Помогаешь клиентам записаться на услуги, отвечаешь на вопросы
- Общаешься естественно, по-человечески, без шаблонных фраз
- НЕ используй фразы типа "вы сказали", "я распознала", "голосовое сообщение" - просто отвечай по существу

ВАЖНЫЕ ПРАВИЛА:
1. ТОЛЬКО про студию маникюра - НЕ отвечай на посторонние темы (погода, новости, советы не про ногти)
2. Если спрашивают не про маникюр/педикюр - вежливо перенаправь к записи
3. Используй продающие техники:
   - Предлагай альтернативное время, если клиент не может
   - Рекомендуй дополнительные услуги (SPA, дизайн, IBX)
   - Упоминай спецпредложения и акции
   - Подчеркивай выгоду комбо-услуг

ИНФОРМАЦИЯ О СТУДИИ:
Название: Nail Lux
Услуги: маникюр, педикюр, наращивание, моделирование, уход
Часы работы: 9:00 - 20:00 (обед 13:00-14:00)
Адрес: уточняется при записи

ТОПОВЫЕ УСЛУГИ:
- Маникюр с гель-лаком: 3,900₽ (90 мин)
- Педикюр Golden Trace с гель-лаком: 4,100₽ (120 мин)
- Наращивание с гель-лаком: 4,900₽ (150 мин)

ДОПОЛНИТЕЛЬНО:
- SPA-уход для рук: 1,300₽
- SPA-уход для ног: 1,500₽
- IBX System (лечение): 700₽
- Дизайны от 100₽/ноготь

СТИЛЬ ОБЩЕНИЯ:
✅ "Отлично! Записываю вас на маникюр"
✅ "13 числа в 16:30 вас устроит?"
✅ "Могу предложить 15:00 или 17:00"
✅ "А вы пробовали нашу SPA-программу? Ручки будут как у принцессы! 😊"

❌ "Вы сказали..."
❌ "Я распознала ваше голосовое..."
❌ "Согласно вашему запросу..."

Будь живой, дружелюбной и полезной! 💅✨"""

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_id TEXT,
            date DATE,
            time TIME,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reminder_sent BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def add_user(user_id: int, username: str, first_name: str):
    """Add or update user in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    ''', (user_id, username, first_name))

    conn.commit()
    conn.close()

def get_user(user_id: int) -> Optional[Tuple]:
    """Get user from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    conn.close()
    return user

def create_booking(user_id: int, service_id: str, date: str, time: str) -> int:
    """Create new booking and return booking ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO bookings (user_id, service_id, date, time)
        VALUES (?, ?, ?, ?)
    ''', (user_id, service_id, date, time))

    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.info(f"Booking created: ID={booking_id}, user={user_id}, service={service_id}, date={date}, time={time}")
    return booking_id

def get_user_bookings(user_id: int) -> List[Tuple]:
    """Get all active bookings for user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, service_id, date, time
        FROM bookings
        WHERE user_id = ? AND status = 'active'
        ORDER BY date, time
    ''', (user_id,))

    bookings = cursor.fetchall()
    conn.close()

    return bookings

def cancel_booking(booking_id: int):
    """Cancel booking by ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE bookings
        SET status = 'cancelled'
        WHERE id = ?
    ''', (booking_id,))

    conn.commit()
    conn.close()

    logger.info(f"Booking cancelled: ID={booking_id}")

def get_booked_times(date: str) -> List[str]:
    """Get all booked time slots for a specific date"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT time FROM bookings
        WHERE date = ? AND status = 'active'
    ''', (date,))

    times = [row[0] for row in cursor.fetchall()]
    conn.close()

    return times

def get_today_bookings() -> List[Tuple]:
    """Get all active bookings for today"""
    today = datetime.now(TIMEZONE).date().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.id, b.user_id, b.service_id, b.time, u.first_name, u.username
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.date = ? AND b.status = 'active'
        ORDER BY b.time
    ''', (today,))

    bookings = cursor.fetchall()
    conn.close()

    return bookings

def get_tomorrow_bookings() -> List[Tuple]:
    """Get all active bookings for tomorrow (for reminders)"""
    tomorrow = (datetime.now(TIMEZONE) + timedelta(days=1)).date().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.id, b.user_id, b.service_id, b.time, u.first_name
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.date = ? AND b.status = 'active' AND b.reminder_sent = 0
    ''', (tomorrow,))

    bookings = cursor.fetchall()
    conn.close()

    return bookings

def mark_reminder_sent(booking_id: int):
    """Mark reminder as sent for booking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE bookings
        SET reminder_sent = 1
        WHERE id = ?
    ''', (booking_id,))

    conn.commit()
    conn.close()

def get_statistics() -> Dict:
    """Get bot statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    # Active bookings
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE status = "active"')
    active_bookings = cursor.fetchone()[0]

    # Today's bookings
    today = datetime.now(TIMEZONE).date().isoformat()
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE date = ? AND status = "active"', (today,))
    today_bookings = cursor.fetchone()[0]

    conn.close()

    return {
        'total_users': total_users,
        'active_bookings': active_bookings,
        'today_bookings': today_bookings
    }

def get_all_user_ids() -> List[int]:
    """Get all user IDs for broadcast"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users')
    user_ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return user_ids

# ============================================================================
# GOOGLE SHEETS INTEGRATION
# ============================================================================

def get_sheets_client():
    """Get Google Sheets client"""
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets client: {e}")
        return None

def sync_booking_to_sheets(booking_id: int, user_id: int, service_id: str, date: str, time: str):
    """Sync booking to Google Sheets"""
    try:
        client = get_sheets_client()
        if not client:
            return

        # Open or create sheet
        try:
            sheet = client.open('Nail Lux - Записи').sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            spreadsheet = client.create('Nail Lux - Записи')
            sheet = spreadsheet.sheet1
            # Set headers
            sheet.append_row(['ID', 'Клиент', 'Username', 'Телефон', 'Услуга', 'Дата', 'Время', 'Статус', 'Создано'])

        # Get user data
        user = get_user(user_id)
        first_name = user[2] if user else 'Unknown'
        username = user[1] if user else ''
        phone = user[3] if user and len(user) > 3 else ''

        # Get service name
        service_name = SERVICES.get(service_id, {}).get('name', service_id)

        # Current timestamp
        created_at = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

        # Append row
        sheet.append_row([
            booking_id,
            first_name,
            f"@{username}" if username else '',
            phone,
            service_name,
            date,
            time,
            'active',
            created_at
        ])

        logger.info(f"Booking {booking_id} synced to Google Sheets")

    except Exception as e:
        logger.error(f"Failed to sync booking to Google Sheets: {e}")

def update_booking_status_in_sheets(booking_id: int, status: str):
    """Update booking status in Google Sheets"""
    try:
        client = get_sheets_client()
        if not client:
            return

        sheet = client.open('Nail Lux - Записи').sheet1

        # Find booking by ID
        cell = sheet.find(str(booking_id))
        if cell:
            # Update status column (column 8)
            sheet.update_cell(cell.row, 8, status)
            logger.info(f"Booking {booking_id} status updated to {status} in Google Sheets")

    except Exception as e:
        logger.error(f"Failed to update booking status in Google Sheets: {e}")

# ============================================================================
# NOTIFICATION FUNCTIONS
# ============================================================================

async def send_group_notification(context: ContextTypes.DEFAULT_TYPE, message: str, parse_mode: str = 'HTML'):
    """Send notification to admin group"""
    if not NOTIFICATION_GROUP_ID:
        return

    try:
        await context.bot.send_message(
            chat_id=NOTIFICATION_GROUP_ID,
            text=message,
            parse_mode=parse_mode
        )
        logger.info("Notification sent to admin group")
    except Exception as e:
        logger.error(f"Failed to send group notification: {e}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_categories() -> List[str]:
    """Get unique service categories"""
    categories = set()
    for service in SERVICES.values():
        categories.add(service['category'])
    return sorted(list(categories))

def get_services_by_category(category: str) -> Dict:
    """Get all services in a category"""
    return {k: v for k, v in SERVICES.items() if v['category'] == category}

def format_date(date_str: str) -> str:
    """Format date for display"""
    date = datetime.fromisoformat(date_str)
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    return f"{date.day} {months[date.month]}"

def get_available_dates(days: int = 14) -> List[str]:
    """Get next N available dates"""
    dates = []
    today = datetime.now(TIMEZONE).date()

    for i in range(days):
        date = today + timedelta(days=i)
        dates.append(date.isoformat())

    return dates

def get_available_time_slots(date: str, service_duration: int) -> List[str]:
    """Get available time slots for a date"""
    # Get booked times
    booked_times = get_booked_times(date)

    # Generate all possible slots
    slots = []
    current_hour = WORK_HOURS['start']

    while current_hour < WORK_HOURS['end']:
        for minute in [0, 30]:
            # Skip lunch break
            if current_hour == WORK_HOURS['lunch_start'] or \
               (current_hour == WORK_HOURS['lunch_start'] - 1 and minute == 30):
                continue

            time_str = f"{current_hour:02d}:{minute:02d}"

            # Check if service fits before end time
            slot_time = datetime.strptime(time_str, '%H:%M')
            end_time = slot_time + timedelta(minutes=service_duration)
            end_hour = end_time.hour + (end_time.minute / 60)

            if end_hour <= WORK_HOURS['end']:
                # Check if slot is not booked
                if time_str not in booked_times:
                    slots.append(time_str)

        current_hour += 1

    return slots

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

# ============================================================================
# KEYBOARD BUILDERS
# ============================================================================

def build_main_menu(user_id: int) -> InlineKeyboardMarkup:
    """Build main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📅 Записаться на услугу", callback_data="book")],
        [InlineKeyboardButton("📋 Мои записи", callback_data="my_bookings")],
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="ask_question")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
    ]

    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(keyboard)

def build_categories_keyboard() -> InlineKeyboardMarkup:
    """Build service categories keyboard"""
    categories = get_categories()
    keyboard = []

    category_icons = {
        'Маникюр': '📂',
        'Педикюр': '📂',
        'Моделирование': '📂',
        'Уход': '📂'
    }

    for category in categories:
        icon = category_icons.get(category, '📂')
        keyboard.append([InlineKeyboardButton(
            f"{icon} {category}",
            callback_data=f"category_{category}"
        )])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])

    return InlineKeyboardMarkup(keyboard)

def build_services_keyboard(category: str) -> InlineKeyboardMarkup:
    """Build services keyboard for category"""
    services = get_services_by_category(category)
    keyboard = []

    for service_id, service in services.items():
        button_text = f"{service['name']}\n💰 {service['price']}₽ | ⏱ {service['duration']} мин"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"service_{service_id}"
        )])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")])

    return InlineKeyboardMarkup(keyboard)

def build_dates_keyboard() -> InlineKeyboardMarkup:
    """Build dates keyboard"""
    dates = get_available_dates(14)
    keyboard = []

    # Show 2 dates per row
    for i in range(0, len(dates), 2):
        row = []
        for j in range(i, min(i + 2, len(dates))):
            date_str = dates[j]
            formatted = format_date(date_str)
            row.append(InlineKeyboardButton(formatted, callback_data=f"date_{date_str}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_categories")])

    return InlineKeyboardMarkup(keyboard)

def build_time_slots_keyboard(date: str, service_id: str) -> InlineKeyboardMarkup:
    """Build time slots keyboard"""
    service = SERVICES[service_id]
    slots = get_available_time_slots(date, service['duration'])

    keyboard = []

    if not slots:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Выбрать другую дату", callback_data="back_to_dates")]
        ])

    # Show 3 slots per row
    for i in range(0, len(slots), 3):
        row = []
        for j in range(i, min(i + 3, len(slots))):
            slot = slots[j]
            row.append(InlineKeyboardButton(slot, callback_data=f"time_{slot}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_dates")])

    return InlineKeyboardMarkup(keyboard)

def build_admin_menu() -> InlineKeyboardMarkup:
    """Build admin menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("📊 Записи на сегодня", callback_data="admin_today")],
        [InlineKeyboardButton("📢 Рассылка всем", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📈 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")],
    ]

    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    # Add user to database
    add_user(user.id, user.username or '', user.first_name or '')

    welcome_message = f"""Привет, {user.first_name}! 👋

Добро пожаловать в студию маникюра Nail Lux ✨

Я помогу вам:
• Записаться на маникюр, педикюр или наращивание 💅
• Посмотреть ваши записи
• Ответить на вопросы
• Подобрать подходящую услугу

Вы можете писать текстом или отправлять голосовые сообщения 🎤

Выберите действие:"""

    await update.message.reply_text(
        welcome_message,
        reply_markup=build_main_menu(user.id)
    )

    logger.info(f"User {user.id} ({user.first_name}) started the bot")

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # Main menu
    if data == "back_to_menu":
        await query.edit_message_text(
            "Выберите действие:",
            reply_markup=build_main_menu(user_id)
        )
        return ConversationHandler.END

    # Contacts
    elif data == "contacts":
        contacts_text = """📞 Контакты студии Nail Lux

📍 Адрес: уточняется при записи
🕐 Часы работы: 9:00 - 20:00 (без выходных)
⏸ Обед: 13:00 - 14:00

💬 Есть вопросы? Просто напишите мне!"""

        await query.edit_message_text(
            contacts_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return ConversationHandler.END

    # Ask question (AI assistant will handle)
    elif data == "ask_question":
        await query.edit_message_text(
            "💬 Задайте свой вопрос текстом или голосовым сообщением, и я с радостью отвечу!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return ConversationHandler.END

    # Admin panel
    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("⛔️ Доступ запрещен")
            return ConversationHandler.END

        await query.edit_message_text(
            "👑 Админ-панель\n\nВыберите действие:",
            reply_markup=build_admin_menu()
        )
        return ConversationHandler.END

    # Start booking flow
    elif data == "book":
        await query.edit_message_text(
            "📂 Выберите категорию услуг:",
            reply_markup=build_categories_keyboard()
        )
        return SELECT_CATEGORY

    # My bookings
    elif data == "my_bookings":
        await show_user_bookings(query, user_id)
        return ConversationHandler.END

async def show_user_bookings(query, user_id: int):
    """Show user's active bookings"""
    bookings = get_user_bookings(user_id)

    if not bookings:
        await query.edit_message_text(
            "У вас пока нет активных записей.\n\nХотите записаться?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📅 Записаться", callback_data="book")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return

    text = "📋 Ваши записи:\n\n"
    keyboard = []

    for booking_id, service_id, date, time in bookings:
        service = SERVICES.get(service_id, {})
        service_name = service.get('name', 'Неизвестная услуга')
        price = service.get('price', 0)

        formatted_date = format_date(date)
        text += f"• {service_name}\n"
        text += f"  📅 {formatted_date} в {time}\n"
        text += f"  💰 {price}₽\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"🗑 Отменить запись на {formatted_date}",
                callback_data=f"cancel_{booking_id}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🔄 Перенести запись на {formatted_date}",
                callback_data=f"reschedule_{booking_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================================
# BOOKING FLOW HANDLERS
# ============================================================================

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_categories":
        await query.edit_message_text(
            "📂 Выберите категорию услуг:",
            reply_markup=build_categories_keyboard()
        )
        return SELECT_CATEGORY

    category = data.replace("category_", "")
    context.user_data['selected_category'] = category

    await query.edit_message_text(
        f"📂 {category}\n\nВыберите услугу:",
        reply_markup=build_services_keyboard(category)
    )

    return SELECT_SERVICE

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_categories":
        await query.edit_message_text(
            "📂 Выберите категорию услуг:",
            reply_markup=build_categories_keyboard()
        )
        return SELECT_CATEGORY

    service_id = data.replace("service_", "")
    context.user_data['selected_service'] = service_id

    service = SERVICES[service_id]

    await query.edit_message_text(
        f"{service['name']}\n💰 {service['price']}₽ | ⏱ {service['duration']} мин\n\n📅 Выберите дату:",
        reply_markup=build_dates_keyboard()
    )

    return SELECT_DATE

async def date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_categories":
        category = context.user_data.get('selected_category')
        await query.edit_message_text(
            f"📂 {category}\n\nВыберите услугу:",
            reply_markup=build_services_keyboard(category)
        )
        return SELECT_SERVICE

    if data == "back_to_dates":
        service_id = context.user_data.get('selected_service')
        service = SERVICES[service_id]
        await query.edit_message_text(
            f"{service['name']}\n💰 {service['price']}₽ | ⏱ {service['duration']} мин\n\n📅 Выберите дату:",
            reply_markup=build_dates_keyboard()
        )
        return SELECT_DATE

    date = data.replace("date_", "")
    context.user_data['selected_date'] = date

    service_id = context.user_data.get('selected_service')
    service = SERVICES[service_id]

    slots = get_available_time_slots(date, service['duration'])

    if not slots:
        await query.edit_message_text(
            f"К сожалению, на {format_date(date)} все места заняты 😔\n\nВыберите другую дату:",
            reply_markup=build_dates_keyboard()
        )
        return SELECT_DATE

    await query.edit_message_text(
        f"📅 {format_date(date)}\n\n🕐 Выберите время:",
        reply_markup=build_time_slots_keyboard(date, service_id)
    )

    return SELECT_TIME

async def time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_dates":
        service_id = context.user_data.get('selected_service')
        service = SERVICES[service_id]
        await query.edit_message_text(
            f"{service['name']}\n💰 {service['price']}₽ | ⏱ {service['duration']} мин\n\n📅 Выберите дату:",
            reply_markup=build_dates_keyboard()
        )
        return SELECT_DATE

    time = data.replace("time_", "")
    context.user_data['selected_time'] = time

    # Show confirmation
    service_id = context.user_data.get('selected_service')
    date = context.user_data.get('selected_date')
    service = SERVICES[service_id]

    confirmation_text = f"""✅ Подтвердите запись:

{service['name']}
📅 {format_date(date)}
🕐 {time}
💰 {service['price']}₽

Все верно?"""

    keyboard = [
        [InlineKeyboardButton("✅ Да, записать!", callback_data="confirm_booking")],
        [InlineKeyboardButton("❌ Отмена", callback_data="back_to_menu")]
    ]

    await query.edit_message_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CONFIRM_BOOKING

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and create booking"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_menu":
        await query.edit_message_text(
            "Запись отменена.\n\nВыберите действие:",
            reply_markup=build_main_menu(query.from_user.id)
        )
        return ConversationHandler.END

    # Create booking
    user_id = query.from_user.id
    service_id = context.user_data.get('selected_service')
    date = context.user_data.get('selected_date')
    time = context.user_data.get('selected_time')

    booking_id = create_booking(user_id, service_id, date, time)

    # Sync to Google Sheets
    sync_booking_to_sheets(booking_id, user_id, service_id, date, time)

    # Send notification to admin group
    user = query.from_user
    service = SERVICES[service_id]
    notification_text = f"""🎉 <b>Новая запись!</b>

👤 {user.first_name} {'@' + user.username if user.username else ''}
💅 {service['name']}
📅 {format_date(date)} в {time}
💰 {service['price']:,}₽

ID записи: #{booking_id}"""

    await send_group_notification(context, notification_text)

    # Send confirmation

    confirmation_message = f"""✅ Отлично! Вы записаны!

{service['name']}
📅 {format_date(date)}
🕐 {time}
💰 {service['price']}₽

Жду вас в студии Nail Lux! ✨
За 24 часа до визита пришлю напоминание 🔔

📍 Адрес уточните в день визита
📞 Есть вопросы? Напишите мне!"""

    await query.edit_message_text(
        confirmation_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]
        ])
    )

    # Clear user data
    context.user_data.clear()

    return ConversationHandler.END

# ============================================================================
# CANCEL BOOKING HANDLERS
# ============================================================================

async def cancel_booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start cancel booking flow"""
    query = update.callback_query
    await query.answer()

    booking_id = int(query.data.replace("cancel_", ""))
    context.user_data['cancel_booking_id'] = booking_id

    # Get booking details
    bookings = get_user_bookings(query.from_user.id)
    booking = next((b for b in bookings if b[0] == booking_id), None)

    if not booking:
        await query.edit_message_text(
            "Запись не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return ConversationHandler.END

    _, service_id, date, time = booking
    service = SERVICES.get(service_id, {})

    confirmation_text = f"""🗑 Отменить запись?

{service.get('name', 'Неизвестная услуга')}
📅 {format_date(date)} в {time}

Вы уверены?"""

    keyboard = [
        [InlineKeyboardButton("✅ Да, отменить", callback_data="confirm_cancel")],
        [InlineKeyboardButton("❌ Нет, оставить", callback_data="my_bookings")]
    ]

    await query.edit_message_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CANCEL_CONFIRM

async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm booking cancellation"""
    query = update.callback_query
    await query.answer()

    if query.data == "my_bookings":
        await show_user_bookings(query, query.from_user.id)
        return ConversationHandler.END

    booking_id = context.user_data.get('cancel_booking_id')

    # Get booking info before cancellation for notification
    bookings = get_user_bookings(query.from_user.id)
    booking_info = next((b for b in bookings if b[0] == booking_id), None)

    # Cancel booking
    cancel_booking(booking_id)

    # Update Google Sheets
    update_booking_status_in_sheets(booking_id, 'cancelled')

    # Send notification to admin group
    if booking_info:
        _, service_id, date, time = booking_info
        service = SERVICES.get(service_id, {})
        user = query.from_user
        notification_text = f"""⚠️ <b>Запись отменена</b>

👤 {user.first_name} {'@' + user.username if user.username else ''}
💅 {service.get('name', 'N/A')}
📅 {format_date(date)} в {time}

ID записи: #{booking_id}"""

        await send_group_notification(context, notification_text)

    await query.edit_message_text(
        "✅ Запись отменена\n\nБуду рада видеть вас снова! 💅\nКогда захотите записаться — я здесь 😊",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]
        ])
    )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# RESCHEDULE BOOKING HANDLERS
# ============================================================================

async def reschedule_booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start reschedule booking flow"""
    query = update.callback_query
    await query.answer()

    booking_id = int(query.data.replace("reschedule_", ""))
    context.user_data['reschedule_booking_id'] = booking_id

    # Get booking details
    bookings = get_user_bookings(query.from_user.id)
    booking = next((b for b in bookings if b[0] == booking_id), None)

    if not booking:
        await query.edit_message_text(
            "Запись не найдена.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")]
            ])
        )
        return ConversationHandler.END

    _, service_id, date, time = booking
    context.user_data['reschedule_service_id'] = service_id

    service = SERVICES.get(service_id, {})

    await query.edit_message_text(
        f"🔄 Перенос записи\n\n{service.get('name', 'Неизвестная услуга')}\n\n📅 Выберите новую дату:",
        reply_markup=build_dates_keyboard()
    )

    return RESCHEDULE_DATE

async def reschedule_date_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection for rescheduling"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_categories":
        await show_user_bookings(query, query.from_user.id)
        return ConversationHandler.END

    date = data.replace("date_", "")
    context.user_data['reschedule_date'] = date

    service_id = context.user_data.get('reschedule_service_id')
    service = SERVICES[service_id]

    slots = get_available_time_slots(date, service['duration'])

    if not slots:
        await query.edit_message_text(
            f"К сожалению, на {format_date(date)} все места заняты 😔\n\nВыберите другую дату:",
            reply_markup=build_dates_keyboard()
        )
        return RESCHEDULE_DATE

    await query.edit_message_text(
        f"📅 {format_date(date)}\n\n🕐 Выберите новое время:",
        reply_markup=build_time_slots_keyboard(date, service_id)
    )

    return RESCHEDULE_TIME

async def reschedule_time_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection for rescheduling"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_to_dates":
        service_id = context.user_data.get('reschedule_service_id')
        service = SERVICES[service_id]
        await query.edit_message_text(
            f"🔄 Перенос записи\n\n{service['name']}\n\n📅 Выберите новую дату:",
            reply_markup=build_dates_keyboard()
        )
        return RESCHEDULE_DATE

    time = data.replace("time_", "")
    context.user_data['reschedule_time'] = time

    # Show confirmation
    service_id = context.user_data.get('reschedule_service_id')
    date = context.user_data.get('reschedule_date')
    service = SERVICES[service_id]

    confirmation_text = f"""✅ Подтвердите перенос:

{service['name']}
📅 {format_date(date)}
🕐 {time}
💰 {service['price']}₽

Перенести запись?"""

    keyboard = [
        [InlineKeyboardButton("✅ Да, перенести!", callback_data="confirm_reschedule")],
        [InlineKeyboardButton("❌ Отмена", callback_data="my_bookings")]
    ]

    await query.edit_message_text(
        confirmation_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return RESCHEDULE_CONFIRM

async def confirm_reschedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm booking rescheduling"""
    query = update.callback_query
    await query.answer()

    if query.data == "my_bookings":
        await show_user_bookings(query, query.from_user.id)
        return ConversationHandler.END

    # Cancel old booking
    old_booking_id = context.user_data.get('reschedule_booking_id')
    cancel_booking(old_booking_id)
    update_booking_status_in_sheets(old_booking_id, 'cancelled')

    # Create new booking
    user_id = query.from_user.id
    service_id = context.user_data.get('reschedule_service_id')
    date = context.user_data.get('reschedule_date')
    time = context.user_data.get('reschedule_time')

    booking_id = create_booking(user_id, service_id, date, time)
    sync_booking_to_sheets(booking_id, user_id, service_id, date, time)

    # Send confirmation
    service = SERVICES[service_id]

    confirmation_message = f"""✅ Запись перенесена!

{service['name']}
📅 {format_date(date)}
🕐 {time}
💰 {service['price']}₽

Жду вас в новое время! ✨"""

    await query.edit_message_text(
        confirmation_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]
        ])
    )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# VOICE MESSAGE HANDLER
# ============================================================================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    try:
        # Send processing message
        processing_msg = await update.message.reply_text("Слушаю вас... 🎤")

        # Download voice file
        voice_file = await update.message.voice.get_file()
        voice_path = f"voice_{update.effective_user.id}_{datetime.now().timestamp()}.ogg"
        await voice_file.download_to_drive(voice_path)

        # Transcribe with Whisper
        try:
            with open(voice_path, 'rb') as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"
                )

            transcribed_text = transcript.text

            # Delete voice file
            os.remove(voice_path)

            # Delete processing message
            await processing_msg.delete()

            # Process with AI assistant
            await process_with_ai(update, transcribed_text)

        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            await processing_msg.edit_text(
                "Извините, не смогла разобрать сообщение 😔\nПопробуйте еще раз или напишите текстом"
            )

            # Clean up voice file if exists
            if os.path.exists(voice_path):
                os.remove(voice_path)

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка 😔\nПопробуйте написать текстом"
        )

# ============================================================================
# AI ASSISTANT HANDLER
# ============================================================================

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with AI assistant"""
    await process_with_ai(update, update.message.text)

async def process_with_ai(update: Update, user_message: str):
    """Process message with Google Gemini AI"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=[])

        # Send message with system prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nКлиент: {user_message}"
        response = chat.send_message(full_prompt)

        bot_response = response.text

        await update.message.reply_text(bot_response)

        logger.info(f"AI response sent to user {update.effective_user.id}")

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка 😔\nПопробуйте написать еще раз или используйте меню",
            reply_markup=build_main_menu(update.effective_user.id)
        )

# ============================================================================
# ADMIN PANEL HANDLERS
# ============================================================================

async def admin_today_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's bookings"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔️ Доступ запрещен")
        return

    bookings = get_today_bookings()

    if not bookings:
        await query.edit_message_text(
            "📊 Записи на сегодня:\n\nНет активных записей",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_panel")]
            ])
        )
        return

    today = datetime.now(TIMEZONE).date()
    text = f"📊 Записи на {today.strftime('%d.%m.%Y')}:\n\n"
    total_revenue = 0

    for booking_id, user_id, service_id, time, first_name, username in bookings:
        service = SERVICES.get(service_id, {})
        service_name = service.get('name', 'Неизвестная услуга')
        price = service.get('price', 0)
        total_revenue += price

        username_str = f"(@{username})" if username else ""
        text += f"🕐 {time} — {first_name} {username_str}\n"
        text += f"   {service_name} — {price}₽\n\n"

    text += "━━━━━━━━━━━━━━━━\n"
    text += f"💰 Итого: {total_revenue:,}₽"

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_panel")]
        ])
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔️ Доступ запрещен")
        return

    stats = get_statistics()

    text = f"""📈 Статистика:

👥 Всего пользователей: {stats['total_users']}
📅 Активных записей: {stats['active_bookings']}
📊 Записей на сегодня: {stats['today_bookings']}"""

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_panel")]
        ])
    )

async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast flow"""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("⛔️ Доступ запрещен")
        return ConversationHandler.END

    await query.edit_message_text(
        "📢 Рассылка всем пользователям\n\nОтправьте текст сообщения для рассылки:"
    )

    return ADMIN_BROADCAST

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast message"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Доступ запрещен")
        return ConversationHandler.END

    broadcast_text = update.message.text
    user_ids = get_all_user_ids()

    sent_count = 0
    failed_count = 0

    status_msg = await update.message.reply_text(
        f"📤 Отправка... 0/{len(user_ids)}"
    )

    for i, user_id in enumerate(user_ids):
        try:
            await context.bot.send_message(user_id, broadcast_text)
            sent_count += 1
            await asyncio.sleep(0.05)  # Rate limiting

            # Update status every 10 messages
            if (i + 1) % 10 == 0:
                await status_msg.edit_text(
                    f"📤 Отправка... {i + 1}/{len(user_ids)}"
                )

        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed_count += 1

    await status_msg.edit_text(
        f"✅ Рассылка завершена!\n\nОтправлено: {sent_count}\nНе доставлено: {failed_count}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ В админ-панель", callback_data="admin_panel")]
        ])
    )

    logger.info(f"Broadcast completed: {sent_count} sent, {failed_count} failed")

    return ConversationHandler.END

# ============================================================================
# REMINDER SYSTEM
# ============================================================================

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Send reminders for tomorrow's bookings"""
    bookings = get_tomorrow_bookings()

    logger.info(f"Sending {len(bookings)} reminders")

    for booking_id, user_id, service_id, time, first_name in bookings:
        try:
            service = SERVICES.get(service_id, {})
            service_name = service.get('name', 'Неизвестная услуга')
            price = service.get('price', 0)

            reminder_text = f"""🔔 Напоминание о записи!

Привет, {first_name}! Завтра вас ждут в студии:

{service_name}
🕐 {time}
💰 {price}₽

До встречи в Nail Lux! ✨"""

            await context.bot.send_message(user_id, reminder_text)
            mark_reminder_sent(booking_id)

            logger.info(f"Reminder sent for booking {booking_id}")

        except Exception as e:
            logger.error(f"Failed to send reminder for booking {booking_id}: {e}")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the bot"""

    # Check environment variables
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set in environment variables")
        sys.exit(1)

    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set - voice messages will not work")

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set - AI assistant will not work")

    # Initialize database
    init_database()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Booking conversation handler
    booking_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_callback, pattern="^book$")
        ],
        states={
            SELECT_CATEGORY: [
                CallbackQueryHandler(category_selected, pattern="^(category_|back_to_categories)")
            ],
            SELECT_SERVICE: [
                CallbackQueryHandler(service_selected, pattern="^(service_|back_to_categories)")
            ],
            SELECT_DATE: [
                CallbackQueryHandler(date_selected, pattern="^(date_|back_to_categories|back_to_dates)")
            ],
            SELECT_TIME: [
                CallbackQueryHandler(time_selected, pattern="^(time_|back_to_dates)")
            ],
            CONFIRM_BOOKING: [
                CallbackQueryHandler(confirm_booking, pattern="^(confirm_booking|back_to_menu)")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(button_callback, pattern="^back_to_menu$")
        ],
    )

    # Cancel booking conversation handler
    cancel_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(cancel_booking_start, pattern="^cancel_")
        ],
        states={
            CANCEL_CONFIRM: [
                CallbackQueryHandler(confirm_cancel, pattern="^(confirm_cancel|my_bookings)")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(button_callback, pattern="^back_to_menu$")
        ],
    )

    # Reschedule booking conversation handler
    reschedule_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(reschedule_booking_start, pattern="^reschedule_")
        ],
        states={
            RESCHEDULE_DATE: [
                CallbackQueryHandler(reschedule_date_selected, pattern="^(date_|back_to_categories)")
            ],
            RESCHEDULE_TIME: [
                CallbackQueryHandler(reschedule_time_selected, pattern="^(time_|back_to_dates)")
            ],
            RESCHEDULE_CONFIRM: [
                CallbackQueryHandler(confirm_reschedule, pattern="^(confirm_reschedule|my_bookings)")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(button_callback, pattern="^back_to_menu$")
        ],
    )

    # Admin broadcast conversation handler
    broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$")
        ],
        states={
            ADMIN_BROADCAST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(button_callback, pattern="^admin_panel$")
        ],
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(booking_conv)
    application.add_handler(cancel_conv)
    application.add_handler(reschedule_conv)
    application.add_handler(broadcast_conv)

    # Admin handlers
    application.add_handler(CallbackQueryHandler(admin_today_bookings, pattern="^admin_today$"))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))

    # General callback handlers
    application.add_handler(CallbackQueryHandler(button_callback))

    # Voice and text message handlers
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Schedule daily reminders at 18:00 Moscow time
    application.job_queue.run_daily(
        send_reminders,
        time=REMINDER_TIME,
        days=(0, 1, 2, 3, 4, 5, 6)
    )

    # Start bot
    logger.info("Bot started successfully")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nail Lux Studio - Admin Telegram Bot
Separate admin interface for salon management
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

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

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
ADMIN_BOT_TOKEN = os.getenv('ADMIN_BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
NOTIFICATION_GROUP_ID = os.getenv('NOTIFICATION_GROUP_ID', '')  # Optional

# Timezone
TIMEZONE = pytz.timezone('Europe/Moscow')

# Database
DB_PATH = 'salon_bot.db'

# Import services from main bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from bot import SERVICES
except ImportError:
    SERVICES = {}
    logger.warning("Could not import SERVICES from bot.py")

# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def get_today_bookings() -> List[Tuple]:
    """Get all bookings for today"""
    today = datetime.now(TIMEZONE).date().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.id, b.user_id, b.service_id, b.time, b.status,
               u.first_name, u.username, u.phone
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.date = ?
        ORDER BY b.time
    ''', (today,))

    bookings = cursor.fetchall()
    conn.close()
    return bookings

def get_week_bookings() -> List[Tuple]:
    """Get all bookings for this week"""
    today = datetime.now(TIMEZONE).date()
    week_end = today + timedelta(days=7)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.id, b.user_id, b.service_id, b.date, b.time, b.status,
               u.first_name, u.username
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.date BETWEEN ? AND ? AND b.status = 'active'
        ORDER BY b.date, b.time
    ''', (today.isoformat(), week_end.isoformat()))

    bookings = cursor.fetchall()
    conn.close()
    return bookings

def get_month_bookings() -> List[Tuple]:
    """Get all bookings for this month"""
    today = datetime.now(TIMEZONE).date()
    month_start = today.replace(day=1)
    next_month = month_start + timedelta(days=32)
    month_end = next_month.replace(day=1) - timedelta(days=1)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.id, b.user_id, b.service_id, b.date, b.time, b.status,
               u.first_name, u.username
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.date BETWEEN ? AND ?
        ORDER BY b.date, b.time
    ''', (month_start.isoformat(), month_end.isoformat()))

    bookings = cursor.fetchall()
    conn.close()
    return bookings

def get_all_clients() -> List[Tuple]:
    """Get all registered clients"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.user_id, u.first_name, u.username, u.phone, u.created_at,
               COUNT(b.id) as total_bookings
        FROM users u
        LEFT JOIN bookings b ON u.user_id = b.user_id
        GROUP BY u.user_id
        ORDER BY total_bookings DESC
    ''')

    clients = cursor.fetchall()
    conn.close()
    return clients

def get_revenue_stats(period: str = 'today') -> Dict:
    """Get revenue statistics for period"""
    today = datetime.now(TIMEZONE).date()

    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today
        end_date = today + timedelta(days=7)
    elif period == 'month':
        start_date = today.replace(day=1)
        next_month = start_date + timedelta(days=32)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    else:
        start_date = today
        end_date = today

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) as total_bookings,
               COUNT(CASE WHEN status = 'active' THEN 1 END) as active_bookings,
               COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_bookings
        FROM bookings
        WHERE date BETWEEN ? AND ?
    ''', (start_date.isoformat(), end_date.isoformat()))

    stats = cursor.fetchone()

    # Calculate revenue
    cursor.execute('''
        SELECT service_id FROM bookings
        WHERE date BETWEEN ? AND ? AND status = 'active'
    ''', (start_date.isoformat(), end_date.isoformat()))

    service_ids = cursor.fetchall()
    total_revenue = sum(SERVICES.get(sid[0], {}).get('price', 0) for sid in service_ids)

    conn.close()

    return {
        'total_bookings': stats[0],
        'active_bookings': stats[1],
        'cancelled_bookings': stats[2],
        'total_revenue': total_revenue
    }

def get_popular_services() -> List[Tuple]:
    """Get most popular services"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT service_id, COUNT(*) as count
        FROM bookings
        WHERE status = 'active'
        GROUP BY service_id
        ORDER BY count DESC
        LIMIT 5
    ''')

    services = cursor.fetchall()
    conn.close()
    return services

# ============================================================================
# NOTIFICATION FUNCTIONS
# ============================================================================

async def send_group_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send notification to admin group"""
    if not NOTIFICATION_GROUP_ID:
        return

    try:
        await context.bot.send_message(
            chat_id=NOTIFICATION_GROUP_ID,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send group notification: {e}")

# ============================================================================
# KEYBOARD BUILDERS
# ============================================================================

def build_main_menu() -> InlineKeyboardMarkup:
    """Build admin main menu"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Сегодня", callback_data="admin_today"),
            InlineKeyboardButton("📅 Неделя", callback_data="admin_week")
        ],
        [
            InlineKeyboardButton("📈 Месяц", callback_data="admin_month"),
            InlineKeyboardButton("💰 Финансы", callback_data="admin_finance")
        ],
        [
            InlineKeyboardButton("👥 Клиенты", callback_data="admin_clients"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("🌐 Web-панель", web_app=WebAppInfo(url="http://localhost:5000"))
        ]
    ]

    return InlineKeyboardMarkup(keyboard)

def build_period_menu() -> InlineKeyboardMarkup:
    """Build period selection menu"""
    keyboard = [
        [
            InlineKeyboardButton("Сегодня", callback_data="period_today"),
            InlineKeyboardButton("Неделя", callback_data="period_week")
        ],
        [
            InlineKeyboardButton("Месяц", callback_data="period_month"),
            InlineKeyboardButton("Весь период", callback_data="period_all")
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    # Check if user is admin
    if user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "⛔️ Доступ запрещен.\n\nЭтот бот только для администраторов."
        )
        logger.warning(f"Unauthorized access attempt by user {user.id} ({user.username})")
        return

    welcome_message = f"""👑 <b>Админ-панель Nail Lux</b>

Добро пожаловать, {user.first_name}!

Это расширенная панель управления салоном.
Выберите раздел для работы:"""

    await update.message.reply_text(
        welcome_message,
        reply_markup=build_main_menu(),
        parse_mode='HTML'
    )

    logger.info(f"Admin {user.id} ({user.username}) started admin bot")

# ============================================================================
# CALLBACK HANDLERS
# ============================================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Check admin permissions
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("⛔️ Доступ запрещен")
        return

    data = query.data

    # Main menu
    if data == "back_main":
        await query.edit_message_text(
            "👑 <b>Админ-панель Nail Lux</b>\n\nВыберите раздел:",
            reply_markup=build_main_menu(),
            parse_mode='HTML'
        )
        return

    # Today's bookings
    elif data == "admin_today":
        await show_today_bookings(query)
        return

    # Week bookings
    elif data == "admin_week":
        await show_week_bookings(query)
        return

    # Month bookings
    elif data == "admin_month":
        await show_month_bookings(query)
        return

    # Finance stats
    elif data == "admin_finance":
        await show_finance_stats(query)
        return

    # Clients database
    elif data == "admin_clients":
        await show_clients(query)
        return

    # Statistics
    elif data == "admin_stats":
        await show_statistics(query)
        return

    # Settings
    elif data == "admin_settings":
        await show_settings(query)
        return

# ============================================================================
# VIEW HANDLERS
# ============================================================================

async def show_today_bookings(query):
    """Show today's bookings"""
    bookings = get_today_bookings()
    today = datetime.now(TIMEZONE).date()

    if not bookings:
        await query.edit_message_text(
            f"📊 <b>Записи на {today.strftime('%d.%m.%Y')}</b>\n\n"
            "Нет записей на сегодня",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
            ]),
            parse_mode='HTML'
        )
        return

    text = f"📊 <b>Записи на {today.strftime('%d.%m.%Y')}</b>\n\n"
    total_revenue = 0
    active_count = 0
    cancelled_count = 0

    for booking_id, user_id, service_id, time, status, first_name, username, phone in bookings:
        service = SERVICES.get(service_id, {})
        service_name = service.get('name', 'Неизвестная услуга')
        price = service.get('price', 0)

        if status == 'active':
            total_revenue += price
            active_count += 1
            status_icon = "✅"
        else:
            cancelled_count += 1
            status_icon = "❌"

        username_str = f"@{username}" if username else ""
        phone_str = f"📱 {phone}" if phone else ""

        text += f"{status_icon} <b>{time}</b> — {first_name} {username_str}\n"
        text += f"   {service_name}\n"
        text += f"   💰 {price:,}₽"
        if phone_str:
            text += f" | {phone_str}"
        text += f"\n\n"

    text += "━━━━━━━━━━━━━━━━\n"
    text += f"📌 Всего: {len(bookings)} | ✅ Активных: {active_count} | ❌ Отменено: {cancelled_count}\n"
    text += f"💰 <b>Итого: {total_revenue:,}₽</b>"

    keyboard = [
        [
            InlineKeyboardButton("📤 Экспорт", callback_data="export_today"),
            InlineKeyboardButton("🔄 Обновить", callback_data="admin_today")
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_week_bookings(query):
    """Show week bookings"""
    bookings = get_week_bookings()

    if not bookings:
        await query.edit_message_text(
            "📅 <b>Записи на неделю</b>\n\nНет записей",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
            ]),
            parse_mode='HTML'
        )
        return

    text = "📅 <b>Записи на неделю</b>\n\n"
    total_revenue = 0

    # Group by date
    by_date = {}
    for booking in bookings:
        date = booking[3]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(booking)

    for date_str, day_bookings in sorted(by_date.items()):
        date = datetime.fromisoformat(date_str)
        weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        weekday = weekdays[date.weekday()]

        text += f"<b>{date.strftime('%d.%m')} ({weekday})</b> — {len(day_bookings)} записей\n"

        for booking in day_bookings:
            service_id = booking[2]
            time = booking[4]
            first_name = booking[6]

            service = SERVICES.get(service_id, {})
            price = service.get('price', 0)
            total_revenue += price

            text += f"  • {time} — {first_name} ({price:,}₽)\n"

        text += "\n"

    text += "━━━━━━━━━━━━━━━━\n"
    text += f"📊 Всего записей: {len(bookings)}\n"
    text += f"💰 <b>Итого: {total_revenue:,}₽</b>"

    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_month_bookings(query):
    """Show month bookings summary"""
    bookings = get_month_bookings()
    stats = get_revenue_stats('month')

    today = datetime.now(TIMEZONE).date()
    month_name = today.strftime('%B %Y')

    text = f"📈 <b>Статистика за {month_name}</b>\n\n"
    text += f"📊 Всего записей: {stats['total_bookings']}\n"
    text += f"✅ Активных: {stats['active_bookings']}\n"
    text += f"❌ Отменено: {stats['cancelled_bookings']}\n"
    text += f"💰 <b>Выручка: {stats['total_revenue']:,}₽</b>\n\n"

    # Popular services
    popular = get_popular_services()
    if popular:
        text += "🔥 <b>Популярные услуги:</b>\n"
        for service_id, count in popular:
            service = SERVICES.get(service_id, {})
            name = service.get('name', 'Неизвестная услуга')
            text += f"  {count}× {name}\n"

    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_finance_stats(query):
    """Show financial statistics"""
    today_stats = get_revenue_stats('today')
    week_stats = get_revenue_stats('week')
    month_stats = get_revenue_stats('month')

    text = "💰 <b>Финансовая статистика</b>\n\n"

    text += "📊 <b>Сегодня:</b>\n"
    text += f"  Записей: {today_stats['active_bookings']}\n"
    text += f"  Выручка: <b>{today_stats['total_revenue']:,}₽</b>\n\n"

    text += "📅 <b>Эта неделя:</b>\n"
    text += f"  Записей: {week_stats['active_bookings']}\n"
    text += f"  Выручка: <b>{week_stats['total_revenue']:,}₽</b>\n\n"

    text += "📈 <b>Этот месяц:</b>\n"
    text += f"  Записей: {month_stats['active_bookings']}\n"
    text += f"  Выручка: <b>{month_stats['total_revenue']:,}₽</b>\n\n"

    # Average check
    if month_stats['active_bookings'] > 0:
        avg_check = month_stats['total_revenue'] / month_stats['active_bookings']
        text += f"💳 <b>Средний чек:</b> {avg_check:,.0f}₽"

    keyboard = [
        [
            InlineKeyboardButton("📤 Экспорт отчета", callback_data="export_finance"),
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_clients(query):
    """Show clients database"""
    clients = get_all_clients()

    if not clients:
        await query.edit_message_text(
            "👥 <b>База клиентов</b>\n\nНет зарегистрированных клиентов",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
            ]),
            parse_mode='HTML'
        )
        return

    text = f"👥 <b>База клиентов</b>\n\n"
    text += f"Всего клиентов: <b>{len(clients)}</b>\n\n"

    # Show top 10 clients
    text += "🔝 <b>Топ-10 клиентов:</b>\n\n"

    for i, (user_id, first_name, username, phone, created_at, total_bookings) in enumerate(clients[:10], 1):
        username_str = f"@{username}" if username else ""
        phone_str = f"📱 {phone}" if phone else ""

        text += f"{i}. {first_name} {username_str}\n"
        text += f"   📊 Визитов: {total_bookings}"
        if phone_str:
            text += f" | {phone_str}"
        text += "\n\n"

    keyboard = [
        [
            InlineKeyboardButton("📤 Экспорт всех", callback_data="export_clients"),
            InlineKeyboardButton("🔍 Поиск", callback_data="search_client")
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_statistics(query):
    """Show general statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    # Total bookings
    cursor.execute('SELECT COUNT(*) FROM bookings')
    total_bookings = cursor.fetchone()[0]

    # Active bookings
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE status = "active"')
    active_bookings = cursor.fetchone()[0]

    # Today's bookings
    today = datetime.now(TIMEZONE).date().isoformat()
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE date = ? AND status = "active"', (today,))
    today_bookings = cursor.fetchone()[0]

    conn.close()

    text = "📊 <b>Общая статистика</b>\n\n"
    text += f"👥 Всего пользователей: <b>{total_users}</b>\n"
    text += f"📅 Всего записей: <b>{total_bookings}</b>\n"
    text += f"✅ Активных записей: <b>{active_bookings}</b>\n"
    text += f"📊 Записей на сегодня: <b>{today_bookings}</b>\n\n"

    # Popular services
    popular = get_popular_services()
    if popular:
        text += "🔥 <b>Популярные услуги:</b>\n"
        for service_id, count in popular:
            service = SERVICES.get(service_id, {})
            name = service.get('name', 'Неизвестная услуга')
            text += f"  {count}× {name}\n"

    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_settings(query):
    """Show settings menu"""
    text = "⚙️ <b>Настройки</b>\n\n"
    text += "Здесь можно настроить:\n"
    text += "• Рабочие часы\n"
    text += "• Услуги и цены\n"
    text += "• Уведомления\n"
    text += "• Интеграции\n\n"
    text += "<i>Функционал в разработке</i>"

    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_main")]
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the admin bot"""

    # Check environment variables
    if not ADMIN_BOT_TOKEN:
        logger.error("ADMIN_BOT_TOKEN not set in environment variables")
        print("\n⚠️  ОШИБКА: Не указан ADMIN_BOT_TOKEN в .env файле")
        print("\nДобавьте в .env:")
        print("ADMIN_BOT_TOKEN=your_admin_bot_token_here")
        print("\nПолучить токен: @BotFather -> /newbot")
        sys.exit(1)

    if not ADMIN_IDS:
        logger.error("ADMIN_IDS not set in environment variables")
        sys.exit(1)

    # Create application
    application = Application.builder().token(ADMIN_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start bot
    logger.info("Admin bot started successfully")
    print("\n✅ Админ-бот запущен!")
    print(f"👑 Администраторы: {', '.join(map(str, ADMIN_IDS))}")
    if NOTIFICATION_GROUP_ID:
        print(f"📢 Группа уведомлений: {NOTIFICATION_GROUP_ID}")
    print("\nБот работает... (Ctrl+C для остановки)\n")

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nail Lux Studio - Web Admin Panel
Flask-based web interface for salon management
"""

import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Configuration
DB_PATH = 'salon_bot.db'
TIMEZONE = pytz.timezone('Europe/Moscow')
SECRET_KEY = os.getenv('WEB_ADMIN_SECRET_KEY', 'change-this-secret-key-in-production')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Change in production!

# Import services
try:
    from bot import SERVICES
except ImportError:
    SERVICES = {}

# Create Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# AUTH DECORATOR
# ============================================================================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# ROUTES - AUTH
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Успешный вход!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный пароль', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('logged_in', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

# ============================================================================
# ROUTES - MAIN
# ============================================================================

@app.route('/')
@login_required
def dashboard():
    """Main dashboard"""
    conn = get_db()
    cursor = conn.cursor()

    # Today's stats
    today = datetime.now(TIMEZONE).date().isoformat()

    cursor.execute('''
        SELECT COUNT(*) FROM bookings
        WHERE date = ? AND status = 'active'
    ''', (today,))
    today_bookings = cursor.fetchone()[0]

    # Calculate today's revenue
    cursor.execute('''
        SELECT service_id FROM bookings
        WHERE date = ? AND status = 'active'
    ''', (today,))
    services = cursor.fetchall()
    today_revenue = sum(SERVICES.get(s[0], {}).get('price', 0) for s in services)

    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    # Active bookings
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE status = "active"')
    active_bookings = cursor.fetchone()[0]

    # Recent bookings (last 10)
    cursor.execute('''
        SELECT b.id, b.date, b.time, b.service_id, b.status,
               u.first_name, u.username
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        ORDER BY b.created_at DESC
        LIMIT 10
    ''')
    recent_bookings = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           today_bookings=today_bookings,
                           today_revenue=today_revenue,
                           total_users=total_users,
                           active_bookings=active_bookings,
                           recent_bookings=recent_bookings,
                           services=SERVICES)

@app.route('/bookings')
@login_required
def bookings():
    """Bookings page"""
    # Get filter parameters
    date_filter = request.args.get('date', '')
    status_filter = request.args.get('status', 'all')

    conn = get_db()
    cursor = conn.cursor()

    # Build query
    query = '''
        SELECT b.id, b.date, b.time, b.service_id, b.status, b.created_at,
               u.first_name, u.username, u.phone
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE 1=1
    '''
    params = []

    if date_filter:
        query += ' AND b.date = ?'
        params.append(date_filter)

    if status_filter != 'all':
        query += ' AND b.status = ?'
        params.append(status_filter)

    query += ' ORDER BY b.date DESC, b.time DESC'

    cursor.execute(query, params)
    all_bookings = cursor.fetchall()

    conn.close()

    return render_template('bookings.html',
                           bookings=all_bookings,
                           services=SERVICES,
                           date_filter=date_filter,
                           status_filter=status_filter)

@app.route('/clients')
@login_required
def clients():
    """Clients page"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.user_id, u.first_name, u.username, u.phone, u.created_at,
               COUNT(b.id) as total_bookings,
               MAX(b.date) as last_visit
        FROM users u
        LEFT JOIN bookings b ON u.user_id = b.user_id
        GROUP BY u.user_id
        ORDER BY total_bookings DESC
    ''')

    all_clients = cursor.fetchall()
    conn.close()

    return render_template('clients.html', clients=all_clients)

@app.route('/statistics')
@login_required
def statistics():
    """Statistics page"""
    conn = get_db()
    cursor = conn.cursor()

    # Monthly revenue for chart
    cursor.execute('''
        SELECT date, service_id FROM bookings
        WHERE status = 'active' AND date >= date('now', '-6 months')
        ORDER BY date
    ''')

    bookings_data = cursor.fetchall()

    # Group by month
    monthly_revenue = {}
    for booking in bookings_data:
        date = datetime.fromisoformat(booking[0])
        month_key = date.strftime('%Y-%m')
        service_id = booking[1]
        price = SERVICES.get(service_id, {}).get('price', 0)

        if month_key not in monthly_revenue:
            monthly_revenue[month_key] = 0
        monthly_revenue[month_key] += price

    # Service popularity
    cursor.execute('''
        SELECT service_id, COUNT(*) as count
        FROM bookings
        WHERE status = 'active'
        GROUP BY service_id
        ORDER BY count DESC
    ''')

    service_stats = cursor.fetchall()

    conn.close()

    return render_template('statistics.html',
                           monthly_revenue=monthly_revenue,
                           service_stats=service_stats,
                           services=SERVICES)

@app.route('/services')
@login_required
def services_page():
    """Services management page"""
    return render_template('services.html', services=SERVICES)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel booking via API"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE bookings SET status = 'cancelled'
        WHERE id = ?
    ''', (booking_id,))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Booking cancelled'})

@app.route('/api/stats/today')
@login_required
def api_today_stats():
    """Get today's stats via API"""
    conn = get_db()
    cursor = conn.cursor()

    today = datetime.now(TIMEZONE).date().isoformat()

    cursor.execute('''
        SELECT COUNT(*), service_id FROM bookings
        WHERE date = ? AND status = 'active'
        GROUP BY service_id
    ''', (today,))

    bookings = cursor.fetchall()
    total_count = sum(b[0] for b in bookings)
    total_revenue = sum(b[0] * SERVICES.get(b[1], {}).get('price', 0) for b in bookings)

    conn.close()

    return jsonify({
        'total_bookings': total_count,
        'total_revenue': total_revenue
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌐 Nail Lux - Web Admin Panel")
    print("="*50)
    print(f"\n🔐 Login: {ADMIN_PASSWORD}")
    print("📍 URL: http://localhost:5000")
    print("\n⚠️  ВАЖНО: Смените пароль в .env файле!")
    print("   ADMIN_PASSWORD=your_secure_password")
    print("\n" + "="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)

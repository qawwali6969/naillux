# Админ-Панель Nail Lux - Инструкция по Настройке

Полное руководство по настройке расширенной системы управления салоном.

---

## 📋 Что Входит в Админ-Систему

1. **Отдельный Админ-Бот** (@naillux_admin_bot) - Telegram бот только для администраторов
2. **Web-Панель** (http://localhost:5000) - Веб-интерфейс с дашбордом и графиками
3. **Группа Уведомлений** - Автоматические алерты о всех событиях
4. **Интеграция** - Все работает с одной базой данных

---

## 🚀 Быстрый Старт (30 минут)

### Шаг 1: Создать Админ-Бота

1. Откройте Telegram, найдите **@BotFather**
2. Отправьте `/newbot`
3. Название: `Nail Lux Admin`
4. Username: `naillux_admin_bot` (или любой доступный)
5. **Скопируйте токен** - это ваш `ADMIN_BOT_TOKEN`

### Шаг 2: Создать Группу для Уведомлений (опционально)

1. Создайте приватную группу: "Nail Lux - Уведомления"
2. Добавьте **оба бота** в группу:
   - Основной бот (@naillux_bot)
   - Админ-бот (@naillux_admin_bot)
3. Сделайте ботов администраторами группы

#### Как получить ID группы:

**Вариант A (простой):**
1. Добавьте в группу бота @userinfobot
2. ID группы будет в формате `-1001234567890`

**Вариант B (через основной бот):**
1. Добавьте ваш основной бот в группу
2. Отправьте любое сообщение в группу
3. Откройте https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
4. Найдите `"chat":{"id":-1001234567890}`

### Шаг 3: Обновить .env Файл

Откройте `/opt/salon-bot/.env` и добавьте:

```env
# Токен админ-бота
ADMIN_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# ID группы для уведомлений (необязательно)
NOTIFICATION_GROUP_ID=-1001234567890

# Пароль для веб-панели
ADMIN_PASSWORD=ваш_надёжный_пароль

# Секретный ключ для Flask (любая случайная строка)
WEB_ADMIN_SECRET_KEY=случайная_строка_минимум_32_символа
```

**Полный пример .env:**
```env
BOT_TOKEN=123456:ABC-основной-бот-токен
ADMIN_BOT_TOKEN=789012:DEF-админ-бот-токен
ADMIN_IDS=123456789,987654321
NOTIFICATION_GROUP_ID=-1001234567890
OPENAI_API_KEY=sk-ваш-ключ
GEMINI_API_KEY=ваш-ключ
ADMIN_PASSWORD=SuperSecurePassword123!
WEB_ADMIN_SECRET_KEY=random-secret-key-change-in-production-32chars
```

### Шаг 4: Установить Flask

```bash
cd /opt/salon-bot
source venv/bin/activate
pip install flask==3.0.0
```

### Шаг 5: Запустить Админ-Бота

```bash
cd /opt/salon-bot
source venv/bin/activate
python admin_bot.py
```

**Проверка:** Откройте Telegram, найдите ваш админ-бот, отправьте `/start`

### Шаг 6: Запустить Web-Панель (опционально)

В **отдельном терминале**:

```bash
cd /opt/salon-bot
source venv/bin/activate
python web_admin.py
```

Откройте браузер: http://localhost:5000

**Логин:** Пароль из `ADMIN_PASSWORD` в .env

---

## 🔧 Production Deployment (systemd)

### Настроить Автозапуск Админ-Бота

#### 1. Создать service файл для админ-бота:

```bash
sudo nano /etc/systemd/system/salon-admin-bot.service
```

Вставить:
```ini
[Unit]
Description=Nail Lux Admin Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/salon-bot
Environment="PATH=/opt/salon-bot/venv/bin"
ExecStart=/opt/salon-bot/venv/bin/python3 /opt/salon-bot/admin_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Активировать:

```bash
sudo systemctl daemon-reload
sudo systemctl enable salon-admin-bot
sudo systemctl start salon-admin-bot
```

#### 3. Проверить:

```bash
sudo systemctl status salon-admin-bot
journalctl -u salon-admin-bot -f
```

### Настроить Автозапуск Web-Панели

#### 1. Создать service файл:

```bash
sudo nano /etc/systemd/system/salon-web-admin.service
```

Вставить:
```ini
[Unit]
Description=Nail Lux Web Admin Panel
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/salon-bot
Environment="PATH=/opt/salon-bot/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/opt/salon-bot/venv/bin/python3 /opt/salon-bot/web_admin.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Активировать:

```bash
sudo systemctl daemon-reload
sudo systemctl enable salon-web-admin
sudo systemctl start salon-web-admin
```

---

## 📱 Функционал Админ-Бота

### Главное Меню

```
👑 Админ-панель Nail Lux

├── 📊 Сегодня - записи на сегодня с выручкой
├── 📅 Неделя - все записи на неделю
├── 📈 Месяц - статистика за месяц
├── 💰 Финансы - выручка по периодам
├── 👥 Клиенты - база клиентов (топ-10)
├── 📊 Статистика - общая статистика
├── 📢 Рассылка - отправка сообщений
└── ⚙️ Настройки - конфигурация
```

### Примеры Экранов

**Сегодняшние записи:**
```
📊 Записи на 26.10.2025

✅ 10:00 — Анна @anna
   💅 Маникюр с гель-лаком
   💰 3,900₽ | 📱 +7 999 123-45-67

✅ 14:00 — Мария @maria
   👣 Педикюр Golden Trace
   💰 4,100₽

━━━━━━━━━━━━━━━━
📌 Всего: 5 | ✅ Активных: 5 | ❌ Отменено: 0
💰 Итого: 19,500₽
```

**Финансы:**
```
💰 Финансовая статистика

📊 Сегодня:
  Записей: 5
  Выручка: 19,500₽

📅 Эта неделя:
  Записей: 23
  Выручка: 94,000₽

📈 Этот месяц:
  Записей: 87
  Выручка: 356,000₽

💳 Средний чек: 4,092₽
```

---

## 🌐 Web-Панель

### Доступные Страницы

#### 1. Дашборд (/)
- 4 карточки с метриками
- Последние 10 записей
- Быстрый доступ ко всем разделам

#### 2. Записи (/bookings)
- Таблица всех записей
- Фильтры: дата, статус
- Кнопка отмены записи
- Экспорт в Excel (планируется)

#### 3. Клиенты (/clients)
- База всех клиентов
- Количество визитов
- Последний визит
- Контактная информация

#### 4. Статистика (/statistics)
- График выручки по месяцам
- Популярные услуги
- Аналитика

#### 5. Услуги (/services)
- Каталог всех услуг
- Цены и длительность
- Редактирование (планируется)

### Как Открыть Web-Панель из Интернета

#### Вариант 1: Nginx Reverse Proxy

```bash
sudo apt install nginx

sudo nano /etc/nginx/sites-available/nail-lux-admin
```

Вставить:
```nginx
server {
    listen 80;
    server_name admin.naillux.ru;  # Ваш домен

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Basic Auth для дополнительной защиты
    auth_basic "Admin Area";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

Создать пароль:
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

Активировать:
```bash
sudo ln -s /etc/nginx/sites-available/nail-lux-admin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Вариант 2: SSH Tunnel (для разработки)

На своём компьютере:
```bash
ssh -L 5000:localhost:5000 root@your-server-ip
```

Теперь http://localhost:5000 на вашем компьютере покажет админку с сервера.

---

## 🔔 Уведомления в Группу

### Какие События Отправляются

#### 1. Новая Запись
```
🎉 Новая запись!

👤 Анна @anna
💅 Маникюр с гель-лаком
📅 15 марта в 16:00
💰 3,900₽

ID записи: #42
```

#### 2. Отмена Записи
```
⚠️ Запись отменена

👤 Мария @maria
💅 Педикюр Golden Trace
📅 16 марта в 14:00

ID записи: #43
```

### Настройка Уведомлений

Уведомления отправляются автоматически если:
1. Указан `NOTIFICATION_GROUP_ID` в .env
2. Бот добавлен в группу как администратор
3. Группа приватная

**Для отключения:** Просто удалите `NOTIFICATION_GROUP_ID` из .env

---

## 🎯 Telegram Web App (Mini App)

В админ-боте есть кнопка "🌐 Web-панель" которая открывает встроенное мини-приложение.

### Настройка Web App

1. Убедитесь что web_admin.py запущен
2. Измените URL в admin_bot.py (строка 214):

```python
InlineKeyboardButton("🌐 Web-панель", web_app=WebAppInfo(url="https://admin.naillux.ru"))
```

3. URL должен быть HTTPS (не HTTP)
4. Настройте Nginx с SSL сертификатом

### Получить SSL Сертификат (бесплатно)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d admin.naillux.ru
```

Автопродление:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 🔒 Безопасность

### Обязательно:

1. **Смените пароль админки:**
```env
ADMIN_PASSWORD=ваш_сложный_пароль_не_admin123
```

2. **Генерируйте случайный SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Используйте результат:
```env
WEB_ADMIN_SECRET_KEY=полученная_случайная_строка
```

3. **Firewall:**
```bash
sudo ufw allow 22   # SSH
sudo ufw allow 80   # HTTP
sudo ufw allow 443  # HTTPS
sudo ufw enable
```

4. **Ограничьте доступ к web-панели:**
   - Используйте Nginx Basic Auth
   - Или VPN
   - Или IP whitelist

### Nginx IP Whitelist

```nginx
location / {
    # Разрешить только с этих IP
    allow 192.168.1.100;
    allow 10.0.0.0/24;
    deny all;

    proxy_pass http://127.0.0.1:5000;
}
```

---

## 📊 Мониторинг

### Проверка Статуса Всех Сервисов

```bash
# Основной бот
sudo systemctl status salon-bot

# Админ-бот
sudo systemctl status salon-admin-bot

# Web-панель
sudo systemctl status salon-web-admin
```

### Логи

```bash
# Основной бот
journalctl -u salon-bot -f

# Админ-бот
journalctl -u salon-admin-bot -f

# Web-панель
journalctl -u salon-web-admin -f

# Все вместе
journalctl -u salon-bot -u salon-admin-bot -u salon-web-admin -f
```

### Restart Всех Сервисов

```bash
sudo systemctl restart salon-bot salon-admin-bot salon-web-admin
```

---

## 🐛 Troubleshooting

### Админ-бот не запускается

**Проверьте:**
```bash
cd /opt/salon-bot
source venv/bin/activate
python admin_bot.py
```

**Ошибка:** `ADMIN_BOT_TOKEN not set`
- Добавьте токен в .env файл

**Ошибка:** `Could not import SERVICES from bot.py`
- Убедитесь что bot.py в той же папке

### Web-панель недоступна

**Проверьте что запущена:**
```bash
curl http://localhost:5000
```

Если ошибка:
```bash
cd /opt/salon-bot
source venv/bin/activate
python web_admin.py
```

### Уведомления не приходят в группу

1. Проверьте `NOTIFICATION_GROUP_ID` в .env
2. Убедитесь что бот администратор группы
3. Отправьте тестовое сообщение:

```python
# test_notification.py
import asyncio
from telegram import Bot

async def test():
    bot = Bot(token="ваш_бот_токен")
    await bot.send_message(
        chat_id="ваш_group_id",
        text="Тест"
    )

asyncio.run(test())
```

---

## 📈 Что Дальше

### Планируемые Фичи

- [ ] Экспорт отчетов в Excel
- [ ] Редактирование услуг через web
- [ ] Управление расписанием
- [ ] Push-уведомления в браузере
- [ ] Telegram Mini App (полная интеграция)
- [ ] Графики в реальном времени
- [ ] Мобильная версия web-панели
- [ ] API для интеграций

---

## 💡 Полезные Команды

```bash
# Рестарт всех сервисов
sudo systemctl restart salon-bot salon-admin-bot salon-web-admin

# Логи всех сервисов
journalctl -u salon-bot -u salon-admin-bot -u salon-web-admin -f

# Проверка статуса
sudo systemctl status salon-bot salon-admin-bot salon-web-admin

# Остановить всё
sudo systemctl stop salon-bot salon-admin-bot salon-web-admin

# Запустить всё
sudo systemctl start salon-bot salon-admin-bot salon-web-admin
```

---

## ✅ Чеклист Настройки

- [ ] Создан админ-бот через @BotFather
- [ ] Получен `ADMIN_BOT_TOKEN`
- [ ] Создана приватная группа
- [ ] Боты добавлены в группу как админы
- [ ] Получен `NOTIFICATION_GROUP_ID`
- [ ] Обновлен .env файл
- [ ] Установлен Flask
- [ ] Админ-бот запускается
- [ ] Web-панель открывается
- [ ] Уведомления приходят в группу
- [ ] Настроен systemd для автозапуска
- [ ] Изменен пароль админки
- [ ] Настроен Nginx (опционально)
- [ ] Получен SSL сертификат (опционально)

---

**Готово!** 🎉

Теперь у вас полноценная система управления салоном с тремя интерфейсами:
1. Telegram Админ-Бот
2. Web-Панель
3. Группа Уведомлений

Если что-то не работает - смотрите раздел Troubleshooting или логи сервисов.

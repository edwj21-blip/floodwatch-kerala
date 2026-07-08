# 🌊 FloodWatch Kerala — v8 (Bug-Fixed & Updated)

Kerala State Disaster Management Authority — Flood Early Warning & Community Reporting Portal.

---

## 🐛 Bugs Fixed in v8

| # | Severity | Bug | Fix Applied |
|---|----------|-----|-------------|
| 1 | 🔴 Critical | `admin_reports.html` — Missing `{% for report in reports %}` loop; only one report ever rendered | Added the for loop wrapper around the report card HTML |
| 2 | 🔴 Critical | `settings.py` — `LOGIN_URL = '/portal/'` sent unauthenticated users to the landing page instead of login form | Changed to `LOGIN_URL = '/login/'` |
| 3 | 🔴 Critical | `views.py` — `flood_map_view` was missing `@login_required`, accessible without authentication | Added `@login_required` decorator |
| 4 | 🟠 Feature | `fw-sw.js` — Poll interval was `300000` (5 min) but feature spec says 25 min; contradictory comment | Set to `1500000` (25 minutes) matching the popup throttle |
| 5 | 🟠 Feature | `static/core/img/` — Notification icons `fw-icon-192.png` and `fw-badge-72.png` missing; desktop push notifications showed broken icon | Created both icon files |
| 6 | 🟠 Feature | `views.py` — PDF download had no password gate (only staff check); feature required admin password prompt | Added password form (`pdf_password.html`) + `ADMIN_PDF_PASSWORD` setting |
| 7 | 🟠 Feature | `views.py` — `@user_passes_test` on WhatsApp/email/PDF views redirected to `/portal/` not `/login/` | Added `login_url='/login/'` to all three decorators |
| 8 | 🟡 Minor | `views.py` — `api_district_status` used `max(..., default=0)` with redundant `or [0]` fallback | Cleaned up to `max(list(...) or [0])` |
| 9 | 🟡 Minor | `requirements.txt` — `Pillow` was missing (required for ImageField photo uploads) | Confirmed Pillow entry with explanatory comment |
| 10 | 🟡 Minor | `static/core/img/` — Entire img folder missing from zip | Created folder + icon files |

---

## ✅ All Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Alert popup throttled to every 25 minutes | ✅ Fixed (was 5 min) |
| 2 | Offline SVG Kerala map (14 districts) | ✅ |
| 3 | Animated water level waves in popup | ✅ |
| 4 | Admin SVG map with pulsing critical districts | ✅ |
| 5 | Auto email alerts to all registered users | ✅ |
| 6 | WhatsApp one-click broadcast (admin) | ✅ |
| 7 | Admin PDF per district (password protected) | ✅ Fixed |
| 8 | Desktop PC push notification | ✅ Fixed (icons added) |
| 9 | Click notification → opens alerts page | ✅ |
| 10 | WhatsApp share inside alert popup | ✅ |

---

## 🚀 Quick Start

```bash
cd FloodWatch_v8_Fixed
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Visit: http://127.0.0.1:8000/portal/

---

## ⚙️ Configuration (`floodwatch/settings.py`)

```python
# Email alerts (Gmail SMTP)
EMAIL_HOST_USER     = 'your_gmail@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password_here'  # Gmail App Password

# Weather API (optional live data)
OPENWEATHER_API_KEY = 'your_openweather_key_here'

# Admin PDF password gate
ADMIN_PDF_PASSWORD  = 'floodwatch2024'  # ← Change this!

# SECRET_KEY — change before deploying to production!
SECRET_KEY = 'django-insecure-...'
```

---

## 📁 Project Structure

```
FloodWatch_v8_Fixed/
├── core/
│   ├── models.py          — WaterLevel, FloodAlert, FloodReport, RescueTeam
│   ├── views.py           — All views (fixed)
│   ├── urls.py            — URL routes
│   ├── simulator.py       — Background water level simulator
│   ├── static/core/
│   │   ├── js/fw-sw.js   — Service worker (fixed poll interval)
│   │   ├── img/           — Notification icons (NEW)
│   │   └── sounds/        — Alert sounds
│   └── templates/core/
│       ├── admin_reports.html  — Fixed for loop
│       ├── pdf_password.html   — NEW: PDF password gate
│       └── ...
├── floodwatch/
│   ├── settings.py        — Fixed LOGIN_URL + ADMIN_PDF_PASSWORD added
│   └── urls.py
└── requirements.txt       — Pillow confirmed
```

Emergency Helpline: **1077** | Kerala SDMA Portal

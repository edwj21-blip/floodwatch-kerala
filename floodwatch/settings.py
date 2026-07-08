from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load secrets from a local .env file (never committed to git — see .gitignore)
load_dotenv(BASE_DIR / '.env')

# ─── Core secrets — set these in your .env file, do NOT hardcode them here ───
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-floodwatch-secret-key-change-in-production',  # dev-only fallback
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'floodwatch.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # FloodWatch: injects active HIGH/EXTREME alerts into all pages
                'core.context_processors.active_alert_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'floodwatch.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/portal/'

# ─── OpenWeatherMap API ───────────────────────────────────────────────────────
# Sign up free at https://openweathermap.org/api and put your key in .env as OPENWEATHER_API_KEY
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'YOUR_OPENWEATHER_API_KEY_HERE')

# ─── Email Configuration (Gmail SMTP) ────────────────────────────────────────
# For auto email alerts: use Gmail App Password (not your normal password)
# Steps: Google Account → Security → 2-Step Verification → App passwords
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'your_gmail@gmail.com')          # ← Set in .env
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'your_app_password_here')  # ← Set in .env (App Password, not Gmail password)
DEFAULT_FROM_EMAIL = f'FloodWatch Kerala <{EMAIL_HOST_USER}>'
FLOODWATCH_ALERT_EMAIL_ENABLED = os.environ.get('FLOODWATCH_ALERT_EMAIL_ENABLED', 'True') == 'True'

# ─── PDF Report ───────────────────────────────────────────────────────────────
# pip install reportlab
FLOODWATCH_PDF_ENABLED = True
# Admin PDF password gate — set a strong secret password in .env
ADMIN_PDF_PASSWORD = os.environ.get('ADMIN_PDF_PASSWORD', 'floodwatch2024')   # ← Change this in production!

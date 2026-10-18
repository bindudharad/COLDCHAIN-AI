from pathlib import Path
import os, sys

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
BASE_DIR = REPO_ROOT

for p in [str(BACKEND_DIR), str(REPO_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-only-change-this-key')
IOT_HARDWARE_API_KEY = os.getenv('COLDCHAIN_IOT_HARDWARE_KEY', 'coldchain-verified-hardware-secret-key-2026')
REGISTERED_IOT_HARDWARE_DEVICES = {
    'HW-NODE-01': os.getenv('HW_NODE_01_KEY', 'hw-node-01-sec-7f9a2b4c'),
    'HW-NODE-02': os.getenv('HW_NODE_02_KEY', 'hw-node-02-sec-8e1d3c5b'),
    'AUTHENTICATED-HW-01': os.getenv('AUTHENTICATED_HW_01_KEY', 'authenticated-hw-01-sec-1a2b3c4d'),
    'CC-PHYSICAL-MAIN': os.getenv('CC_PHYSICAL_MAIN_KEY', 'cc-physical-main-sec-9a0b1c2d'),
}
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')]
INSTALLED_APPS = ['corsheaders','django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','rest_framework','apps.monitoring']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:4173',
    'http://127.0.0.1:4173',
]
CORS_ALLOW_ALL_ORIGINS = DEBUG
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BACKEND_DIR / 'templates', BASE_DIR / 'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BACKEND_DIR / 'db.sqlite3'}}
LANGUAGE_CODE='en-us'; TIME_ZONE='UTC'; USE_I18N=True; USE_TZ=True
STATIC_URL='static/'
STATICFILES_DIRS=[p for p in [BACKEND_DIR / 'static', BASE_DIR / 'static'] if p.exists()]
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
WINDOW_SIZE = 60; FORECAST_HORIZON = 15


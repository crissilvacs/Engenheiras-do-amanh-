"""
Django settings for engenheiras_do_amanha project.
"""

import os
from pathlib import Path
import environ

# Inicializa o django-environ no topo do ficheiro
env = environ.Env(
    DEBUG=(bool, False)
)

# Define o caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Tenta ler o ficheiro .env (para desenvolvimento local)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# --- Configurações de Segurança e Chaves ---
# Lê a SECRET_KEY do ambiente. Se não encontrar, usa uma chave insegura (só para emergências).
SECRET_KEY = env('SECRET_KEY', default='django-insecure-fallback-key-for-local-dev')

# Lê o modo DEBUG do ambiente. O padrão é True para desenvolvimento local.
DEBUG = env.bool('DEBUG', default=False)


# --- Configurações Gerais ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'pagina_inicial'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- Configurações de Ambiente (Desenvolvimento vs. Produção) ---

if DEBUG:
    # --- Configurações para Ambiente de Desenvolvimento Local (DEBUG=True) ---
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'comunidade', 'static')]
    
    # Em desenvolvimento, os e-mails são IMPRESSOS NO TERMINAL
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

else:
    # --- Configurações para Ambiente de Produção (DEBUG=False) ---
    ALLOWED_HOSTS = ['engamanha.pythonanywhere.com']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'engamanha$default',
            'USER': 'engamanha',
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': 'engamanha.mysql.pythonanywhere-services.com',
            'PORT': '3306',
        }
    }
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    
    # Em produção, usamos um servidor de e-mail real
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# --- Aplicações Instaladas (Comum a ambos os ambientes) ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'comunidade',
    'taggit',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'captcha',
    'metrics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'metrics.middleware.RequestLogMiddleware',
]

ROOT_URLCONF = 'engenheiras_do_amanha.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'comunidade', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'engenheiras_do_amanha.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configurações do Django Allauth ---
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/login/'
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_ADAPTER = 'comunidade.adapters.CustomSocialAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online', 'prompt': 'select_account'}
    }
}

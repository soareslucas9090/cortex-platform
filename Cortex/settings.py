import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from .rest_framework_settings import *
from .spectacular_settings import *


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

_DEFAULT_SECRET_KEY = 'TROQUE-ESTA-CHAVE-NO-ENV-ANTES-DE-SUBIR-PARA-PRODUCAO'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', _DEFAULT_SECRET_KEY)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

if not DEBUG and SECRET_KEY == _DEFAULT_SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY não configurada. Defina DJANGO_SECRET_KEY no arquivo .env antes de rodar em produção.'
    )

# Signing key do Simple JWT — usa SECRET_KEY como fallback seguro em dev.
# Configure SIMPLE_JWT_SIGNING_KEY no .env em produção para uma chave dedicada.
SIMPLE_JWT['SIGNING_KEY'] = os.environ.get('SIMPLE_JWT_SIGNING_KEY', SECRET_KEY)  # noqa: F821

# Backends de autenticação — EmailOrCpfBackend aceita login por e-mail ou CPF;
# ModelBackend é mantido como fallback para o Django admin.
AUTHENTICATION_BACKENDS = [
    'AppCore.basics.auth.backends.EmailOrCpfBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# AUTH_USER_MODEL será definido na Milestone 1 quando identidade.Usuario for criado.
# AUTH_USER_MODEL = 'identidade.Usuario'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [origin for origin in csrf_origins.split(',') if origin]

cors_origins = os.environ.get('CORS_ORIGIN_WHITELIST', '')
CORS_ORIGIN_WHITELIST = [origin for origin in cors_origins.split(',') if origin]

internal_ips = os.environ.get('INTERNAL_IPS', '')
INTERNAL_IPS = [ip for ip in internal_ips.split(',') if ip]

CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False') == 'True'

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DATABASE_USER', ''),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', ''),
        'PORT': os.environ.get('DATABASE_PORT', ''),
    }
}

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")

EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# As configurações padrões são para o serviço de email do Google, mas podem ser alteradas
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", True)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

DEFAULT_ROOT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'debug_toolbar',
    'rest_framework_simplejwt',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'simple_history',
    # Allauth (descomente quando configurar o login social)
    # 'django.contrib.sites',
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',
]

AUTH_APPS = [
    'Auth.auth',
]

# Adicione os apps do seu projeto aqui
PROJECT_APPS = [
    'identidade',
]

INSTALLED_APPS = DEFAULT_ROOT_APPS + AUTH_APPS + PROJECT_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

AUTH_USER_MODEL = 'identidade.Usuario'

AUTHENTICATION_BACKENDS = [
    # Backend principal: aceita 'login' como e-mail ou CPF.
    # Requer que AUTH_USER_MODEL possua os campos 'email' e 'cpf'.
    'AppCore.basics.auth.backends.EmailOrCpfBackend',
    # Fallback padrão do Django — mantém login pelo admin e outros fluxos internos.
    'django.contrib.auth.backends.ModelBackend',
]

# Configurações do django-allauth (descomente para ativar login social)
# SITE_ID = 1
# ACCOUNT_AUTHENTICATION_METHOD = 'email'
# ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = 'none'
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'SCOPE': ['profile', 'email'],
#         'AUTH_PARAMS': {'access_type': 'online'},
#         'APP': {
#             'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
#             'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
#             'key': '',
#         },
#     }
# }

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.history.HistoryPanel',
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

ROOT_URLCONF = 'Cortex.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'Cortex.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Fortaleza'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

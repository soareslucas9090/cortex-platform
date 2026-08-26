import os, sys
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

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', '*').split(',')
    if host.strip()
]

if not DEBUG and (not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        'ALLOWED_HOSTS inválido em produção. Defina domínios explícitos (não use *).'
    )

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
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DATABASE_NAME', 'cortex'),
        'USER': os.environ.get('DATABASE_USER', 'cortex'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'cortex'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cortex',
        'USER': 'postgres',
        'PASSWORD': '12345678',
        'HOST': 'localhost',
        'PORT': '5432',
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
    'django.contrib.postgres',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
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
    'Identidade.usuarios',
    'Identidade.contatos',
    'Identidade.enderecos',
    'Identidade.matriculas',
    'Organizacional.setores',
    'Organizacional.funcoes',
    'Organizacional.vinculos',
    'PessoasInstitucionais.cargos',
    'PessoasInstitucionais.empresas_instituicoes',
    'PessoasInstitucionais.servidores',
    'PessoasInstitucionais.terceirizados',
    'Academico.cursos',
    'Academico.alunos',
    'Academico.aluno_cursos',
    'Infraestrutura.blocos',
    'Infraestrutura.salas',
    'Infraestrutura.recursos',
    'Infraestrutura.permissoes',
    'Infraestrutura.autorizacoes',
    'Infraestrutura.emprestimos',
    'Infraestrutura.importacoes',
]

_DEBUG_APPS = ['debug_toolbar'] if DEBUG else []

INSTALLED_APPS = DEFAULT_ROOT_APPS + _DEBUG_APPS + AUTH_APPS + PROJECT_APPS

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
]

if DEBUG:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

AUTH_USER_MODEL = 'usuarios.Usuario'

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

if DEBUG:
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
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de Mídia (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configurações do Celery
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Configurações do armazenamento de modelos (S3)
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', 'https://t3.storage.box')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'bucket-name')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
CORTEX_PUBLIC_BASE_URL = os.environ.get('CORTEX_PUBLIC_BASE_URL', '').rstrip('/')


import os
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'AppCore.basics.pagination.pagination.PaginacaoCustomizada',
    'PAGE_SIZE': 10,
    'DATE_INPUT_FORMATS': [
        '%Y-%m-%d',
        '%Y/%m/%d',
    ],
    'TIME_INPUT_FORMATS': [
        '%H:%M',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'BLACKLIST_AFTER_ROTATION': False,
    # SIGNING_KEY é definido em settings.py após SECRET_KEY para evitar import circular.
    # O valor aqui é sobrescrito pelo update() em settings.py.
    'AUTH_HEADER_TYPES': ('Bearer',),
    # Serializer de login do projeto — altere para customizar payload e login por tipo:
    'TOKEN_OBTAIN_SERIALIZER': 'Auth.auth.serializers.LoginSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
    'SLIDING_TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer',
    'SLIDING_TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer',
}

from pathlib import Path
from datetime import timedelta
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool)



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.usuarios',
    'apps.roles',
    'apps.eventos',
    'apps.lugares',
    'apps.layouts',
    'apps.asientos',
    'apps.ordenes',
    'apps.zonas',
    'apps.grid_cells',
    'apps.tickets',
    'apps.precio_zona_evento',
    'apps.auditoria_logs',
    'rest_framework',
    'corsheaders',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config(
        'CORS_ORIGINS',
        default='http://localhost:5173,http://localhost:5174,http://localhost:3000',
    ).split(',')
    if origin.strip()
]

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1',
).split(',')

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.common.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_CLAIM": "user_id",
}
LOGS_DIR = BASE_DIR / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} | {levelname: <8} | {name}:{funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG",
        },
        "file_debug": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "debug.log"),
            "formatter": "verbose",
            "level": "DEBUG",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,               # retención: últimos 5 archivos
            "encoding": "utf-8",
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "error.log"),
            "formatter": "verbose",
            "level": "ERROR",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "filters": {
        "only_debug": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: record.levelno <= 10,  # solo DEBUG
        },
        "only_error": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: record.levelno >= 40,  # solo ERROR+
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_debug"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.eventos": {
            "handlers": ["console", "file_debug", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.lugares": {
            "handlers": ["console", "file_debug", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps.layouts": {
            "handlers": ["console", "file_debug", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file_debug", "file_error"],
        "level": "DEBUG",
    },
}

AES_SECRET_KEY = config(
    'AES_SECRET_KEY',
    default=None,
    cast=str
)

HMAC_SECRET_KEY = config(
    'HMAC_SECRET_KEY',
    default=None,
    cast=str
)

# Validación en desarrollo
if DEBUG and (AES_SECRET_KEY is None or HMAC_SECRET_KEY is None):
    import warnings
    warnings.warn(
        "AES_SECRET_KEY y/o HMAC_SECRET_KEY no están configuradas. "
        "Ejecutar: python generate_keys.py",
        RuntimeWarning
    )
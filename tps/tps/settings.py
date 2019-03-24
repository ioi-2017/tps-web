# Amir Keivan Mohtashami
# Amirmohsen Ahanchi
# Mohammad Javad Naderi

"""
Django settings for tps project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

import logging

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from kombu import Exchange
from kombu import Queue

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'd#kb9j&&o5t!p(^cj!2c6#e!g5_)9yj-m%%d!djxmasi5eu1ir'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

SITE_ID = 1

# Application definition

INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',


    # Vendor Apps
    'bootstrap3',
    'import_export',
    'debug_toolbar',
    'django_extensions',

    # TPS Apps
    'core',
    'accounts',
    'problems',
    'judge',
    'file_repository',
    'runner',
    'tasks',
    'trader',

]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tps.middlewares.middleware.LoginRequiredMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'tps.urls'

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
                'problems.views.context_processors.revision_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'tps.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


AUTH_USER_MODEL = 'accounts.User'

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # Problem role permission backend
    'problems.backends.ProblemRoleBackend',
)

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "assets"),
]

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static")

MEDIA_ROOT = os.path.join(BASE_DIR, 'storage')
MEDIA_URL = "/storage/"

COMMIT_STORAGE_ROOT = os.path.join(BASE_DIR, 'commits')

# project settings

# fail-safe time limit in seconds (float)
FAILSAFE_TIME_LIMIT = 30

# fail-safe memory limit in MB (int)
FAILSAFE_MEMORY_LIMIT = 512

SANDBOX_TEMP_DIR = "/tmp"
# SANDBOX_TEMP_DIR = os.path.join(BASE_DIR, "tmp")

# sandbox
SANDBOX_KEEP = False
SANDBOX_USE_CGROUPS = True
SANDBOX_MAX_FILE_SIZE = 1048576
SANDBOX_BOX_ID_OFFSET = 0
# isolate
ISOLATE_PATH = os.path.join(BASE_DIR, "../isolate/isolate")

BOOTSTRAP3 = {
    'field_renderers': {
        'default': 'bootstrap3.renderers.FieldRenderer',
        'inline': 'bootstrap3.renderers.InlineFieldRenderer',
        'readonly': 'problems.forms.renderers.ReadOnlyFieldRenderer',
    },
}

LOGIN_REQUIRED_URLS_EXCEPTIONS = (
    r'/accounts/login/$',
    r'/accounts/logout/$',
    r'/admin/login/$',
    r'/admin/$'
)

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

JUDGE_DEFAULT_NAME = 'local_runner'

JUDGE_HANDLERS = {
    'local_runner': {
        'class': 'judges.runner.Runner',
        'parameters': {
            'compile_time_limit': 30,
            'compile_memory_limit': 1024,
        }
    }
}

CELERY_MAX_RETRIES = None
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

CELERY_TASK_QUEUES = (
    Queue('celery', Exchange('celery'), routing_key='default'),
    Queue('invoke', Exchange('invoke'), routing_key='invoke'),
)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": None
    }
}



DISABLE_BRANCHES = True

# GIT ORM
from git_orm import set_repository, set_branch

set_repository(os.path.join(BASE_DIR, 'repo'))
set_branch('master')

GIT_USER_NAME = 'TPS'
GIT_USER_EMAIL = 'tps@localhost'


def SHOW_TOOLBAR(request):
    return request.user.is_superuser and False

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': SHOW_TOOLBAR,
}

try:
    from .local_settings import *
except:
    pass

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-this-key-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "companyapp",
    "candidateapp",
    "adminapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "career_predictor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "career_predictor.wsgi.application"

if os.getenv("USE_MYSQL", "False") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "career_predictor"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:redirect_after_login"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------- NVIDIA AI Build config (https://build.nvidia.com/models) ----------------
NVIDIA_API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
NVIDIA_KEYS = {
    "resume_parser": os.getenv("NVIDIA_API_KEY_RESUME_PARSER", ""),
    "career_roadmap": os.getenv("NVIDIA_API_KEY_CAREER_ROADMAP", ""),
    "resume_analyzer": os.getenv("NVIDIA_API_KEY_RESUME_ANALYZER", ""),
    "chat": os.getenv("NVIDIA_API_KEY_CHAT", ""),
}
NVIDIA_MODELS = {
    "resume_parser": os.getenv("NVIDIA_MODEL_RESUME_PARSER", "meta/llama3-70b-instruct"),
    "career_roadmap": os.getenv("NVIDIA_MODEL_CAREER_ROADMAP", "meta/llama3-70b-instruct"),
    "resume_analyzer": os.getenv("NVIDIA_MODEL_RESUME_ANALYZER", "meta/llama3-70b-instruct"),
    "chat": os.getenv("NVIDIA_MODEL_CHAT", "meta/llama3-70b-instruct"),
}

MAX_QUIZ_VIOLATIONS = 3

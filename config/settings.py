"""
Django 配置 - OPASSIT 企业运营与自动化工作平台
支持 .env 环境变量，跨 Windows / Linux 运行
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-django-opassit")

DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "corsheaders",
    "apps.organizations",
    "apps.accounts",
    "apps.automation",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# === 数据库 MySQL ===
_db_user = os.getenv("MYSQL_USER", "opassit")
_db_pass = os.getenv("MYSQL_PASSWORD", "opassit")
_db_host = os.getenv("MYSQL_HOST", "localhost")
_db_port = os.getenv("MYSQL_PORT", "3306")
_db_name = os.getenv("MYSQL_DATABASE", "opassit")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": _db_name,
        "USER": _db_user,
        "PASSWORD": _db_pass,
        "HOST": _db_host,
        "PORT": _db_port,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === CORS 多端访问（PC/平板/手机前端）===
_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
CORS_ALLOWED_ORIGINS = [x.strip() for x in _cors.split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# === 登录/登出 ===
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# === Jazzmin Admin 主题 ===
JAZZMIN_SETTINGS = {
    "site_title": "OPASSIT 管理后台",
    "site_header": "OPASSIT",
    "site_brand": "企业运营与自动化",
    "welcome_sign": "欢迎使用 OPASSIT 管理后台",
    "search_model": ["organizations.Organization", "auth.User", "accounts.Role"],
    "topmenu_links": [
        {"name": "仪表盘", "url": "/dashboard/"},
        {"name": "首页", "url": "/"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "organizations": "fas fa-building",
        "organizations.Organization": "fas fa-sitemap",
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "accounts": "fas fa-user-tag",
        "accounts.role": "fas fa-user-shield",
        "automation": "fas fa-robot",
        "automation.automationtask": "fas fa-tasks",
    },
    "order_with_respect_to": ["organizations", "auth", "accounts", "automation"],
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": False,
    "language_chooser": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "organizations.organization": "collapsible",
    },
}

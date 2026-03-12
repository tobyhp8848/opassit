"""
ASGI 配置 - OPASSIT
用于 WebSocket / 异步部署
"""
import os

import pymysql
pymysql.install_as_MySQLdb()

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()

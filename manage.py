#!/usr/bin/env python
"""Django 管理脚本 - OPASSIT 企业运营与自动化工作平台"""
import os
import sys

# PyMySQL 兼容 Django（无需 mysqlclient 编译）
import pymysql
pymysql.install_as_MySQLdb()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django。请确认已安装且虚拟环境已激活。"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

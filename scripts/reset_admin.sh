#!/bin/bash
# 重置管理员密码（调用 Django management 命令）
# 用法: ./scripts/reset_admin.sh  或  ./scripts/reset_admin.sh 用户名  或  ./scripts/reset_admin.sh 用户名 新密码
cd "$(dirname "$0")/.."
[ -d .venv ] && source .venv/bin/activate
if [ -n "$2" ]; then
  python manage.py reset_admin --username "$1" --password "$2"
elif [ -n "$1" ]; then
  python manage.py reset_admin --username "$1"
else
  python manage.py reset_admin
fi

#!/bin/bash
# 创建 opassit 数据库、用户，并执行 Django 迁移
set -e
cd "$(dirname "$0")/.."

echo "=== 1. 创建 opassit 数据库和用户 ==="
read -s -p "请输入 MySQL root 密码: " MYSQL_ROOT_PWD
echo
export MYSQL_PWD="$MYSQL_ROOT_PWD"
mysql -u root -e "
CREATE DATABASE IF NOT EXISTS opassit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'opassit'@'localhost' IDENTIFIED BY 'opassit';
GRANT ALL PRIVILEGES ON opassit.* TO 'opassit'@'localhost';
FLUSH PRIVILEGES;
"
unset MYSQL_PWD
echo "数据库和用户已就绪。"

echo ""
echo "=== 2. 执行 Django 迁移 ==="
source .venv/bin/activate
python manage.py migrate
echo ""
echo "=== 完成 ==="

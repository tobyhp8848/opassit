#!/bin/bash
# OPASSIT 运行环境创建脚本 - Linux / macOS (Django)
set -e
cd "$(dirname "$0")/.."

echo "==> 创建 Python 虚拟环境..."
python3 -m venv .venv

echo "==> 激活虚拟环境..."
source .venv/bin/activate

echo "==> 安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> 复制环境变量..."
[ -f .env ] || cp .env.example .env
echo "    请编辑 .env 配置数据库等"

echo ""
echo "==> 初始化数据库（需先启动 MySQL）..."
echo "    python manage.py migrate"
echo "    python manage.py createsuperuser  # 创建管理员"
echo ""
echo "✅ 环境创建完成！"
echo "   激活: source .venv/bin/activate"
echo "   运行: python manage.py runserver"
echo "   后台: http://127.0.0.1:8000/admin/"
echo "   健康: http://127.0.0.1:8000/health/"

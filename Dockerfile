# OPASSIT - Django 跨平台 Docker 镜像
# 可在 Windows / Linux 上运行
FROM python:3.12-slim

WORKDIR /app

# Python 依赖（PyMySQL 无需系统库）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

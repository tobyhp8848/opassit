# OPASSIT - 企业运营与自动化工作平台

基于 **Django + MySQL** 的企业级 Web 应用，支持金融、电商、企业管理场景，多端适配，跨 Windows / Linux 运行。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Django 5.x |
| 数据库 | MySQL 8.0 (PyMySQL) |
| 前端 | 响应式模板，可扩展 Vue/React |
| 部署 | Docker / Gunicorn |

## 运行环境创建

### 方式一：脚本自动创建（推荐）

**Linux / macOS：**
```bash
chmod +x scripts/setup_env.sh
./scripts/setup_env.sh
source .venv/bin/activate
```

**Windows PowerShell：**
```powershell
.\scripts\setup_env.ps1
.\.venv\Scripts\Activate.ps1
```

### 方式二：手动创建

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置 MYSQL_* 等
```

### 方式三：Docker（跨平台统一环境）

```bash
cp .env.example .env
docker-compose up -d
# Web: http://localhost:8000
# MySQL: localhost:3306
```

## 初始化与启动

```bash
# 激活环境后
python manage.py migrate          # 创建表
python manage.py createsuperuser  # 创建管理员

# 开发模式
python manage.py runserver

# 生产模式（Gunicorn）
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

| 地址 | 说明 |
|------|------|
| http://127.0.0.1:8000/ | 首页 |
| http://127.0.0.1:8000/admin/ | 管理后台 |
| http://127.0.0.1:8000/health/ | 健康检查 |
| http://127.0.0.1:8000/api/status/ | API 状态 |

## 项目结构

```
opassit/
├── manage.py
├── config/               # Django 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   └── core/             # 核心应用
├── templates/
├── static/
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

## 架构说明

采用 **Django 全栈架构**，适合金融、电商、企业管理等对数据安全和业务严谨性要求高的场景。详见 [docs/ARCHITECTURE_OPTIONS.md](docs/ARCHITECTURE_OPTIONS.md)。

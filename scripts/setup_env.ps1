# OPASSIT 运行环境创建脚本 - Windows PowerShell (Django)
Set-Location $PSScriptRoot\..

Write-Host "==> 创建 Python 虚拟环境..." -ForegroundColor Cyan
python -m venv .venv

Write-Host "==> 激活虚拟环境..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

Write-Host "==> 安装依赖..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "==> 复制环境变量..." -ForegroundColor Cyan
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "    请编辑 .env 配置数据库等" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==> 初始化数据库（需先启动 MySQL）..." -ForegroundColor Cyan
Write-Host "    python manage.py migrate"
Write-Host "    python manage.py createsuperuser  # 创建管理员"
Write-Host ""
Write-Host "✅ 环境创建完成！" -ForegroundColor Green
Write-Host "   激活: .\.venv\Scripts\Activate.ps1"
Write-Host "   运行: python manage.py runserver"
Write-Host "   后台: http://127.0.0.1:8000/admin/"
Write-Host "   健康: http://127.0.0.1:8000/health/"

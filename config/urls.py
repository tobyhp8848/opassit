"""
OPASSIT 主 URL 配置
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_status_view(request):
    """API 状态"""
    return JsonResponse({
        "app": "OPASSIT",
        "status": "ok",
        "message": "Django 服务运行中，支持多端访问",
    })


def health_view(request):
    """健康检查"""
    return JsonResponse({"status": "healthy"})


urlpatterns = [
    path("", include("apps.core.urls")),
    path("api/status/", api_status_view),
    path("health/", health_view),
    path("admin/", admin.site.urls),
]

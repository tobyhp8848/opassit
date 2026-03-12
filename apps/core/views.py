from django.shortcuts import render


def index(request):
    """首页 - 响应式模板，适配 PC/平板/手机"""
    return render(request, "core/index.html", {"app_name": "OPASSIT"})

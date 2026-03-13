from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView as AuthPasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import View
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """退出登录 - 登出后跳转到首页"""
    logout(request)
    return redirect("/")


class HomeLoginView(LoginView):
    """首页 = 登录页"""
    template_name = "core/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/dashboard/"


class DashboardView(LoginRequiredMixin, View):
    """管理后台仪表盘"""
    login_url = "/"

    def get(self, request):
        return render(request, "core/dashboard.html", {"user": request.user})


class PasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, AuthPasswordChangeView):
    """修改密码 - AdminLTE 风格"""
    template_name = "core/password_change.html"
    success_url = reverse_lazy("core:dashboard")
    success_message = "密码已修改，请使用新密码登录。"

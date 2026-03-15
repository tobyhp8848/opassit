"""核心中间件"""
from django.shortcuts import redirect
from django.urls import reverse

from apps.accounts.models import UserProfile


class RequirePasswordChangeMiddleware:
    """当用户被标记为首次登录须修改密码时，强制跳转到修改密码页"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                must_change = request.user.profile.must_change_password
            except (UserProfile.DoesNotExist, AttributeError):
                must_change = False
            if must_change:
                password_change_url = reverse("core:password_change")
                logout_url = "/logout/"
                current_path = request.path
                if not current_path.startswith(password_change_url) and current_path != logout_url:
                    return redirect(f"{password_change_url}?next={request.get_full_path()}")
        return self.get_response(request)

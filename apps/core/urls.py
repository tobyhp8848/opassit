from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/password-change/", views.PasswordChangeView.as_view(), name="password_change"),
]

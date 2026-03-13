from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/add/", views.UserCreateView.as_view(), name="user_add"),
    path("users/<int:pk>/", views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("roles/", views.RoleListView.as_view(), name="role_list"),
    path("roles/add/", views.RoleCreateView.as_view(), name="role_add"),
    path("roles/<int:pk>/", views.RoleUpdateView.as_view(), name="role_edit"),
    path("roles/<int:pk>/delete/", views.RoleDeleteView.as_view(), name="role_delete"),
]

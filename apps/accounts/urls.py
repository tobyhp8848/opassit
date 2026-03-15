from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/add/", views.UserCreateView.as_view(), name="user_add"),
    path("users/deleted/", views.UserDeletedListView.as_view(), name="user_deleted_list"),
    path("users/<int:pk>/", views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/reset-password/", views.UserResetPasswordView.as_view(), name="user_reset_password"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("users/<int:pk>/restore/", views.UserRestoreView.as_view(), name="user_restore"),
    path("users/<int:pk>/permanent-delete/", views.UserPermanentDeleteView.as_view(), name="user_permanent_delete"),
    path("roles/", views.RoleListView.as_view(), name="role_list"),
    path("roles/add/", views.RoleCreateView.as_view(), name="role_add"),
    path("roles/<int:pk>/", views.RoleUpdateView.as_view(), name="role_edit"),
    path("roles/<int:pk>/delete/", views.RoleDeleteView.as_view(), name="role_delete"),
    path("uor/", views.UserOrganizationRoleListView.as_view(), name="uor_list"),
    path("uor/add/", views.UserOrganizationRoleCreateView.as_view(), name="uor_add"),
    path("uor/<int:pk>/", views.UserOrganizationRoleUpdateView.as_view(), name="uor_edit"),
    path("uor/<int:pk>/delete/", views.UserOrganizationRoleDeleteView.as_view(), name="uor_delete"),
]

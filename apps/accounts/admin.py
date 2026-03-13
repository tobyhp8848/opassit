from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from .models import Role, UserOrganizationRole, UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "用户档案"


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """角色管理重定向到 AdminLTE 自定义页面"""

    list_display = ["name", "code", "is_system"]

    def changelist_view(self, request, extra_context=None):
        return redirect("accounts:role_list")

    def add_view(self, request, form_url="", extra_context=None):
        return redirect("accounts:role_add")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect("accounts:role_edit", pk=object_id)

    def delete_view(self, request, object_id, extra_context=None):
        return redirect("accounts:role_delete", pk=object_id)


@admin.register(UserOrganizationRole)
class UserOrganizationRoleAdmin(admin.ModelAdmin):
    """用户-组织-角色 重定向到 AdminLTE 自定义页面"""

    list_display = ["user", "organization", "role", "is_primary"]

    def changelist_view(self, request, extra_context=None):
        return redirect("accounts:uor_list")

    def add_view(self, request, form_url="", extra_context=None):
        return redirect("accounts:uor_add")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect("accounts:uor_edit", pk=object_id)

    def delete_view(self, request, object_id, extra_context=None):
        return redirect("accounts:uor_delete", pk=object_id)

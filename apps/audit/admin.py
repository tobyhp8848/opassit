"""审计日志 - 仅展示，不可编辑"""
from django.contrib import admin
from django.utils.html import format_html

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action_badge", "target_model", "target_id", "target_repr", "user", "ip_address", "created_at")
    list_filter = ("action", "target_model")
    search_fields = ("target_repr", "target_id", "user__username")
    readonly_fields = ("user", "action", "target_model", "target_id", "target_repr", "extra", "ip_address", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    def action_badge(self, obj):
        colors = {
            "create": "success",
            "update": "info",
            "delete": "warning",
            "restore": "primary",
            "approve": "success",
            "reject": "danger",
            "cancel": "secondary",
            "permanent_delete": "danger",
            "execute": "primary",
        }
        c = colors.get(obj.action, "secondary")
        return format_html('<span class="badge badge-{}">{}</span>', c, obj.get_action_display())
    action_badge.short_description = "操作"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

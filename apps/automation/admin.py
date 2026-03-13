from django.contrib import admin
from django.shortcuts import redirect
from .models import AutomationTask


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    """自动化任务重定向到 AdminLTE 自定义页面"""

    list_display = ["name", "task_type", "organization", "status", "created_at"]

    def changelist_view(self, request, extra_context=None):
        return redirect("automation:task_list")

    def add_view(self, request, form_url="", extra_context=None):
        return redirect("automation:task_add")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect("automation:task_edit", pk=object_id)

    def delete_view(self, request, object_id, extra_context=None):
        return redirect("automation:task_delete", pk=object_id)

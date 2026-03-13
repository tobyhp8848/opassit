from django.contrib import admin
from .models import AutomationTask


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    list_display = ["name", "task_type", "organization", "status", "created_at"]
    list_filter = ["task_type", "status"]
    search_fields = ["name"]

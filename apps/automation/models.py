"""
自动化任务模型 - 例行、重复性工作的自动化
"""
from django.contrib.auth import get_user_model
from django.db import models
from apps.organizations.models import Organization

User = get_user_model()


class AutomationTask(models.Model):
    """自动化任务 - 抓取、定时运行等"""

    class TaskType(models.TextChoices):
        SCRAPE = "scrape", "数据抓取"
        SCHEDULE = "schedule", "定时任务"
        WORKFLOW = "workflow", "工作流"
        TRIGGER = "trigger", "触发器"

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        ACTIVE = "active", "运行中"
        PAUSED = "paused", "已暂停"
        ERROR = "error", "异常"

    name = models.CharField("任务名称", max_length=100)
    task_type = models.CharField(
        "任务类型", max_length=20, choices=TaskType.choices, default=TaskType.SCHEDULE
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="automation_tasks",
        verbose_name="所属组织",
        null=True,
        blank=True,
    )
    config = models.JSONField("配置(JSON)", default=dict, blank=True)
    status = models.CharField(
        "状态", max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="创建人"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_run_at = models.DateTimeField("上次运行", null=True, blank=True)

    class Meta:
        verbose_name = "自动化任务"
        verbose_name_plural = "自动化任务"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

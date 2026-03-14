"""
自动化任务模型 - 例行、重复性工作的自动化
"""
import random
import string

from django.contrib.auth import get_user_model
from django.db import models
from apps.organizations.models import Organization

User = get_user_model()


def generate_task_id():
    """生成全项目唯一任务 ID：TASK + 时间戳后缀 + 随机码，确保不重复"""
    from django.utils import timezone
    chars = string.ascii_uppercase + string.digits
    base = f"TASK{timezone.now().strftime('%m%d%H%M')}"
    for _ in range(50):
        suffix = "".join(random.choices(chars, k=4))
        tid = f"{base}{suffix}"
        if not AutomationTask.objects.filter(task_id=tid).exists():
            return tid
    for _ in range(100):
        suffix = "".join(random.choices(chars, k=6))
        tid = f"TASK{suffix}"
        if not AutomationTask.objects.filter(task_id=tid).exists():
            return tid
    raise ValueError("无法生成唯一 task_id，请重试")


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

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "审批通过"
        ASSIGN_BUILD = "assign_build", "指派人员构建工作"
        ASSIGN_DONE = "assign_done", "指派任务完成"
        EXECUTABLE = "executable", "任务可执行"
        REJECTED = "rejected", "已驳回"
        CANCELLED = "cancelled", "被取消"

    class BuildStatus(models.TextChoices):
        ACCEPTED = "accepted", "接受任务"
        IN_PROGRESS = "in_progress", "构建工作进行中"
        COMPLETED = "completed", "构建工作完成"
        RETURN_REVISION = "return_revision", "退回再修改"

    class ScheduleType(models.TextChoices):
        ONCE = "once", "执行一次"
        RECURRING = "recurring", "周期性执行"

    task_id = models.CharField(
        "任务ID",
        max_length=20,
        unique=True,
        blank=True,
        help_text="全项目唯一标识，用于追踪。系统自动生成或用户指定，均不可重复。",
    )
    name = models.CharField("任务名称", max_length=100)
    task_type = models.CharField(
        "任务类型", max_length=20, choices=TaskType.choices, default=TaskType.SCHEDULE
    )
    description = models.TextField("任务详细说明", blank=True)
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
    # 计划执行时间
    schedule_type = models.CharField(
        "执行类型", max_length=20, choices=ScheduleType.choices, default=ScheduleType.ONCE
    )
    scheduled_run_at = models.DateTimeField("计划执行时间", null=True, blank=True)
    cron_expression = models.CharField(
        "Cron 表达式", max_length=100, blank=True,
        help_text="周期性任务使用，如 0 9 * * * 表示每天 9:00"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="创建人"
    )
    approval_status = models.CharField(
        "审批状态",
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approved_at = models.DateTimeField("审批时间", null=True, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_build_tasks",
        verbose_name="指派构建人员",
    )
    build_status = models.CharField(
        "构建状态",
        max_length=20,
        choices=BuildStatus.choices,
        blank=True,
        default="",
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_tasks",
        verbose_name="审批人",
    )
    is_deleted = models.BooleanField("已删除", default=False)
    deleted_at = models.DateTimeField("删除时间", null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deleted_tasks",
        verbose_name="删除人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    last_run_at = models.DateTimeField("上次运行", null=True, blank=True)

    class Meta:
        verbose_name = "自动化任务"
        verbose_name_plural = "自动化任务"
        ordering = ["-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        tid = (self.task_id or "").strip()
        if tid:
            qs = AutomationTask.objects.filter(task_id=tid)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"task_id": f"任务ID「{tid}」已存在，全项目必须唯一"})

    def save(self, *args, **kwargs):
        if not (self.task_id or "").strip():
            self.task_id = generate_task_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class TaskRemark(models.Model):
    """管理员/高级管理员对任务的备注 - 仅 staff 以上可添加"""
    task = models.ForeignKey(
        AutomationTask,
        on_delete=models.CASCADE,
        related_name="remarks",
        verbose_name="所属任务",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="添加人",
    )
    content = models.TextField("备注内容")
    created_at = models.DateTimeField("添加时间", auto_now_add=True)

    class Meta:
        verbose_name = "任务备注"
        verbose_name_plural = "任务备注"
        ordering = ["-created_at"]

    def __str__(self):
        return f"备注 #{self.pk}"


class TaskAttachment(models.Model):
    """任务附件 - 支持批量上传，可标注备注"""
    task = models.ForeignKey(
        AutomationTask,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="所属任务",
    )
    file = models.FileField("附件", upload_to="task_attachments/%Y/%m/%d/")
    remark = models.CharField("备注", max_length=200, blank=True)
    created_at = models.DateTimeField("上传时间", auto_now_add=True)

    class Meta:
        verbose_name = "任务附件"
        verbose_name_plural = "任务附件"

    def __str__(self):
        return self.file.name

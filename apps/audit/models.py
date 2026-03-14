"""审计日志 - 记录用户操作"""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class AuditLog(models.Model):
    """操作审计日志"""

    class Action(models.TextChoices):
        CREATE = "create", "创建"
        UPDATE = "update", "编辑"
        DELETE = "delete", "删除(软删除)"
        RESTORE = "restore", "恢复"
        APPROVE = "approve", "审批通过"
        REJECT = "reject", "审批驳回"
        CANCEL = "cancel", "审批取消"
        PERMANENT_DELETE = "permanent_delete", "永久删除"
        EXECUTE = "execute", "执行"

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="操作人",
    )
    action = models.CharField("操作类型", max_length=20, choices=Action.choices)
    target_model = models.CharField("目标模型", max_length=50)  # automation_task, user
    target_id = models.PositiveIntegerField("目标ID")
    target_repr = models.CharField("目标描述", max_length=200, blank=True)
    extra = models.JSONField("扩展信息", default=dict, blank=True)
    ip_address = models.GenericIPAddressField("IP地址", null=True, blank=True)
    created_at = models.DateTimeField("操作时间", auto_now_add=True)

    class Meta:
        verbose_name = "审计日志"
        verbose_name_plural = "审计日志"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} {self.target_model}#{self.target_id} by {self.user}"


def log_audit(request, action, target_model, target_id, target_repr="", extra=None):
    """记录审计日志"""
    from apps.audit.models import AuditLog

    ip = None
    if request:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = (xff.split(",")[0].strip() if xff else None) or request.META.get("REMOTE_ADDR")

    AuditLog.objects.create(
        user=request.user if request and request.user.is_authenticated else None,
        action=action,
        target_model=target_model,
        target_id=target_id,
        target_repr=target_repr[:200],
        extra=extra or {},
        ip_address=ip,
    )

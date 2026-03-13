"""
用户、角色、权限模型
支持组织架构下的角色与权限管理
"""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
from apps.organizations.models import Organization


class Role(models.Model):
    """角色 - 可绑定到组织"""

    name = models.CharField("角色名称", max_length=50)
    code = models.CharField("角色编码", max_length=30, unique=True)
    description = models.TextField("描述", blank=True)
    permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="custom_roles",
        verbose_name="权限",
    )
    is_system = models.BooleanField("系统角色(不可删)", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """用户扩展信息 - 关联主组织"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="用户"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
        verbose_name="主组织",
    )
    phone = models.CharField("手机号", max_length=20, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "用户档案"
        verbose_name_plural = "用户档案"

    def __str__(self):
        return self.user.username


class UserOrganizationRole(models.Model):
    """用户-组织-角色 关联（支持用户在多个组织拥有不同角色）"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="org_roles",
        verbose_name="用户",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name="组织",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_orgs",
        verbose_name="角色",
    )
    is_primary = models.BooleanField("主组织", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "用户组织角色"
        verbose_name_plural = "用户组织角色"
        unique_together = [["user", "organization", "role"]]

    def __str__(self):
        return f"{self.user.username} @ {self.organization.name} ({self.role.name})"

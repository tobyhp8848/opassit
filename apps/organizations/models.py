"""
组织架构模型
三层结构：总公司、子公司、子公司部门
"""
from django.db import models


class Organization(models.Model):
    """组织/机构 - 总公司、子公司、子公司部门"""

    class OrgType(models.TextChoices):
        HEADQUARTERS = "headquarters", "总公司"
        SUBSIDIARY = "subsidiary", "子公司"
        DEPARTMENT = "department", "子公司部门"

    name = models.CharField("组织名称", max_length=100)
    code = models.CharField("组织编码", max_length=50, unique=True, null=True, blank=True)
    org_type = models.CharField(
        "组织类型",
        max_length=20,
        choices=OrgType.choices,
        default=OrgType.HEADQUARTERS,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="上级组织",
    )
    description = models.TextField("描述", blank=True)
    is_active = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "组织"
        verbose_name_plural = "组织"
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"

    def get_ancestors(self):
        """获取所有上级组织"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """获取所有下级组织"""
        return Organization.objects.filter(parent=self)

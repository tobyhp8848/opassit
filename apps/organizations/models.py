"""
组织架构模型
支持：单公司、集团与分子公司、总代理商与子代理商
"""
from django.db import models


class Organization(models.Model):
    """组织/机构 - 支持集团、分子公司、总代、子代层级"""

    class OrgType(models.TextChoices):
        COMPANY = "company", "单公司/单位"
        GROUP = "group", "集团公司"
        SUBSIDIARY = "subsidiary", "分子公司"
        DISTRIBUTOR = "distributor", "总代理商"
        SUB_DISTRIBUTOR = "sub_distributor", "子代理商"
        THIRD_DISTRIBUTOR = "third_distributor", "第三级代理"
        FOURTH_DISTRIBUTOR = "fourth_distributor", "第四级代理"

    name = models.CharField("组织名称", max_length=100)
    code = models.CharField("组织编码", max_length=50, unique=True, null=True, blank=True)
    org_type = models.CharField(
        "组织类型",
        max_length=20,
        choices=OrgType.choices,
        default=OrgType.COMPANY,
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

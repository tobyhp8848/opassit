from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Organization


class OrganizationInline(admin.TabularInline):
    """下级组织内联编辑"""
    model = Organization
    fk_name = "parent"
    extra = 0
    fields = ["name", "code", "org_type", "is_active"]
    verbose_name = "下级组织"
    verbose_name_plural = "下级组织"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "org_type_badge",
        "parent_link",
        "children_count",
        "is_active_badge",
        "created_at",
    ]
    list_display_links = ["name"]
    list_filter = ["org_type", "is_active"]
    search_fields = ["name", "code", "description"]
    list_per_page = 20
    list_select_related = ["parent"]
    raw_id_fields = ["parent"]
    inlines = [OrganizationInline]
    date_hierarchy = "created_at"
    ordering = ["parent__code", "code", "name"]

    fieldsets = (
        ("基本信息", {
            "fields": ("name", "code", "org_type", "parent", "description"),
        }),
        ("状态", {
            "fields": ("is_active",),
        }),
    )

    def org_type_badge(self, obj):
        colors = {
            "company": "secondary",
            "group": "primary",
            "subsidiary": "info",
            "distributor": "success",
            "sub_distributor": "warning",
            "third_distributor": "info",
            "fourth_distributor": "secondary",
        }
        color = colors.get(obj.org_type, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_org_type_display(),
        )

    org_type_badge.short_description = "组织类型"

    def parent_link(self, obj):
        if not obj.parent:
            return mark_safe('<span class="text-muted">— 顶级</span>')
        url = reverse("admin:organizations_organization_change", args=[obj.parent_id])
        return format_html('<a href="{}">{}</a>', url, obj.parent.name)

    parent_link.short_description = "上级组织"

    def children_count(self, obj):
        count = obj.children.count()
        if count == 0:
            return format_html('<span class="text-muted">0</span>')
        url = reverse("admin:organizations_organization_changelist") + f"?parent__id__exact={obj.pk}"
        return format_html('<a href="{}">{} 个</a>', url, count)

    children_count.short_description = "下级数量"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span class="badge bg-success">启用</span>')
        return format_html('<span class="badge bg-danger">停用</span>')

    is_active_badge.short_description = "状态"

    @admin.action(description="启用选中组织")
    def enable_organizations(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"已启用 {updated} 个组织")

    @admin.action(description="停用选中组织")
    def disable_organizations(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"已停用 {updated} 个组织")

    actions = [enable_organizations, disable_organizations]

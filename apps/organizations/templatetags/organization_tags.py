from django import template

register = template.Library()


@register.filter
def org_badge_color(org_type):
    colors = {
        "company": "secondary",
        "group": "primary",
        "subsidiary": "info",
        "distributor": "success",
        "sub_distributor": "warning",
        "third_distributor": "info",
        "fourth_distributor": "secondary",
    }
    return colors.get(org_type, "secondary")

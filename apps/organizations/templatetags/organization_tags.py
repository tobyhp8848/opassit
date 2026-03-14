from django import template

register = template.Library()


@register.filter
def org_badge_color(org_type):
    colors = {
        "headquarters": "primary",
        "subsidiary": "info",
        "department": "secondary",
    }
    return colors.get(org_type, "secondary")

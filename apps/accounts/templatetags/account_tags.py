from django import template

from apps.accounts.models import UserProfile

register = template.Library()


@register.filter
def user_org(user):
    """安全获取用户主组织名称"""
    try:
        profile = user.profile
        if profile.organization:
            return profile.organization.name
    except UserProfile.DoesNotExist:
        pass
    return "—"

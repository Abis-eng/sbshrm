from django import template
from core.company_utils import has_feature_access, is_super_admin, is_company_admin, get_user_company

register = template.Library()

@register.filter
def dict_get(d, key):
    if d is None:
        return None
    return d.get(key)

@register.filter
def attr(obj, attr_name):
    return getattr(obj, attr_name)

@register.simple_tag(takes_context=True)
def has_feature(context, feature_code):
    """Template tag to check if user has access to a feature"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return has_feature_access(request.user, feature_code)

@register.simple_tag(takes_context=True)
def is_super_admin_user(context):
    """Template tag to check if user is Super Admin"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return is_super_admin(request.user)

@register.simple_tag(takes_context=True)
def is_company_admin_user(context):
    """Template tag to check if user is Company Admin"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return is_company_admin(request.user)

@register.simple_tag(takes_context=True)
def get_user_company_tag(context):
    """Template tag to get user's company"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return None
    return get_user_company(request.user) 
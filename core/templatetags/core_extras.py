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

@register.simple_tag(takes_context=True)
def format_currency(context, amount):
    """Format amount with currency symbol and separators"""
    currency_symbol = context.get('currency_symbol', '$')
    thousand_sep = context.get('thousand_separator', ',')
    decimal_sep = context.get('decimal_separator', '.')
    
    try:
        amount = float(amount)
        # Format with thousand separator
        formatted = f"{amount:,.2f}".replace(',', thousand_sep).replace('.', decimal_sep)
        # Handle decimal separator properly
        if decimal_sep != '.':
            parts = formatted.split('.')
            if len(parts) == 2:
                formatted = f"{parts[0].replace(',', thousand_sep)}{decimal_sep}{parts[1]}"
        return f"{currency_symbol}{formatted}"
    except (ValueError, TypeError):
        return f"{currency_symbol}0{decimal_sep}00"

@register.simple_tag(takes_context=True)
def get_currency_symbol(context):
    """Get currency symbol from context"""
    return context.get('currency_symbol', '$') 
"""
Context Processors for Company and Feature Access
Adds company context to all templates
"""
from .company_utils import get_company_context
from .models import LocalizationSettings


def company_context(request):
    """Add company context to all templates"""
    context = {}
    if request.user.is_authenticated:
        company_context_data = get_company_context(request.user)
        context.update(company_context_data)
    else:
        context.update({
            'user_company': None,
            'is_super_admin': False,
            'is_company_admin': False,
        })
    
    # Add currency settings to all templates
    try:
        loc_settings = LocalizationSettings.objects.first()
        if loc_settings:
            context['currency_symbol'] = loc_settings.currency_symbol
            context['currency_code'] = loc_settings.currency
            context['thousand_separator'] = loc_settings.thousand_separator
            context['decimal_separator'] = loc_settings.decimal_separator
        else:
            # Default values if no settings exist
            context['currency_symbol'] = '₨'
            context['currency_code'] = 'PKR'
            context['thousand_separator'] = ','
            context['decimal_separator'] = '.'
    except:
        context['currency_symbol'] = '₨'
        context['currency_code'] = 'PKR'
        context['thousand_separator'] = ','
        context['decimal_separator'] = '.'
    
    return context


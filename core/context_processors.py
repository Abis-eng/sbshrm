"""
Context Processors for Company and Feature Access
Adds company context to all templates
"""
from .company_utils import get_company_context


def company_context(request):
    """Add company context to all templates"""
    if request.user.is_authenticated:
        return get_company_context(request.user)
    return {
        'user_company': None,
        'is_super_admin': False,
        'is_company_admin': False,
    }


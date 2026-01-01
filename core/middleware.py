"""
Middleware for Company-based Data Isolation
Ensures all data queries are filtered by company
"""
from django.utils.deprecation import MiddlewareMixin
from .company_utils import get_user_company, is_super_admin


class CompanyIsolationMiddleware(MiddlewareMixin):
    """
    Middleware to set company context for all requests
    This ensures data isolation at the request level
    """
    
    def process_request(self, request):
        """Set company context on request object"""
        if request.user.is_authenticated:
            if is_super_admin(request.user):
                request.company = None  # Super Admin sees all
            else:
                request.company = get_user_company(request.user)
        else:
            request.company = None
        
        return None


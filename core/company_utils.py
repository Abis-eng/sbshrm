"""
Company and Feature Access Control Utilities
Provides decorators and helper functions for multi-tenant feature access
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied


def get_user_company(user):
    """Get the company for a user"""
    if not user.is_authenticated:
        return None
    try:
        if hasattr(user, 'profile'):
            return user.profile.company
    except Exception:
        pass
    return None


def is_super_admin(user):
    """Check if user is Super Admin"""
    return user.is_authenticated and user.is_superuser


def is_company_admin(user):
    """Check if user is a Company Admin"""
    if not user.is_authenticated:
        return False
    try:
        if hasattr(user, 'profile'):
            return user.profile.is_company_admin
    except Exception:
        pass
    return False


def has_feature_access(user, feature_code):
    """Check if user has access to a feature"""
    if is_super_admin(user):
        return True  # Super Admin has access to all features
    
    if not user.is_authenticated:
        return False
    
    try:
        if hasattr(user, 'profile'):
            return user.profile.has_feature_access(feature_code)
    except Exception:
        pass
    
    return False


def require_feature(feature_code):
    """
    Decorator to require feature access for a view
    Usage: @require_feature('employees')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not has_feature_access(request.user, feature_code):
                messages.error(request, f"You don't have access to this feature.")
                return HttpResponseForbidden("Access Denied: You don't have permission to access this feature.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def require_company_admin(view_func):
    """
    Decorator to require Company Admin or Super Admin access
    Usage: @require_company_admin
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not (is_super_admin(request.user) or is_company_admin(request.user)):
            messages.error(request, "You must be a Company Admin to access this page.")
            return HttpResponseForbidden("Access Denied: Company Admin access required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def filter_by_company(queryset, user):
    """
    Filter a queryset by user's company
    Super Admins see all, Company Admins and Employees see only their company's data
    """
    if is_super_admin(user):
        return queryset  # Super Admin sees all
    
    company = get_user_company(user)
    if company:
        # Filter by company field if it exists
        if hasattr(queryset.model, 'company'):
            return queryset.filter(company=company)
        # For models without direct company field, filter through related models
        # This is a fallback - specific views should handle this properly
    return queryset.none()  # No company = no data


def get_company_context(user):
    """Get company context for templates"""
    company = get_user_company(user)
    return {
        'user_company': company,
        'is_super_admin': is_super_admin(user),
        'is_company_admin': is_company_admin(user),
    }


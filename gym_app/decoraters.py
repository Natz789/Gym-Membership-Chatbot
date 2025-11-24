from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    """Decorator to restrict access to admin users only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if not request.user.is_admin():
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    """Decorator to restrict access to staff and admin users"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if not request.user.is_staff_or_admin():
            messages.error(request, 'Access denied. Staff privileges required.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def member_required(view_func):
    """Decorator to restrict access to member users only"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        if request.user.role != 'member':
            messages.error(request, 'Access denied. Members only.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
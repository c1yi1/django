from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserProfile


def role_required(*allowed_roles):
    """角色权限装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, '请先登录')
                return redirect('accounts:login')
            
            try:
                profile = request.user.profile
                user_role = profile.role
            except UserProfile.DoesNotExist:
                messages.error(request, '用户信息不完整，请联系管理员')
                return redirect('accounts:login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if user_role not in allowed_roles:
                messages.error(request, '您没有权限访问此页面')
                return redirect('accounts:home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def student_required(view_func):
    """学生权限装饰器"""
    return role_required('student')(view_func)


def teacher_required(view_func):
    """教师权限装饰器"""
    return role_required('teacher', 'admin')(view_func)


def admin_required(view_func):
    """管理员权限装饰器"""
    return role_required('admin')(view_func)







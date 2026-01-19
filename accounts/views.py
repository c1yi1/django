from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import transaction
from django.http import JsonResponse
import random
from .models import UserProfile


def generate_captcha():
    """生成4位数字验证码"""
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])


@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_view(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('/')
    
    # 生成验证码（GET请求或验证失败时）
    if request.method == 'GET' or 'captcha' not in request.session:
        captcha = generate_captcha()
        request.session['captcha'] = captcha
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        captcha_input = request.POST.get('captcha', '').strip()
        captcha_session = request.session.get('captcha', '')
        
        # 验证验证码
        if captcha_input != captcha_session:
            messages.error(request, '验证码错误，请重新输入')
            # 重新生成验证码
            request.session['captcha'] = generate_captcha()
            return render(request, 'accounts/login.html', {
                'captcha': request.session['captcha']
            })
        
        if not username or not password:
            messages.error(request, '请输入用户名和密码')
            request.session['captcha'] = generate_captcha()
            return render(request, 'accounts/login.html', {
                'captcha': request.session['captcha']
            })
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            remember = request.POST.get('remember')
            if remember:
                request.session.set_expiry(2592000)
            else:
                request.session.set_expiry(0)
            
            # 登录成功后清除验证码
            if 'captcha' in request.session:
                del request.session['captcha']
            
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误，请重试')
            # 验证失败后重新生成验证码
            request.session['captcha'] = generate_captcha()
    
    return render(request, 'accounts/login.html', {
        'captcha': request.session.get('captcha', generate_captcha())
    })


@require_http_methods(["GET"])
def refresh_captcha(request):
    """刷新验证码"""
    captcha = generate_captcha()
    request.session['captcha'] = captcha
    return JsonResponse({'captcha': captcha})


@login_required
def home_view(request):
    """首页视图"""
    try:
        profile = request.user.profile
        if request.user.is_superuser and profile.role != 'admin':
            profile.role = 'admin'
            profile.save()
        role = profile.role
        role_display = profile.get_role_display()
    except UserProfile.DoesNotExist:
        if request.user.is_superuser:
            role = 'admin'
            role_display = '管理员'
        else:
            role = 'student'
            role_display = '学生'
        profile = UserProfile.objects.create(user=request.user, role=role)
    
    return render(request, 'accounts/home.html', {
        'user': request.user,
        'profile': profile,
        'role': role,
        'role_display': role_display,
    })


@require_http_methods(["POST"])
@login_required
def logout_view(request):
    """用户登出视图"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('accounts:login')

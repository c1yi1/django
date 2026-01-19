from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('captcha/refresh/', views.refresh_captcha, name='refresh_captcha'),
    path('', views.home_view, name='home'),
]







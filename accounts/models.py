from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """用户扩展信息模型"""
    ROLE_CHOICES = [
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    ]
    
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name='角色')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    student_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='学号')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True, verbose_name='性别')
    major = models.CharField(max_length=100, blank=True, null=True, verbose_name='专业')
    grade = models.CharField(max_length=20, blank=True, null=True, verbose_name='年级')
    class_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='班级')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'
        db_table = 'user_profile'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """当创建新用户时，自动创建用户信息"""
    if created:
        role = 'admin' if instance.is_superuser else 'student'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})

from django.contrib import admin

# Register your models here.
# exam/admin.py
from django.contrib import admin
from .models import Category, Question, Exam, Paper, PaperQuestion, ExamAttempt, Answer

admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Exam)
admin.site.register(Paper)
admin.site.register(PaperQuestion)
admin.site.register(ExamAttempt)
admin.site.register(Answer)
from django.urls import path
from . import views

app_name = 'exam'

urlpatterns = [
    # 学生考试相关
    path('student/exams/', views.exam_list_student_view, name='exam_list_student'),
    path('my-wrongs/', views.my_wrongs_view, name='my_wrongs'),
    path('my-wrongs/<int:wrong_id>/', views.wrong_question_detail_view, name='wrong_question_detail'),
    path('my-favorites/', views.my_favorites_view, name='my_favorites'),
    path('practice/', views.practice_home_view, name='practice_home'),
    path('practice/api/questions/', views.practice_questions_api, name='practice_questions_api'),
    path('practice/api/questions/<int:question_id>/check/', views.practice_check_api, name='practice_check_api'),
    path('practice/api/favorites/<int:question_id>/toggle/', views.favorite_toggle_api, name='favorite_toggle_api'),
    path('exams/<int:exam_id>/start/', views.start_exam_view, name='start_exam'),
    path('attempts/<int:attempt_id>/', views.take_exam_view, name='take_exam'),
    path('attempts/<int:attempt_id>/result/', views.exam_result_view, name='exam_result'),
    path('my-scores/', views.my_scores_view, name='my_scores'),
    path('my-mistakes/', views.my_mistakes_view, name='my_mistakes'),
    path('answers/<int:answer_id>/favorite/', views.toggle_favorite_answer_view, name='toggle_favorite_answer'),
    
    # 后台首页 / 仪表盘（教师和管理员）
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # 题库管理（教师和管理员）
    path('questions/', views.question_list_view, name='question_list'),
    path('questions/create/', views.question_create_view, name='question_create'),
    path('questions/import/', views.question_import_view, name='question_import'),
    path('questions/template/<str:file_type>/', views.download_template_view, name='download_template'),
    path('questions/<int:question_id>/', views.question_detail_view, name='question_detail'),
    path('questions/<int:question_id>/edit/', views.question_edit_view, name='question_edit'),
    path('questions/<int:question_id>/delete/', views.question_delete_view, name='question_delete'),
    
    # 考试管理（教师和管理员）
    path('exams/', views.exam_list_view, name='exam_list'),
    path('exams/create/', views.exam_create_view, name='exam_create'),
    path('exams/<int:exam_id>/', views.exam_detail_view, name='exam_detail'),
    path('exams/<int:exam_id>/edit/', views.exam_edit_view, name='exam_edit'),
    path('exams/<int:exam_id>/delete/', views.exam_delete_view, name='exam_delete'),
    path('exams/<int:exam_id>/attempts/', views.exam_attempt_list_view, name='exam_attempt_list'),
    path('exams/<int:exam_id>/statistics/', views.exam_statistics_view, name='exam_statistics'),
    path('exams/statistics/', views.exam_statistics_entry_view, name='exam_statistics_entry'),
    
    # 试卷管理
    path('exams/<int:exam_id>/papers/create/', views.paper_create_view, name='paper_create'),
    path('papers/<int:paper_id>/', views.paper_detail_view, name='paper_detail'),
    path('papers/<int:paper_id>/edit-questions/', views.paper_edit_questions_view, name='paper_edit_questions'),
    
    # 答卷批阅
    path('attempts/<int:attempt_id>/review/', views.attempt_review_view, name='attempt_review'),

    # 前端反作弊 / 行为日志上报接口
    path('api/attempts/<int:attempt_id>/log-event/', views.log_exam_event_view, name='log_exam_event'),
]


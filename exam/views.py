from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Max, Min, Count
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.decorators import teacher_required, admin_required
from accounts.models import UserProfile
from .models import Exam, Paper, PaperQuestion, ExamAttempt, Answer, Question, Category, ExamActivityLog, WrongQuestion, FavoriteQuestion
from .utils import parse_excel_file, parse_csv_file, parse_json_file, import_questions_from_data
import json
from django.http import JsonResponse, HttpResponse
import base64
import numpy as np
import cv2
from django.views.decorators.csrf import csrf_exempt
import os

def log_wrong_question(user, question, source='exam'):
    """记录错题（客观题为主），重复错误叠加计数"""
    if not user or not question:
        return
    obj, created = WrongQuestion.objects.get_or_create(
        user=user,
        question=question,
        defaults={'source': source}
    )
    if not created:
        obj.wrong_count += 1
        obj.source = source or obj.source
    obj.save(update_fields=['wrong_count', 'source', 'last_wrong_at'])


@login_required
def exam_list_student_view(request):
    """学生考试列表视图 - 显示可参加的考试"""
    try:
        now = timezone.now()
        # 查询已发布的考试，且未结束的（结束时间大于等于当前时间）
        # 包括：已发布但未开始的、进行中的、已发布但未结束的
        exams = Exam.objects.filter(
            status__in=['published', 'ongoing'],
            end_time__gte=now  # 只要还没结束就可以看到
        ).order_by('-start_time')
        
        # 获取用户每个考试的尝试次数和最高分
        exam_attempts_info = {}
        for exam in exams:
            submitted_attempts = ExamAttempt.objects.filter(
                exam=exam,
                user=request.user,
                status__in=['submitted', 'timeout']
            ).order_by('-total_score')
            
            attempts_count = submitted_attempts.count()
            max_score = submitted_attempts.first().total_score if submitted_attempts.exists() else None
            
            exam_attempts_info[exam.id] = {
                'attempts_count': attempts_count,
                'max_attempts': exam.max_attempts,
                'can_attempt': attempts_count < exam.max_attempts,
                'max_score': max_score,
            }
        
        # 为每个考试计算是否可用（可以开始答题）
        exam_availability = {}
        for exam in exams:
            exam_availability[exam.id] = exam.is_available()
        
        context = {
            'exams': exams,
            'exam_attempts_info': exam_attempts_info,
            'exam_availability': exam_availability,
            'now': now,  # 传递当前时间给模板，方便调试
        }
        return render(request, 'exam/exam_list_student.html', context)
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        messages.error(request, f'加载考试列表失败：{error_msg}')
        return render(request, 'exam/exam_list_student.html', {
            'exams': [],
            'exam_attempts_info': {},
            'exam_availability': {},
            'now': timezone.now(),
        })


@login_required
def my_wrongs_view(request):
    wrongs = WrongQuestion.objects.filter(user=request.user).select_related('question', 'question__category')
    return render(request, 'exam/my_wrongs.html', {'wrongs': wrongs})


@login_required
def wrong_question_detail_view(request, wrong_id):
    """错题详情视图"""
    wrong = get_object_or_404(WrongQuestion, id=wrong_id, user=request.user)
    question = wrong.question
    
    # 获取用户在这道题上的错误记录（如果有答案记录）
    user_answers = []
    if wrong.source == 'exam':
        # 从考试答案中查找
        attempts = ExamAttempt.objects.filter(user=request.user, status__in=['submitted', 'timeout'])
        for attempt in attempts:
            answer = attempt.answers.filter(question=question).first()
            if answer and not answer.is_correct:
                user_answers.append({
                    'user_answer': answer.user_answer,
                    'exam_title': attempt.exam.title,
                    'submit_time': attempt.submit_time,
                })
    
    context = {
        'wrong': wrong,
        'question': question,
        'user_answers': user_answers,
    }
    return render(request, 'exam/wrong_question_detail.html', context)


@login_required
def my_favorites_view(request):
    favs = FavoriteQuestion.objects.filter(user=request.user).select_related('question', 'question__category')
    return render(request, 'exam/my_favorites.html', {'favs': favs})


@login_required
@require_http_methods(["GET"])
def practice_home_view(request):
    """
    学生在线练习首页：选择条件后前端通过 API 拉取题目并即时判分。
    """
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories,
        'question_types': Question.QUESTION_TYPES,
        'difficulties': Question.DIFFICULTY_LEVELS,
    }
    return render(request, 'exam/practice.html', context)


@login_required
@require_http_methods(["GET"])
def practice_questions_api(request):
    """
    获取练习题列表（客观题），支持分类/难度/题型过滤。
    """
    try:
        limit = int(request.GET.get('limit', 10))
    except ValueError:
        limit = 10
    limit = max(1, min(limit, 50))

    qs = Question.objects.filter(is_active=True).exclude(question_type='subjective')

    category_id = request.GET.get('category')
    if category_id:
        qs = qs.filter(category_id=category_id)

    difficulty = request.GET.get('difficulty')
    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    question_type = request.GET.get('question_type')
    if question_type:
        qs = qs.filter(question_type=question_type)

    questions = qs.order_by('?')[:limit]
    favorite_ids = set(FavoriteQuestion.objects.filter(user=request.user, question_id__in=[q.id for q in questions]).values_list('question_id', flat=True))

    def serialize_options(opt):
        if isinstance(opt, dict):
            return [{'key': k, 'text': v} for k, v in sorted(opt.items())]
        if isinstance(opt, list):
            return [{'key': str(idx + 1), 'text': v} for idx, v in enumerate(opt)]
        return []

    data = []
    for q in questions:
        image_url = ''
        if q.image:
            try:
                image_url = request.build_absolute_uri(q.image.url)
            except Exception:
                image_url = q.image.url
        data.append({
            'id': q.id,
            'title': q.title,
            'content': q.content,
            'question_type': q.question_type,
            'difficulty': q.get_difficulty_display(),
            'category': q.category.name if q.category else '',
            'options': serialize_options(q.options),
            'image': image_url,
            'is_favorited': q.id in favorite_ids,
        })

    return JsonResponse({'success': True, 'questions': data})


@login_required
@require_http_methods(["POST"])
def practice_check_api(request, question_id):
    """
    判分接口（练习模式），只支持客观题。
    """
    question = get_object_or_404(Question, id=question_id, is_active=True)
    if question.question_type == 'subjective':
        return JsonResponse({'success': False, 'message': '暂不支持主观题练习判分'}, status=400)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = {}

    user_answer = payload.get('answer', '')
    is_correct = question.check_answer(user_answer)
    correct_answer = question.get_correct_answer_list()
    if not is_correct:
        log_wrong_question(request.user, question, source='practice')

    return JsonResponse({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': correct_answer,
        'explanation': question.explanation or '',
    })


@login_required
@require_http_methods(["POST"])
def favorite_toggle_api(request, question_id):
    """练习/题库收藏切换"""
    question = get_object_or_404(Question, id=question_id, is_active=True)
    fav, created = FavoriteQuestion.objects.get_or_create(user=request.user, question=question)
    if created:
        return JsonResponse({'success': True, 'favorited': True})
    fav.delete()
    return JsonResponse({'success': True, 'favorited': False})


@login_required
@require_http_methods(["GET", "POST"])
def start_exam_view(request, exam_id):
    """开始考试视图"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # 检查考试是否可用
    if not exam.is_available():
        messages.error(request, '该考试当前不可用')
        return redirect('exam:exam_list_student')

    # 如果已经有一份“进行中”的答题记录，则直接续答，防止通过退出/重新进入来“重置计时”（反作弊）
    existing_attempt = ExamAttempt.objects.filter(
        exam=exam,
        user=request.user,
        status='in_progress'
    ).order_by('-start_time').first()
    if existing_attempt:
        messages.info(request, '您已有一份正在进行的答卷，系统已为您继续该答卷。')
        return redirect('exam:take_exam', attempt_id=existing_attempt.id)
    
    # 检查是否超过最大尝试次数
    # 这里统计“已提交”和“超时”的记录，和学生考试列表逻辑保持一致
    attempts_count = ExamAttempt.objects.filter(
        exam=exam,
        user=request.user,
        status__in=['submitted', 'timeout']
    ).count()
    if attempts_count >= exam.max_attempts:
        messages.error(request, f'您已达到最大尝试次数（{exam.max_attempts}次）')
        return redirect('exam:exam_list_student')
    
    # 获取试卷（使用第一个试卷）
    paper = exam.papers.first()
    if not paper:
        messages.error(request, '该考试还没有试卷')
        return redirect('exam:exam_list_student')
    
    if request.method == 'POST':
        # 创建答题记录
        attempt = ExamAttempt.objects.create(
            exam=exam,
            paper=paper,
            user=request.user,
            status='in_progress'
        )
        return redirect('exam:take_exam', attempt_id=attempt.id)
    
    # 显示确认页面
    return render(request, 'exam/start_exam.html', {
        'exam': exam,
        'paper': paper,
        'attempts_count': attempts_count,
    })


@login_required
@require_http_methods(["POST"])
def log_exam_event_view(request, attempt_id):
    """
    前端考试行为事件上报接口：
    - 心跳（保持在线）
    - 切屏 / 最小化 等可疑行为
    当同一次答卷的可疑行为次数超过阈值时，强制结束本次考试。
    """
    try:
        attempt = ExamAttempt.objects.select_related('exam', 'user').get(
            id=attempt_id,
            user=request.user
        )
    except ExamAttempt.DoesNotExist:
        return JsonResponse({'success': False, 'message': '答题记录不存在或无权访问'}, status=404)

    # 只对进行中的答卷做处理
    if attempt.status != 'in_progress':
        return JsonResponse({'success': False, 'message': '当前答卷已结束'}, status=400)

    # 解析前端 JSON 数据
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        payload = {}

    event_type = payload.get('event_type', 'heartbeat')
    detail = payload.get('detail', '')

    # 记录日志
    ExamActivityLog.objects.create(
        attempt=attempt,
        user=request.user,
        event_type=event_type,
        detail=detail or None,
    )

    # 定义哪些事件属于“可疑行为”
    suspicious_events = {'visibility_hidden', 'window_blur'}

    response_data = {'success': True}

    if event_type in suspicious_events:
        # 统计当前 attempt 下的可疑事件次数
        suspicious_count = attempt.activity_logs.filter(
            event_type__in=list(suspicious_events)
        ).count()

        # 可以根据需要调整阈值，例如 5 次
        MAX_SUSPICIOUS_PER_ATTEMPT = 5

        if suspicious_count >= MAX_SUSPICIOUS_PER_ATTEMPT:
            # 强制结束本次考试（视为超时处理）
            attempt.status = 'timeout'
            attempt.submit_time = timezone.now()
            # 计算当前得分
            for answer in attempt.answers.all():
                answer.check_and_score()
            attempt.calculate_score()
            attempt.save()  # 确保保存状态
            # 记录强制提交事件
            ExamActivityLog.objects.create(
                attempt=attempt,
                user=request.user,
                event_type='force_submit',
                detail=f'达到可疑行为阈值({MAX_SUSPICIOUS_PER_ATTEMPT}次)，系统强制提交',
            )
            response_data.update({
                'force_submit': True,
                'message': f'检测到{MAX_SUSPICIOUS_PER_ATTEMPT}次切屏/最小化，本次考试已被系统强制结束。'
            })
        else:
            response_data.update({
                'force_submit': False,
                'suspicious_count': suspicious_count,
                'left_count': MAX_SUSPICIOUS_PER_ATTEMPT - suspicious_count,
            })

    return JsonResponse(response_data)


@csrf_exempt
def upload_frame(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': 'Only POST allowed'})

    try:
        # 1. 解析数据
        data = json.loads(request.body)
        image_str = data.get('image')
        # attempt_id = data.get('attempt_id') # 暂时不用，以后可以用来存日志

        if not image_str:
            return JsonResponse({'status': 'error', 'msg': 'No image'})

        # 2. 解码图片
        header, encoded = image_str.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # ==================== 🕵️‍♂️ 核心反作弊逻辑 ====================

        # A. 准备人脸检测器 (OpenCV 自带模型)
        # 注意：第一次运行时，OpenCV 会自动查找这个 XML 文件
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # B. 转为灰度图 (检测更快)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # C. 检测人脸
        # scaleFactor=1.1, minNeighbors=5 是标准参数
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        face_count = len(faces)

        # D. 判定逻辑
        status = 'success'
        msg = '正常'

        if face_count == 0:
            status = 'alert'
            msg = '⚠️ 警告：未检测到考生人脸！请保持在摄像头范围内。'
            print(f"❌ [监控] 异常：无人脸")

        elif face_count > 1:
            status = 'alert'
            msg = '⚠️ 严重警告：检测到多人！请确保独立完成考试。'
            print(f"❌ [监控] 异常：多人 ({face_count}人)")

        else:
            # face_count == 1
            print(f"✅ [监控] 正常：检测到 1 人")

        # ==========================================================

        return JsonResponse({'status': status, 'msg': msg})

    except Exception as e:
        print(f"❌ 处理出错: {e}")
        return JsonResponse({'status': 'error', 'msg': str(e)})
@login_required
@require_http_methods(["GET", "POST"])
def take_exam_view(request, attempt_id):
    """答题视图"""
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    
    # 检查是否是自己的答题记录
    if attempt.user != request.user:
        messages.error(request, '无权访问')
        return redirect('exam:exam_list_student')
    
    # 检查是否已提交
    if attempt.status != 'in_progress':
        return redirect('exam:exam_result', attempt_id=attempt.id)
    
    # 检查是否超时
    elapsed_time = attempt.get_duration()
    exam_duration_seconds = attempt.exam.duration * 60
    
    if elapsed_time >= exam_duration_seconds:
        # 自动提交
        attempt.status = 'timeout'
        attempt.submit_time = timezone.now()
        attempt.calculate_score()
        messages.warning(request, '考试时间已到，系统已自动提交')
        return redirect('exam:exam_result', attempt_id=attempt.id)
    
    if request.method == 'POST':
        # 保存答案
        paper_questions = attempt.paper.paper_questions.all().select_related('question')
        
        for pq in paper_questions:
            question_id = str(pq.question.id)
            
            if pq.question.question_type == 'multiple':
                # 多选题
                user_answers = request.POST.getlist(f'answer_{question_id}')
                user_answer = ','.join(sorted(user_answers)) if user_answers else ''
            else:
                # 单选题 / 判断题 / 主观题：统一用单一文本字段接收
                user_answer = request.POST.get(f'answer_{question_id}', '').strip()
            
            # 创建或更新答案
            if user_answer:  # 只保存有答案的
                answer, created = Answer.objects.get_or_create(
                    attempt=attempt,
                    question=pq.question,
                    defaults={'user_answer': user_answer}
                )
                if not created:
                    answer.user_answer = user_answer
                    answer.save()
        
        # 检查是否是提交操作
        if 'submit' in request.POST:
            # 计算分数
            for answer in attempt.answers.all():
                answer.check_and_score()
                # 记录错题（客观题）
                if answer.question.question_type != 'subjective' and not answer.is_correct:
                    log_wrong_question(request.user, answer.question, source='exam')
            
            attempt.calculate_score()
            attempt.status = 'submitted'
            attempt.submit_time = timezone.now()
            attempt.save()
            
            messages.success(request, '考试已提交！')
            return redirect('exam:exam_result', attempt_id=attempt.id)
        else:
            # 自动保存（不显示消息，避免干扰）
            pass
    
    # GET请求，显示答题页面
    # 先获取所有题目，然后手动排序确保顺序正确
    # 使用select_related和prefetch_related确保加载完整的question数据
    paper_questions_queryset = attempt.paper.paper_questions.all().select_related('question', 'question__category')
    
    # 获取已保存的答案
    saved_answers = {ans.question_id: ans.user_answer for ans in attempt.answers.all()}
    
    remaining_time = exam_duration_seconds - elapsed_time
    
    # 获取用户信息
    try:
        user_profile = request.user.profile
    except:
        user_profile = None
    
    # 确保题目按order排序，如果order为0则按id排序
    paper_questions = list(paper_questions_queryset)
    paper_questions.sort(key=lambda pq: (pq.order if pq.order > 0 else 999, pq.id))
    
    # 按题目类型分组，同时记录在排序后列表中的索引
    questions_by_type = {
        'single': [],
        'multiple': [],
        'judge': [],
        'subjective': [],
    }
    
    for index, pq in enumerate(paper_questions):
        question_type = pq.question.question_type
        display_order = pq.order if pq.order > 0 else index + 1
        if question_type in questions_by_type:
            questions_by_type[question_type].append({
                'pq': pq,
                'index': index,          # 在排序后列表中的位置索引（与中间题卡一一对应）
                'order': display_order,  # 显示的题号（全卷统一编号）
                'question_id': pq.question.id,  # 题目ID，用于匹配
            })
    
    # 为了让左侧导航更直观，将每个题型内部按题号升序排序
    for q_type in questions_by_type.keys():
        questions_by_type[q_type].sort(key=lambda item: item['order'])
    
    context = {
        'attempt': attempt,
        'exam': attempt.exam,
        'paper': attempt.paper,
        'paper_questions': paper_questions,
        'saved_answers': saved_answers,
        'remaining_time': remaining_time,
        'user_profile': user_profile,
        'questions_by_type': questions_by_type,
    }
    
    return render(request, 'exam/take_exam.html', context)


@login_required
def exam_result_view(request, attempt_id):
    """考试结果视图"""
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    
    if attempt.status == 'in_progress':
        return redirect('exam:take_exam', attempt_id=attempt.id)
    
    # 获取答案详情，按试卷中的题目顺序排序
    paper_questions = attempt.paper.paper_questions.all().select_related('question').order_by('order', 'id')
    question_order_map = {pq.question_id: pq.order for pq in paper_questions}
    
    # 获取答案并按题目顺序排序
    answers = attempt.answers.all().select_related('question')
    answers_list = list(answers)
    answers_list.sort(key=lambda a: question_order_map.get(a.question_id, 999))
    
    # 按题型做简单成绩分析（单选 / 多选 / 判断 / 主观）
    type_stats = {}
    # 先初始化每种题型的总题数和满分
    for pq in paper_questions:
        q_type = pq.question.question_type
        if q_type not in type_stats:
            type_stats[q_type] = {
                'label': pq.question.get_question_type_display(),
                'question_count': 0,
                'full_score': 0,
                'got_score': 0,
                'correct_count': 0,  # 主观题一般不统计对错次数
            }
        type_stats[q_type]['question_count'] += 1
        type_stats[q_type]['full_score'] += pq.score
    
    # 再累加各题型实际得分与正确数量（仅客观题）
    for ans in answers_list:
        q_type = ans.question.question_type
        if q_type not in type_stats:
            continue
        type_stats[q_type]['got_score'] += ans.score
        if q_type != 'subjective' and ans.is_correct:
            type_stats[q_type]['correct_count'] += 1
    
    context = {
        'attempt': attempt,
        'exam': attempt.exam,
        'paper': attempt.paper,
        'answers': answers_list,
        'question_order_map': question_order_map,
        'type_stats': type_stats,
    }
    
    return render(request, 'exam/exam_result.html', context)


@login_required
def my_scores_view(request):
    """我的成绩视图"""
    attempts = ExamAttempt.objects.filter(user=request.user, status='submitted').select_related('exam', 'paper').order_by('-submit_time')
    
    # 分页
    paginator = Paginator(attempts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'exam/my_scores.html', context)


@login_required
def my_mistakes_view(request):
    """我的错题集（仅提交/超时的答卷，客观题按是否正确，主观题按得分>0视为正确）"""
    answers = (
        Answer.objects
        .filter(attempt__user=request.user, attempt__status__in=['submitted', 'timeout'], is_correct=False)
        .select_related('question', 'attempt', 'attempt__exam')
        .order_by('-attempt__submit_time')
    )
    return render(request, 'exam/my_mistakes.html', {'answers': answers})


@login_required
@require_http_methods(["POST"])
def toggle_favorite_answer_view(request, answer_id):
    """收藏/取消收藏某个答案（学生端）"""
    answer = get_object_or_404(Answer, id=answer_id, attempt__user=request.user)
    answer.is_favorited = not answer.is_favorited
    answer.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'favorited': answer.is_favorited})
    messages.success(request, '已收藏' if answer.is_favorited else '已取消收藏')
    return redirect(request.META.get('HTTP_REFERER', 'exam:my_mistakes'))


# ==================== 题库管理视图（教师和管理员） ====================

@login_required
@teacher_required
def question_list_view(request):
    """题目列表视图"""
    # 批量更新（题型/难度/分类/分值/标题前缀）
    if request.method == 'POST' and request.POST.get('bulk_action') == 'update':
        selected_ids = request.POST.getlist('selected')
        if not selected_ids:
            messages.warning(request, '请先勾选要批量修改的题目')
            return redirect('exam:question_list')

        new_type = request.POST.get('bulk_question_type') or ''
        new_difficulty = request.POST.get('bulk_difficulty') or ''
        raw_category = request.POST.get('bulk_category', '')
        if raw_category == '__none':
            new_category = None
        elif raw_category:
            new_category = raw_category
        else:
            new_category = '__keep__'
        new_score_raw = request.POST.get('bulk_score', '').strip()
        title_prefix = request.POST.get('bulk_title_prefix', '').strip()
        title_replace = request.POST.get('bulk_title', '').strip()

        try:
            new_score = int(new_score_raw) if new_score_raw else None
        except ValueError:
            messages.error(request, '分值需为数字')
            return redirect('exam:question_list')

        qs = Question.objects.filter(id__in=selected_ids)
        updated = 0
        for q in qs:
            changed = False
            if title_replace:
                q.title = title_replace
                changed = True
            elif title_prefix:
                q.title = f"{title_prefix}{q.title}"
                changed = True
            if new_type:
                q.question_type = new_type
                changed = True
            if new_difficulty:
                q.difficulty = new_difficulty
                changed = True
            if new_category != '__keep__':
                q.category_id = new_category
                changed = True
            if new_score is not None:
                q.score = new_score
                changed = True
            if changed:
                q.save()
                updated += 1

        messages.success(request, f'已批量更新 {updated} 道题目')
        return redirect('exam:question_list')

    questions = Question.objects.all().select_related('category', 'created_by')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        questions = questions.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # 筛选功能
    category_id = request.GET.get('category')
    if category_id:
        questions = questions.filter(category_id=category_id)
    
    question_type = request.GET.get('type')
    if question_type:
        questions = questions.filter(question_type=question_type)
    
    difficulty = request.GET.get('difficulty')
    if difficulty:
        questions = questions.filter(difficulty=difficulty)
    
    # 分页
    paginator = Paginator(questions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_type': question_type,
        'selected_difficulty': difficulty,
    }
    
    return render(request, 'exam/question_list.html', context)


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def question_create_view(request):
    """创建题目视图"""
    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            question_type = request.POST.get('question_type')
            difficulty = request.POST.get('difficulty', 'medium')
            category_id = request.POST.get('category') or None
            score = int(request.POST.get('score', 5))
            correct_answer = request.POST.get('correct_answer', '').strip()
            explanation = request.POST.get('explanation', '').strip()
            image_file = request.FILES.get('image')
            
            # 构建选项字典
            options = {}
            if question_type in ['single', 'multiple']:
                option_keys = ['A', 'B', 'C', 'D', 'E', 'F']
                for key in option_keys:
                    option_value = request.POST.get(f'option_{key}', '').strip()
                    if option_value:
                        options[key] = option_value
            
            # 创建题目
            question = Question.objects.create(
                title=title,
                content=content,
                question_type=question_type,
                difficulty=difficulty,
                category_id=category_id,
                score=score,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                image=image_file,
                created_by=request.user
            )
            
            messages.success(request, '题目创建成功！')
            return redirect('exam:question_list')
        except Exception as e:
            messages.error(request, f'创建题目失败：{str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'exam/question_form.html', {
        'categories': categories,
        'action': 'create'
    })


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def question_edit_view(request, question_id):
    """编辑题目视图"""
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        try:
            question.title = request.POST.get('title', '').strip()
            question.content = request.POST.get('content', '').strip()
            question.question_type = request.POST.get('question_type')
            question.difficulty = request.POST.get('difficulty', 'medium')
            question.category_id = request.POST.get('category') or None
            question.score = int(request.POST.get('score', 5))
            question.correct_answer = request.POST.get('correct_answer', '').strip()
            question.explanation = request.POST.get('explanation', '').strip()
            image_file = request.FILES.get('image')
            clear_image = request.POST.get('clear_image')
            
            # 构建选项字典
            options = {}
            if question.question_type in ['single', 'multiple']:
                option_keys = ['A', 'B', 'C', 'D', 'E', 'F']
                for key in option_keys:
                    option_value = request.POST.get(f'option_{key}', '').strip()
                    if option_value:
                        options[key] = option_value
            question.options = options

            if clear_image:
                if question.image:
                    question.image.delete(save=False)
                question.image = None
            elif image_file:
                question.image = image_file
            
            question.save()
            
            messages.success(request, '题目更新成功！')
            return redirect('exam:question_list')
        except Exception as e:
            messages.error(request, f'更新题目失败：{str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'exam/question_form.html', {
        'question': question,
        'categories': categories,
        'action': 'edit'
    })


@login_required
@teacher_required
def question_delete_view(request, question_id):
    """删除题目视图"""
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, '题目已删除！')
        return redirect('exam:question_list')
    
    return render(request, 'exam/question_confirm_delete.html', {
        'question': question
    })


@login_required
def question_detail_view(request, question_id):
    """题目详情视图"""
    question = get_object_or_404(Question, id=question_id)

    # 获取用户角色
    try:
        profile = request.user.profile
        if request.user.is_superuser and profile.role != 'admin':
            profile.role = 'admin'
        role = profile.role
    except:
        if request.user.is_superuser:
            role = 'admin'
        else:
            role = 'student'

    return render(request, 'exam/question_detail.html', {
        'question': question,
        'role': role
    })


# ==================== 考试管理视图（教师和管理员） ====================

@login_required
@teacher_required
def exam_list_view(request):
    """考试列表视图（教师和管理员）"""
    exams = Exam.objects.all().select_related('created_by').order_by('-created_at')
    
    # 搜索功能
    search_query = request.GET.get('search', '')
    if search_query:
        exams = exams.filter(Q(title__icontains=search_query))
    
    # 状态筛选
    status = request.GET.get('status')
    if status:
        exams = exams.filter(status=status)
    
    # 分页
    paginator = Paginator(exams, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status,
    }
    
    return render(request, 'exam/exam_list.html', context)


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def exam_create_view(request):
    """创建考试视图"""
    if request.method == 'POST':
        try:
            exam = Exam.objects.create(
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', '').strip(),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                duration=int(request.POST.get('duration', 60)),
                total_score=int(request.POST.get('total_score', 100)),
                pass_score=int(request.POST.get('pass_score', 60)),
                max_attempts=int(request.POST.get('max_attempts', 1)),
                status=request.POST.get('status', 'draft'),
                created_by=request.user
            )
            messages.success(request, '考试创建成功！')
            return redirect('exam:exam_detail', exam_id=exam.id)
        except Exception as e:
            messages.error(request, f'创建考试失败：{str(e)}')
    
    return render(request, 'exam/exam_form.html', {
        'action': 'create'
    })


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def exam_edit_view(request, exam_id):
    """编辑考试视图"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        try:
            exam.title = request.POST.get('title', '').strip()
            exam.description = request.POST.get('description', '').strip()
            exam.start_time = request.POST.get('start_time')
            exam.end_time = request.POST.get('end_time')
            exam.duration = int(request.POST.get('duration', 60))
            exam.total_score = int(request.POST.get('total_score', 100))
            exam.pass_score = int(request.POST.get('pass_score', 60))
            exam.max_attempts = int(request.POST.get('max_attempts', 1))
            exam.status = request.POST.get('status', 'draft')
            exam.save()
            
            messages.success(request, '考试更新成功！')
            return redirect('exam:exam_detail', exam_id=exam.id)
        except Exception as e:
            messages.error(request, f'更新考试失败：{str(e)}')
    
    return render(request, 'exam/exam_form.html', {
        'exam': exam,
        'action': 'edit'
    })


@login_required
@teacher_required
def exam_detail_view(request, exam_id):
    """考试详情视图"""
    exam = get_object_or_404(Exam, id=exam_id)
    papers = exam.papers.all().order_by('-created_at')
    
    return render(request, 'exam/exam_detail.html', {
        'exam': exam,
        'papers': papers
    })


@login_required
@teacher_required
@require_http_methods(["POST"])
def exam_delete_view(request, exam_id):
    """删除考试视图（仅教师/管理员，POST 请求）"""
    exam = get_object_or_404(Exam, id=exam_id)
    title = exam.title
    try:
        exam.delete()
        messages.success(request, f'考试“{title}”已删除。')
    except Exception as e:
        messages.error(request, f'删除考试失败：{str(e)}')
    return redirect('exam:exam_list')


# ==================== 试卷管理视图 ====================

@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def paper_create_view(request, exam_id):
    """创建试卷视图"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            generate_type = request.POST.get('generate_type', 'manual')
            
            paper = Paper.objects.create(
                exam=exam,
                name=name,
                generate_type=generate_type
            )
            
            if generate_type == 'manual':
                # 手动选题
                question_ids = request.POST.getlist('questions')
                order = 1
                for question_id in question_ids:
                    question = Question.objects.get(id=question_id)
                    score = int(request.POST.get(f'score_{question_id}', question.score))
                    PaperQuestion.objects.create(
                        paper=paper,
                        question=question,
                        order=order,
                        score=score
                    )
                    order += 1
            else:
                # 随机组卷
                from .exam_utils import generate_random_paper
                rules = {
                    'single': int(request.POST.get('single_count', 0) or 0),
                    'multiple': int(request.POST.get('multiple_count', 0) or 0),
                    'judge': int(request.POST.get('judge_count', 0) or 0),
                }
                
                # 验证至少有一种题目类型
                total_count = sum(rules.values())
                if total_count == 0:
                    messages.error(request, '请至少设置一种题目的数量大于0！')
                    return redirect('exam:paper_create', exam_id=exam.id)
                
                difficulty = request.POST.get('difficulty', 'all')
                category_id = request.POST.get('category') or None
                
                try:
                    generate_random_paper(paper, rules, difficulty, category_id)
                except Exception as e:
                    messages.error(request, f'随机组卷失败：{str(e)}')
                    return redirect('exam:paper_create', exam_id=exam.id)
            
            messages.success(request, '试卷创建成功！')
            return redirect('exam:paper_detail', paper_id=paper.id)
        except Exception as e:
            messages.error(request, f'创建试卷失败：{str(e)}')
    
    # GET请求，显示创建表单
    questions = Question.objects.filter(is_active=True).select_related('category')
    
    # 筛选
    category_id = request.GET.get('category')
    if category_id:
        questions = questions.filter(category_id=category_id)
    
    question_type = request.GET.get('type')
    if question_type:
        questions = questions.filter(question_type=question_type)
    
    categories = Category.objects.all()
    
    return render(request, 'exam/paper_form.html', {
        'exam': exam,
        'questions': questions,
        'categories': categories,
        'selected_category': category_id,
        'selected_type': question_type,
    })


@login_required
@teacher_required
def paper_detail_view(request, paper_id):
    """试卷详情视图"""
    paper = get_object_or_404(Paper, id=paper_id)
    # 使用select_related确保加载完整的question数据，包括所有字段
    paper_questions = paper.paper_questions.all().select_related('question').prefetch_related('question__category').order_by('order', 'id')
    
    return render(request, 'exam/paper_detail.html', {
        'paper': paper,
        'paper_questions': paper_questions
    })


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def paper_edit_questions_view(request, paper_id):
    """
    已生成试卷后，追加题目（特别是随机组卷后继续补充题目）
    仅做“添加题目”，不在这里删除已有题目。
    """
    paper = get_object_or_404(Paper, id=paper_id)
    exam = paper.exam
    
    # 已在试卷中的题目 ID，后面查询题库时排除
    existing_question_ids = list(
        paper.paper_questions.values_list('question_id', flat=True)
    )
    
    if request.method == 'POST':
        try:
            question_ids = request.POST.getlist('questions')
            if not question_ids:
                messages.error(request, '请至少选择一题要添加到试卷中。')
                return redirect('exam:paper_edit_questions', paper_id=paper.id)
            
            # 当前最大 order，从后面继续累加
            from django.db.models import Max as _Max  # 局部别名，避免与上方导入冲突
            max_order = paper.paper_questions.aggregate(max_order=_Max('order')).get('max_order') or 0
            order = max_order + 1
            
            created_count = 0
            for qid in question_ids:
                try:
                    question = Question.objects.get(id=qid)
                except Question.DoesNotExist:
                    continue
                
                # 跳过已经在试卷中的题目（防守式检查）
                if question.id in existing_question_ids:
                    continue
                
                score = int(request.POST.get(f'score_{qid}', question.score or 1))
                PaperQuestion.objects.create(
                    paper=paper,
                    question=question,
                    order=order,
                    score=score
                )
                order += 1
                created_count += 1
            
            if created_count > 0:
                messages.success(request, f'已成功为试卷添加 {created_count} 道题目。')
            else:
                messages.warning(request, '没有成功添加任何题目，请检查所选题目是否已经在试卷中。')
            
            return redirect('exam:paper_detail', paper_id=paper.id)
        except Exception as e:
            messages.error(request, f'添加题目失败：{str(e)}')
            return redirect('exam:paper_edit_questions', paper_id=paper.id)
    
    # GET：展示可供追加的题目列表（只显示还未在本试卷中的题目）
    questions = Question.objects.filter(is_active=True).exclude(id__in=existing_question_ids).select_related('category')
    
    # 筛选
    category_id = request.GET.get('category')
    if category_id:
        questions = questions.filter(category_id=category_id)
    
    question_type = request.GET.get('type')
    if question_type:
        questions = questions.filter(question_type=question_type)
    
    categories = Category.objects.all()
    
    context = {
        'exam': exam,
        'paper': paper,
        'questions': questions,
        'categories': categories,
        'selected_category': category_id,
        'selected_type': question_type,
    }
    return render(request, 'exam/paper_edit_questions.html', context)


@login_required
@teacher_required
def exam_attempt_list_view(request, exam_id):
    """某场考试的学生答卷列表（教师批阅入口）"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    attempts = ExamAttempt.objects.filter(exam=exam).select_related('user', 'paper').prefetch_related('answers__question')
    
    # 统计每个答卷中主观题的数量和已批阅数量
    grading_info = {}
    for attempt in attempts:
        subjective_answers = [a for a in attempt.answers.all() if a.question.question_type == 'subjective']
        total_subjective = len(subjective_answers)
        graded_subjective = sum(1 for a in subjective_answers if a.score > 0)
        grading_info[attempt.id] = {
            'total_subjective': total_subjective,
            'graded_subjective': graded_subjective,
        }
    
    context = {
        'exam': exam,
        'attempts': attempts,
        'grading_info': grading_info,
    }
    return render(request, 'exam/exam_attempt_list.html', context)


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def attempt_review_view(request, attempt_id):
    """单份答卷批阅视图（主观题人工评分）"""
    attempt = get_object_or_404(ExamAttempt, id=attempt_id)
    exam = attempt.exam
    
    # 按试卷题目顺序展示
    paper_questions = attempt.paper.paper_questions.all().select_related('question').order_by('order', 'id')
    question_order_map = {pq.question_id: pq.order for pq in paper_questions}
    
    answers = attempt.answers.all().select_related('question')
    answers_list = list(answers)
    answers_list.sort(key=lambda a: question_order_map.get(a.question_id, 999))
    
    if request.method == 'POST':
        try:
            for answer in answers_list:
                if answer.question.question_type != 'subjective':
                    continue
                field_name = f'score_{answer.id}'
                score_val = request.POST.get(field_name, '').strip()
                if score_val == '':
                    # 留空则视为 0 分
                    answer.score = 0
                else:
                    try:
                        score = float(score_val)
                    except ValueError:
                        score = 0
                    # 分数限定在 0 ~ 满分之间
                    score = max(0, min(score, float(answer.question.score)))
                    answer.score = score
                # 主观题正误标记不太重要，这里简单认为得分 > 0 即为“正确”
                answer.is_correct = answer.score > 0
                answer.save()
            
            # 重新计算总分与及格状态
            attempt.calculate_score()
            messages.success(request, '批阅结果已保存并重新计算总分。')
        except Exception as e:
            messages.error(request, f'批阅保存失败：{str(e)}')
    
    context = {
        'exam': exam,
        'attempt': attempt,
        'answers': answers_list,
        'question_order_map': question_order_map,
    }
    return render(request, 'exam/attempt_review.html', context)


@login_required
@teacher_required
def exam_statistics_view(request, exam_id):
    """考试成绩统计分析视图（教师端）"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    attempts_qs = ExamAttempt.objects.filter(
        exam=exam,
        status__in=['submitted', 'timeout']
    ).select_related('user', 'paper')
    
    total_attempts = attempts_qs.count()
    
    stats = {
        'total_attempts': total_attempts,
        'avg_score': 0,
        'max_score': 0,
        'min_score': 0,
        'pass_count': 0,
        'pass_rate': 0,
        'sections': [],  # 分数段统计
    }
    
    attempts = list(attempts_qs)
    if attempts:
        scores = [a.total_score for a in attempts]
        stats['avg_score'] = round(sum(scores) / len(scores), 2)
        stats['max_score'] = max(scores)
        stats['min_score'] = min(scores)
        pass_count = sum(1 for a in attempts if a.is_passed)
        stats['pass_count'] = pass_count
        stats['pass_rate'] = round(pass_count * 100 / len(scores), 2)
        
        # 简单分数段分布：0-59, 60-69, 70-79, 80-89, 90+
        buckets = [
            {'label': '0-59', 'min': 0, 'max': 59},
            {'label': '60-69', 'min': 60, 'max': 69},
            {'label': '70-79', 'min': 70, 'max': 79},
            {'label': '80-89', 'min': 80, 'max': 89},
            {'label': '90+', 'min': 90, 'max': 1000},
        ]
        sections = []
        for b in buckets:
            count = sum(1 for s in scores if b['min'] <= s <= b['max'])
            sections.append({
                'label': b['label'],
                'count': count,
                'rate': round(count * 100 / len(scores), 2) if len(scores) else 0,
            })
        stats['sections'] = sections
    
    context = {
        'exam': exam,
        'attempts': attempts,
        'stats': stats,
    }
    return render(request, 'exam/exam_statistics.html', context)


@login_required
@teacher_required
def exam_statistics_entry_view(request):
    """成绩统计入口：选择一场考试查看图表"""
    exams = (
        Exam.objects
        .annotate(submitted_count=Count('attempts', filter=Q(attempts__status__in=['submitted', 'timeout'])))
        .order_by('-start_time')
    )
    # 只显示有成绩的考试，若没有则回退显示全部
    exams_with_scores = [e for e in exams if e.submitted_count]
    context = {
        'exams': exams_with_scores or list(exams),
        'show_all': not exams_with_scores,
    }
    return render(request, 'exam/exam_statistics_entry.html', context)


@login_required
@teacher_required
def admin_dashboard_view(request):
    """
    后台管理首页（Dashboard）
    展示一些全局统计数据和考试成绩折线/柱状图。
    """
    # 核心统计数据
    total_students = UserProfile.objects.filter(role='student').count()
    total_teachers = UserProfile.objects.filter(role__in=['teacher', 'admin']).count()
    total_exams = Exam.objects.count()
    total_questions = Question.objects.count()
    
    today = timezone.now().date()
    today_exams = Exam.objects.filter(start_time__date=today).count()
    
    # 最近有成绩的考试平均分（最多 10 场，按开始时间排序）
    exam_stats_qs = (
        ExamAttempt.objects
        .filter(status__in=['submitted', 'timeout'])
        .values('exam_id', 'exam__title', 'exam__start_time')
        .annotate(avg_score=Avg('total_score'), attempt_count=Count('id'))
        .order_by('exam__start_time')
    )
    exam_stats = list(exam_stats_qs)[-10:]  # 只取最后 10 场
    
    labels = [item['exam__title'] for item in exam_stats]
    scores = [round(item['avg_score'] or 0, 2) for item in exam_stats]
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_exams': total_exams,
        'total_questions': total_questions,
        'today_exams': today_exams,
        'chart_labels': json.dumps(labels, ensure_ascii=False),
        'chart_scores': json.dumps(scores),
    }
    return render(request, 'exam/admin_dashboard.html', context)


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def question_import_view(request):
    """题目批量导入视图"""
    if request.method == 'POST':
        try:
            file = request.FILES.get('file')
            if not file:
                messages.error(request, '请选择要导入的文件！')
                return redirect('exam:question_import')
            
            # 获取默认分类
            default_category_id = request.POST.get('category') or None
            
            # 根据文件扩展名选择解析方法
            file_name = file.name.lower()
            if file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                questions_data = parse_excel_file(file)
            elif file_name.endswith('.csv'):
                questions_data = parse_csv_file(file)
            elif file_name.endswith('.json'):
                questions_data = parse_json_file(file)
            else:
                messages.error(request, '不支持的文件格式！请上传Excel(.xlsx/.xls)、CSV(.csv)或JSON(.json)文件。')
                return redirect('exam:question_import')
            
            if not questions_data:
                messages.error(request, '文件中没有找到有效的题目数据！')
                return redirect('exam:question_import')
            
            # 导入题目
            success_count, fail_count, errors = import_questions_from_data(
                questions_data, 
                request.user, 
                default_category_id
            )
            
            if success_count > 0:
                messages.success(request, f'成功导入 {success_count} 道题目！')
            if fail_count > 0:
                error_msg = f'导入失败 {fail_count} 道题目。'
                if errors:
                    error_msg += f' 错误详情：{"; ".join(errors[:5])}'  # 只显示前5个错误
                    if len(errors) > 5:
                        error_msg += f'...（共{len(errors)}个错误）'
                messages.warning(request, error_msg)
            
            return redirect('exam:question_list')
        except ValidationError as e:
            messages.error(request, f'导入失败：{str(e)}')
        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
    
    categories = Category.objects.all()
    return render(request, 'exam/question_import.html', {
        'categories': categories
    })


@login_required
@teacher_required
def download_template_view(request, file_type):
    """下载导入模板文件"""
    if file_type == 'excel':
        # 创建Excel模板
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "题目导入模板"
            
            # 设置表头
            headers = ['题目标题', '题目内容', '题目类型(single/multiple/judge)', '难度(easy/medium/hard)', 
                      '分类名称', '分值', '正确答案', '解析', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F']
            ws.append(headers)
            
            # 设置表头样式
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
            
            # 添加示例数据
            example = [
                '示例题目1', 
                '这是一道示例单选题的内容', 
                'single', 
                'medium', 
                '计算机网络', 
                5, 
                'A', 
                '这是解析内容',
                '选项A的内容',
                '选项B的内容',
                '选项C的内容',
                '选项D的内容',
                '',
                ''
            ]
            ws.append(example)
            
            # 设置列宽
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 15
            ws.column_dimensions['E'].width = 15
            ws.column_dimensions['F'].width = 10
            ws.column_dimensions['G'].width = 15
            ws.column_dimensions['H'].width = 30
            
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="题目导入模板.xlsx"'
            wb.save(response)
            return response
        except ImportError:
            messages.error(request, '请安装openpyxl库：pip install openpyxl')
            return redirect('exam:question_import')
    
    elif file_type == 'csv':
        # 创建CSV模板
        import csv
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="题目导入模板.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['题目标题', '题目内容', '题目类型(single/multiple/judge)', '难度(easy/medium/hard)', 
                        '分类名称', '分值', '正确答案', '解析', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F'])
        writer.writerow(['示例题目1', '这是一道示例单选题的内容', 'single', 'medium', '计算机网络', 5, 'A', '这是解析内容',
                        '选项A的内容', '选项B的内容', '选项C的内容', '选项D的内容', '', ''])
        return response
    
    elif file_type == 'json':
        # 创建JSON模板
        template_data = {
            "questions": [
                {
                    "title": "示例题目1",
                    "content": "这是一道示例单选题的内容",
                    "question_type": "single",
                    "difficulty": "medium",
                    "category": "计算机网络",
                    "score": 5,
                    "options": {
                        "A": "选项A的内容",
                        "B": "选项B的内容",
                        "C": "选项C的内容",
                        "D": "选项D的内容"
                    },
                    "correct_answer": "A",
                    "explanation": "这是解析内容",
                    "image_base64": "可选：图片的base64编码字符串（格式：data:image/png;base64,iVBORw0KGgoAAAANS...）或直接base64字符串"
                }
            ]
        }
        
        response = HttpResponse(json.dumps(template_data, ensure_ascii=False, indent=2), content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="题目导入模板.json"'
        return response
    
    else:
        messages.error(request, '不支持的文件类型！')
        return redirect('exam:question_import')

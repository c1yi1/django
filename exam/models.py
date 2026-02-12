from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    """题目分类"""
    name = models.CharField(max_length=100, unique=True, verbose_name='分类名称')
    description = models.TextField(blank=True, null=True, verbose_name='分类描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '题目分类'
        verbose_name_plural = '题目分类'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Question(models.Model):
    """题目模型"""
    QUESTION_TYPES = [
        ('single', '单选题'),
        ('multiple', '多选题'),
        ('judge', '判断题'),
        ('subjective', '主观题'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ]
    
    title = models.CharField(max_length=500, verbose_name='题目标题')
    content = models.TextField(verbose_name='题目内容（支持HTML）')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, verbose_name='题目类型')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='medium', verbose_name='难度等级')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='题目分类')
    score = models.PositiveIntegerField(default=5, verbose_name='分值')
    options = models.JSONField(default=dict, blank=True, verbose_name='选项')
    image = models.ImageField(upload_to='question_images/', null=True, blank=True, verbose_name='题目图片')
    correct_answer = models.CharField(max_length=500, verbose_name='正确答案')
    explanation = models.TextField(blank=True, null=True, verbose_name='题目解析')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_questions', verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_question_type_display()} - {self.title[:50]}"
    
    def get_correct_answer_list(self):
        """获取正确答案列表（用于多选题）"""
        if self.question_type == 'multiple':
            if isinstance(self.correct_answer, str):
                return [ans.strip() for ans in self.correct_answer.split(',')]
            return self.correct_answer
        return [self.correct_answer]
    
    def check_answer(self, user_answer):
        """检查答案是否正确"""
        # 主观题不在这里判分，由教师人工批阅
        if self.question_type == 'subjective':
            return False
        
        if self.question_type == 'judge':
            correct = str(self.correct_answer).lower()
            user = str(user_answer).lower()
            return correct == user or (correct == 'true' and user in ['正确', '对', '1']) or (correct == 'false' and user in ['错误', '错', '0'])
        elif self.question_type == 'multiple':
            correct_list = set(self.get_correct_answer_list())
            if isinstance(user_answer, str):
                user_list = set([ans.strip() for ans in user_answer.split(',')])
            else:
                user_list = set(user_answer)
            return correct_list == user_list
        else:
            return str(self.correct_answer).strip().upper() == str(user_answer).strip().upper()


class Exam(models.Model):
    """考试模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('ongoing', '进行中'),
        ('finished', '已结束'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='考试名称')
    description = models.TextField(blank=True, null=True, verbose_name='考试描述')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_exams', verbose_name='创建者')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    duration = models.PositiveIntegerField(verbose_name='考试时长（分钟）')
    total_score = models.PositiveIntegerField(default=100, verbose_name='总分')
    pass_score = models.PositiveIntegerField(default=60, verbose_name='及格分数')
    max_attempts = models.PositiveIntegerField(default=1, verbose_name='最大尝试次数')
    show_answer = models.BooleanField(default=True, verbose_name='考试结束后显示答案')
    show_score = models.BooleanField(default=True, verbose_name='考试结束后显示分数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '考试'
        verbose_name_plural = '考试'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def time_status(self):
        """
        根据当前时间动态计算考试状态：
        - draft: 始终显示草稿
        - 已发布（published）：当前时间早于开始时间
        - 进行中（ongoing）：当前时间在开始和结束时间之间
        - 已结束（finished）：当前时间晚于结束时间
        """
        now = timezone.now()
        # 草稿状态单独处理
        if self.status == 'draft':
            return 'draft'
        # 按时间窗口动态计算状态
        if now < self.start_time:
            return 'published'
        if self.start_time <= now <= self.end_time:
            return 'ongoing'
        return 'finished'
    
    def get_time_status_display(self):
        """获取基于时间计算后的状态中文显示"""
        display_map = dict(self.STATUS_CHOICES)
        return display_map.get(self.time_status, display_map.get(self.status, '未知状态'))
    
    def is_available(self):
        """检查考试是否可用（可以开始答题）"""
        now = timezone.now()
        # 考试状态必须是已发布或进行中，且当前时间在开始时间和结束时间之间
        return self.time_status in ['published', 'ongoing'] and self.start_time <= now <= self.end_time


class Paper(models.Model):
    """试卷模型"""
    GENERATE_TYPES = [
        ('manual', '手动选题'),
        ('random', '随机组卷'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='papers', verbose_name='所属考试')
    name = models.CharField(max_length=200, verbose_name='试卷名称')
    generate_type = models.CharField(max_length=20, choices=GENERATE_TYPES, default='manual', verbose_name='生成方式')
    random_rules = models.JSONField(default=dict, blank=True, verbose_name='随机组卷规则')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '试卷'
        verbose_name_plural = '试卷'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.exam.title} - {self.name}"
    
    def get_total_score(self):
        """计算试卷总分"""
        return sum(pq.score for pq in self.paper_questions.all())
    
    def get_total_questions(self):
        """获取题目总数"""
        return self.paper_questions.count()


class PaperQuestion(models.Model):
    """试卷题目关联表"""
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='paper_questions', verbose_name='试卷')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    order = models.PositiveIntegerField(default=0, verbose_name='题目顺序')
    score = models.PositiveIntegerField(verbose_name='分值')
    
    class Meta:
        verbose_name = '试卷题目'
        verbose_name_plural = '试卷题目'
        ordering = ['order', 'id']
        unique_together = ['paper', 'question']
    
    def __str__(self):
        return f"{self.paper.name} - {self.question.title[:30]}"


class ExamAttempt(models.Model):
    """考试答题记录"""
    STATUS_CHOICES = [
        ('in_progress', '答题中'),
        ('submitted', '已提交'),
        ('timeout', '超时'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts', verbose_name='考试')
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='attempts', verbose_name='试卷')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_attempts', verbose_name='考生')
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='开始时间')
    submit_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name='状态')
    total_score = models.FloatField(default=0, verbose_name='总分')
    is_passed = models.BooleanField(default=False, verbose_name='是否及格')
    
    class Meta:
        verbose_name = '考试答题记录'
        verbose_name_plural = '考试答题记录'
        ordering = ['-start_time']
        unique_together = ['exam', 'paper', 'user', 'start_time']  # 同一用户同一试卷的多次答题记录
    
    def __str__(self):
        return f"{self.user.username} - {self.exam.title} - {self.get_status_display()}"
    
    def get_duration(self):
        """获取答题时长（秒）"""
        if self.submit_time:
            return int((self.submit_time - self.start_time).total_seconds())
        return int((timezone.now() - self.start_time).total_seconds())
    
    def calculate_score(self):
        """计算总分"""
        # 总分直接累加每个答案的得分（客观题由系统设置分值，主观题由教师批阅设置分值）
        total = sum(answer.score for answer in self.answers.all())
        self.total_score = total
        self.is_passed = total >= self.exam.pass_score
        self.save()
        return total
    
    @classmethod
    def get_max_score(cls, exam, user):
        """获取用户在某个考试中的最高分"""
        attempts = cls.objects.filter(
            exam=exam,
            user=user,
            status__in=['submitted', 'timeout']
        ).order_by('-total_score')
        
        if attempts.exists():
            return attempts.first().total_score
        return None


class Answer(models.Model):
    """答案记录"""
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name='答题记录')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    user_answer = models.CharField(max_length=500, verbose_name='用户答案')
    is_correct = models.BooleanField(default=False, verbose_name='是否正确')
    score = models.FloatField(default=0, verbose_name='得分')
    # 标记是否收藏（学生自用）
    is_favorited = models.BooleanField(default=False, verbose_name='是否收藏')
    
    class Meta:
        verbose_name = '答案记录'
        verbose_name_plural = '答案记录'
        unique_together = ['attempt', 'question']  # 同一答题记录中同一题目只能有一个答案
    
    def __str__(self):
        return f"{self.attempt.user.username} - {self.question.title[:30]}"
    
    def check_and_score(self):
        """检查答案并计算得分"""
        # 主观题不自动判分，保留当前分数与正误状态，等待教师批阅
        if self.question.question_type == 'subjective':
            return self.score
        
        # 客观题按标准答案自动判分
        self.is_correct = self.question.check_answer(self.user_answer)
        
        # 获取该题目在试卷中的分值
        paper_question = self.attempt.paper.paper_questions.filter(question=self.question).first()
        if paper_question:
            self.score = paper_question.score if self.is_correct else 0
        else:
            self.score = self.question.score if self.is_correct else 0
        self.save()
        return self.score


class ExamActivityLog(models.Model):
    """
    考试行为日志：
    - 心跳（前端定期上报）
    - 切屏 / 最小化 / 恢复 等可疑操作
    方便事后审计与实时反作弊判断。
    """
    EVENT_TYPES = [
        ('heartbeat', '心跳'),
        ('visibility_hidden', '页面隐藏（切屏/最小化）'),
        ('visibility_visible', '页面重新可见'),
        ('window_blur', '窗口失焦'),
        ('window_focus', '窗口获得焦点'),
        ('force_submit', '强制提交'),
        ('other', '其他事件'),
    ]

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name='答题记录'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='exam_activity_logs',
        verbose_name='用户'
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, verbose_name='事件类型')
    detail = models.CharField(max_length=255, blank=True, null=True, verbose_name='事件详情')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发生时间')

    class Meta:
        verbose_name = '考试行为日志'
        verbose_name_plural = '考试行为日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.attempt_id} - {self.event_type}"


class WrongQuestion(models.Model):
    """错题本（含考试与练习）"""
    SOURCE_CHOICES = [
        ('exam', '考试'),
        ('practice', '练习'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wrong_questions', verbose_name='用户')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='wrong_users', verbose_name='题目')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='exam', verbose_name='来源')
    wrong_count = models.PositiveIntegerField(default=1, verbose_name='累计错误次数')
    last_wrong_at = models.DateTimeField(auto_now=True, verbose_name='最后错误时间')
    
    class Meta:
        unique_together = ['user', 'question']
        ordering = ['-last_wrong_at']
        verbose_name = '错题'
        verbose_name_plural = '错题'
    
    def __str__(self):
        return f"{self.user.username} - {self.question_id}"


class FavoriteQuestion(models.Model):
    """收藏题目"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_questions', verbose_name='用户')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='favorited_by', verbose_name='题目')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')
    
    class Meta:
        unique_together = ['user', 'question']
        ordering = ['-created_at']
        verbose_name = '收藏题目'
        verbose_name_plural = '收藏题目'
    
    def __str__(self):
        return f"{self.user.username} - {self.question_id}"

from django.db.models import Q, Max
from .models import Question, PaperQuestion


def generate_random_paper(paper, rules, difficulty='all', category_id=None):
    """
    随机组卷函数
    
    Args:
        paper: Paper对象
        rules: 字典，包含各类型题目的数量，如 {'single': 10, 'multiple': 5, 'judge': 5}
        difficulty: 难度筛选，'all'表示所有难度
        category_id: 分类ID，None表示所有分类
    """
    # 如果试卷中已经有题目，则在现有最大顺序号之后继续编号
    max_order = paper.paper_questions.aggregate(max_order=Max('order'))['max_order'] or 0
    order = max_order + 1
    
    def is_question_complete(q: Question) -> bool:
        """
        判断题目是否“完整”，用于随机选题时过滤掉不完整题目。
        
        完整标准：
        - content 非空
        - correct_answer 非空
        - 单选/多选题必须有非空 options
        """
        # 题干和答案不能为空
        if not q.content or not str(q.content).strip():
            return False
        if not q.correct_answer or not str(q.correct_answer).strip():
            return False
        
        # 选择题必须有选项
        if q.question_type in ['single', 'multiple']:
            if not q.options or not isinstance(q.options, dict) or len(q.options) == 0:
                return False
        
        return True
    
    for question_type, count in rules.items():
        if count <= 0:
            continue
        
        # 构建查询条件（基础过滤：类型 + 启用状态）
        query = Question.objects.filter(
            question_type=question_type,
            is_active=True
        )
        
        if difficulty != 'all':
            query = query.filter(difficulty=difficulty)
        
        if category_id:
            query = query.filter(category_id=category_id)
        
        # 排除已经在试卷中的题目
        existing_question_ids = paper.paper_questions.values_list('question_id', flat=True)
        if existing_question_ids:
            query = query.exclude(id__in=existing_question_ids)
        
        # 进一步在数据库层面过滤掉明显不完整的数据（空内容 / 空答案）
        query = query.filter(
            content__isnull=False
        ).exclude(
            content__exact=''
        ).filter(
            correct_answer__isnull=False
        ).exclude(
            correct_answer__exact=''
        )
        
        # 按随机顺序遍历题目，只选取“完整”的题目，直到达到需要的数量
        # 注意：不要使用 only()/defer()，确保所有字段都加载完整
        random_queryset = query.select_related('category', 'created_by').order_by('?')
        
        selected_count = 0
        for question in random_queryset:
            # 为了保险起见，再次从数据库完整加载 Question 对象
            full_question = Question.objects.select_related('category', 'created_by').get(id=question.id)
            
            # 过滤掉不完整的题目（题干/答案/选项缺失）
            if not is_question_complete(full_question):
                continue
            
            # 创建试卷题目关联
            PaperQuestion.objects.create(
                paper=paper,
                question=full_question,
                order=order,
                score=full_question.score
            )
            order += 1
            selected_count += 1
            
            if selected_count >= count:
                break
        
        # 如果未能选满，说明题库中可用且“完整”的题目数量不足
        if selected_count < count:
            available_total = query.count()
            raise ValueError(
                f'{question_type} 类型题目中，满足条件且内容完整的题目数量不足：'
                f'需要 {count} 道，实际只生成 {selected_count} 道（题库总可选 {available_total} 道）。'
            )


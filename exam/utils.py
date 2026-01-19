import json
import csv
from io import StringIO
from django.core.exceptions import ValidationError
from .models import Question, Category


def parse_excel_file(file):
    """解析Excel文件"""
    try:
        import openpyxl
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        
        questions = []
        # 跳过表头，从第二行开始
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not row[0]:  # 如果第一列为空，跳过
                continue
            
            question_data = {
                'title': str(row[0]).strip() if row[0] else '',
                'content': str(row[1]).strip() if row[1] else '',
                'question_type': str(row[2]).strip().lower() if row[2] else 'single',
                'difficulty': str(row[3]).strip().lower() if row[3] else 'medium',
                'category': str(row[4]).strip() if row[4] else None,
                'score': int(row[5]) if row[5] else 5,
                'options': {},
                'correct_answer': str(row[6]).strip() if row[6] else '',
                'explanation': str(row[7]).strip() if row[7] else '',
            }
            
            # 解析选项（从第8列开始，A、B、C、D...）
            option_keys = ['A', 'B', 'C', 'D', 'E', 'F']
            for idx, key in enumerate(option_keys):
                col_idx = 8 + idx
                if col_idx < len(row) and row[col_idx]:
                    question_data['options'][key] = str(row[col_idx]).strip()
            
            questions.append(question_data)
        
        return questions
    except ImportError:
        raise ValidationError('请安装openpyxl库：pip install openpyxl')
    except Exception as e:
        raise ValidationError(f'解析Excel文件失败：{str(e)}')


def parse_csv_file(file):
    """解析CSV文件"""
    try:
        # 尝试使用UTF-8编码
        try:
            content = file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试GBK
            file.seek(0)
            content = file.read().decode('gbk')
        
        csv_reader = csv.reader(StringIO(content))
        questions = []
        
        # 跳过表头
        next(csv_reader, None)
        
        for row in csv_reader:
            if not row or not row[0]:  # 如果第一列为空，跳过
                continue
            
            question_data = {
                'title': row[0].strip() if len(row) > 0 else '',
                'content': row[1].strip() if len(row) > 1 else '',
                'question_type': row[2].strip().lower() if len(row) > 2 else 'single',
                'difficulty': row[3].strip().lower() if len(row) > 3 else 'medium',
                'category': row[4].strip() if len(row) > 4 and row[4] else None,
                'score': int(row[5]) if len(row) > 5 and row[5] else 5,
                'options': {},
                'correct_answer': row[6].strip() if len(row) > 6 else '',
                'explanation': row[7].strip() if len(row) > 7 else '',
            }
            
            # 解析选项（从第8列开始）
            option_keys = ['A', 'B', 'C', 'D', 'E', 'F']
            for idx, key in enumerate(option_keys):
                col_idx = 8 + idx
                if col_idx < len(row) and row[col_idx]:
                    question_data['options'][key] = row[col_idx].strip()
            
            questions.append(question_data)
        
        return questions
    except Exception as e:
        raise ValidationError(f'解析CSV文件失败：{str(e)}')


def parse_json_file(file):
    """解析JSON文件"""
    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        
        # 支持两种格式：数组格式和对象格式
        if isinstance(data, list):
            questions = data
        elif isinstance(data, dict) and 'questions' in data:
            questions = data['questions']
        else:
            raise ValidationError('JSON格式错误：应为数组或包含questions字段的对象')
        
        # 验证和规范化数据
        normalized_questions = []
        for item in questions:
            question_data = {
                'title': item.get('title', '').strip(),
                'content': item.get('content', '').strip(),
                'question_type': item.get('question_type', 'single').strip().lower(),
                'difficulty': item.get('difficulty', 'medium').strip().lower(),
                'category': item.get('category', '').strip() if item.get('category') else None,
                'score': int(item.get('score', 5)),
                'options': item.get('options', {}),
                'correct_answer': str(item.get('correct_answer', '')).strip(),
                'explanation': item.get('explanation', '').strip() if item.get('explanation') else '',
                'image_base64': item.get('image_base64', '').strip() if item.get('image_base64') else None,
            }
            normalized_questions.append(question_data)
        
        return normalized_questions
    except json.JSONDecodeError as e:
        raise ValidationError(f'JSON格式错误：{str(e)}')
    except Exception as e:
        raise ValidationError(f'解析JSON文件失败：{str(e)}')


def import_questions_from_data(questions_data, user, default_category=None):
    """
    将解析后的题目数据导入数据库
    
    Args:
        questions_data: 题目数据列表
        user: 创建者用户对象
        default_category: 默认分类ID（如果题目没有指定分类）
    
    Returns:
        tuple: (成功数量, 失败数量, 错误列表)
    """
    success_count = 0
    fail_count = 0
    errors = []
    
    for idx, q_data in enumerate(questions_data, start=1):
        try:
            # 验证题目类型
            if q_data['question_type'] not in ['single', 'multiple', 'judge']:
                raise ValidationError(f"无效的题目类型：{q_data['question_type']}")
            
            # 验证难度
            if q_data['difficulty'] not in ['easy', 'medium', 'hard']:
                q_data['difficulty'] = 'medium'
            
            # 处理分类
            category = None
            if q_data.get('category'):
                # 尝试通过名称查找分类
                category = Category.objects.filter(name=q_data['category']).first()
                if not category and default_category:
                    category = Category.objects.filter(id=default_category).first()
            elif default_category:
                category = Category.objects.filter(id=default_category).first()
            
            # 处理图片（base64编码）
            image_file = None
            if q_data.get('image_base64'):
                try:
                    import base64
                    from io import BytesIO
                    from django.core.files.base import ContentFile
                    from PIL import Image
                    
                    # 解析base64数据（可能包含data:image/png;base64,前缀）
                    image_data = q_data['image_base64']
                    if ',' in image_data:
                        image_data = image_data.split(',')[1]
                    
                    # 解码base64
                    image_bytes = base64.b64decode(image_data)
                    
                    # 验证是否为有效图片
                    img = Image.open(BytesIO(image_bytes))
                    img_format = img.format.lower() if img.format else 'png'
                    
                    # 转换为RGB（如果是RGBA）
                    if img_format == 'png' and img.mode == 'RGBA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])
                        img = background
                    
                    # 保存为文件
                    buffer = BytesIO()
                    img.save(buffer, format=img_format)
                    image_file = ContentFile(buffer.getvalue(), name=f'imported_{idx}.{img_format}')
                except Exception as e:
                    # 图片处理失败，记录错误但不阻止题目创建
                    errors.append(f"第{idx}行图片处理失败：{str(e)}")
            
            # 创建题目
            question = Question.objects.create(
                title=q_data['title'],
                content=q_data['content'],
                question_type=q_data['question_type'],
                difficulty=q_data['difficulty'],
                category=category,
                score=q_data['score'],
                options=q_data.get('options', {}),
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation', ''),
                created_by=user
            )
            
            # 如果有图片，保存图片
            if image_file:
                question.image = image_file
                question.save()
            success_count += 1
        except Exception as e:
            fail_count += 1
            errors.append(f"第{idx}行：{str(e)}")
    
    return success_count, fail_count, errors






HEAD
# Django 在线考试系统开发日志

## 项目概述

这是一个基于 Django 5.2.8 开发的在线考试系统，支持学生在线考试、教师后台管理、题库管理、成绩统计等功能。

## 技术栈

- **后端框架**: Django 5.2.8
- **数据库**: MySQL 8.0+（生产环境）
- **前端**: HTML5 + CSS3 + JavaScript (ES6+)
- **图标库**: Remix Icon 3.5.0 (CDN)
- **图表库**: ECharts 5.5.0 (CDN)
- **特效库**: Particles.js 2.0.0 (CDN)
- **图像处理**: Pillow 10.0.0+
- **文件处理**: openpyxl 3.1.0+

**详细技术栈文档**：查看 `TECH_STACK.md`  
**数据库ER图**：查看 `ER_DIAGRAM.md`

---

## 开发历程与修改记录

### 第一阶段：UI商业化改造

#### 1.1 创建全局主题样式系统
**文件**: `static/css/theme.css`
- 创建统一的CSS主题文件
- 定义颜色变量、按钮样式、卡片样式、表格样式
- 集成 Remix Icon CDN
- 统一导航栏、侧边栏、表单等组件样式

#### 1.2 替换图标系统
**目标**: 将所有页面的emoji图标替换为专业的Remix Icon图标库

**修改的文件**:
- `templates/accounts/home.html` - 用户首页
- `templates/accounts/login.html` - 登录页面
- `templates/exam/admin_dashboard.html` - 后台首页
- `templates/exam/exam_list.html` - 考试列表
- `templates/exam/exam_detail.html` - 考试详情
- `templates/exam/exam_form.html` - 考试表单
- `templates/exam/exam_list_student.html` - 学生考试列表
- `templates/exam/exam_result.html` - 考试结果
- `templates/exam/my_scores.html` - 我的成绩
- `templates/exam/paper_detail.html` - 试卷详情
- `templates/exam/paper_edit_questions.html` - 编辑试卷题目
- `templates/exam/paper_form.html` - 试卷表单
- `templates/exam/question_confirm_delete.html` - 删除确认
- `templates/exam/question_detail.html` - 题目详情
- `templates/exam/question_form.html` - 题目表单
- `templates/exam/question_import.html` - 题目导入
- `templates/exam/question_list.html` - 题目列表
- `templates/exam/start_exam.html` - 开始考试
- `templates/exam/take_exam.html` - 答题页面

**主要图标替换**:
- 📝 → `ri-file-list-line`
- 📊 → `ri-bar-chart-line`
- 📖 → `ri-book-open-line`
- 🎯 → `ri-dashboard-line`
- 💾 → `ri-database-2-line`
- 📄 → `ri-file-paper-line`
- ⚙️ → `ri-user-settings-line`
- 等等...

---

### 第二阶段：后端管理页面优化

#### 2.1 后台首页差异化设计
**文件**: `templates/exam/admin_dashboard.html`
- 根据用户角色（管理员/教师）显示不同的顶部标题
  - 管理员: "Python 在线考试后台管理系统"
  - 教师: "Python 在线考试教师后台"
- 优化侧边栏导航菜单
- 添加数据统计图表（使用ECharts）

#### 2.2 可折叠导航菜单
**文件**: `templates/exam/admin_dashboard.html`
- 实现"考试与题库"二级菜单的折叠/展开功能
- 使用JavaScript控制菜单状态
- 包含子菜单项：
  - 考试管理
  - 试卷管理
  - 成绩统计
  - 题库管理

#### 2.3 移除后台首页的用户管理
- 从后台首页移除用户管理入口（避免冗余）

---

### 第三阶段：学生在线练习模块

#### 3.1 练习题库首页
**文件**: `templates/exam/practice.html`
- 创建学生在线练习界面
- 支持按分类、难度筛选题目
- 实时答题和即时反馈
- 显示题目图片（图形推理题）

#### 3.2 练习API接口
**文件**: `exam/views.py`
- `practice_home_view`: 练习首页视图
- `practice_questions_api`: 获取练习题目API（返回JSON）
- `practice_check_api`: 检查答案API
- `favorite_toggle_api`: 收藏/取消收藏题目API

**功能特性**:
- 支持单选题、多选题、判断题
- 图形推理题正确显示图片
- 判断题显示选择框（True/False）
- 即时显示答案正确性
- 收藏功能

#### 3.3 错题本功能
**文件**: 
- `exam/models.py` - 添加 `WrongQuestion` 模型
- `exam/views.py` - 添加 `my_wrongs_view` 视图
- `templates/exam/my_wrongs.html` - 错题本页面

**功能**:
- 记录考试错题
- 记录练习错题
- 显示题目信息（标题、类型、难度、分类、最后错误时间）
- 提供"去练习"按钮

#### 3.4 收藏夹功能
**文件**:
- `exam/models.py` - 添加 `FavoriteQuestion` 模型
- `exam/views.py` - 添加 `my_favorites_view` 视图和 `favorite_toggle_api` API
- `templates/exam/my_favorites.html` - 收藏夹页面

**功能**:
- 在练习模式中收藏题目
- 查看收藏的题目列表
- 取消收藏功能
- 显示题目详情和图片

---

### 第四阶段：题目管理功能增强

#### 4.1 题目图片上传功能
**文件**: 
- `exam/models.py` - 在 `Question` 模型中添加 `image` 字段
- `exam/views.py` - 修改 `question_create_view` 和 `question_edit_view` 处理图片上传
- `templates/exam/question_form.html` - 添加图片上传表单
- `templates/exam/question_detail.html` - 显示题目图片
- `templates/exam/take_exam.html` - 考试时显示题目图片
- `Django_Excem/settings.py` - 配置 `MEDIA_URL` 和 `MEDIA_ROOT`
- `Django_Excem/urls.py` - 配置媒体文件服务

**功能**:
- 单张图片上传（支持常见图片格式）
- 图片预览
- 删除当前图片选项
- 图片在题目详情页和考试页面正确显示

#### 4.2 批量管理功能
**文件**: `templates/exam/question_list.html`
- 添加"批量管理"按钮
- 点击后显示复选框和批量操作工具栏
- 批量操作包括：
  - 修改题目类型
  - 修改难度
  - 修改分类
  - 修改分值
  - 修改标题（前缀或替换）

**文件**: `exam/views.py` - `question_list_view`
- 处理批量更新逻辑
- 支持部分字段更新（只更新选中的字段）

#### 4.3 题目编辑选项修复
**文件**: `templates/exam/question_form.html`
- 修复编辑题目时选项不显示的问题
- 确保单选题/多选题编辑时正确显示选项输入框
- 支持A-F六个选项
- 修复模板语法错误（条件判断）

---

### 第五阶段：成绩统计功能

#### 5.1 成绩统计入口页面
**文件**: 
- `templates/exam/exam_statistics_entry.html` - 新建
- `exam/views.py` - 添加 `exam_statistics_entry_view`

**功能**:
- 显示所有考试列表
- 选择考试后进入统计页面
- 修复后台首页"成绩统计"链接

#### 5.2 成绩统计详情页面
**文件**: `templates/exam/exam_statistics.html`
- 集成ECharts图表库
- 实现两个图表：
  1. **成绩分布饼图**: 显示不同分数段的人数分布
  2. **题型得分率柱状图**: 显示各题型的平均得分率

**文件**: `exam/views.py`
- `exam_statistics_view`: 成绩统计视图
- `exam_statistics_api`: 提供JSON数据API

**修复问题**:
- 修复饼图标签重叠问题（隐藏默认标签，悬停显示）
- 修复模板语法错误（使用 `json_script` 安全传递数据）

---

### 第六阶段：防作弊功能增强

#### 6.1 防作弊事件监听
**文件**: `templates/exam/take_exam.html`
- 添加客户端事件监听：
  - `visibilitychange`: 检测窗口切换
  - `blur`/`focus`: 检测窗口焦点
  - `mouseleave`: 检测鼠标离开窗口
- 实现事件防抖（避免重复触发）
- 添加警告提示区域

#### 6.2 防作弊后端逻辑
**文件**: `exam/views.py` - `log_exam_event_view`
- 记录可疑活动事件
- 达到阈值（5次）后强制提交考试
- 记录 `force_submit` 事件类型

**文件**: `exam/models.py` - `ExamActivityLog`
- 添加 `force_submit` 和 `other` 事件类型
- 记录所有可疑活动

**功能**:
- 前3次可疑活动：仅记录，不提示
- 第4-5次：显示警告提示
- 第5次：强制提交考试并跳转到结果页

---

### 第七阶段：题目导入功能增强

#### 7.1 JSON模板图片支持
**文件**: 
- `exam/utils.py` - `parse_json_file` 和 `import_questions_from_data`
- `exam/views.py` - `download_template_view`

**功能**:
- JSON模板中添加 `image_base64` 字段说明
- 支持通过base64编码导入图片
- 自动处理图片格式转换（RGBA转RGB）
- 图片处理失败时记录错误但不阻止题目创建

**JSON格式示例**:
```json
{
  "title": "图形推理题",
  "content": "请选择正确的答案",
  "question_type": "single",
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "options": {
    "A": "选项A",
    "B": "选项B"
  },
  "correct_answer": "A"
}
```

#### 7.2 导入反馈优化
**文件**: `templates/exam/question_import.html`
- 添加消息显示区域
- 显示导入成功/失败信息

---

### 第八阶段：Bug修复

#### 8.1 模板语法错误修复
**问题**: `TemplateSyntaxError: Could not parse the remainder`
**修复文件**:
- `templates/exam/paper_detail.html`
- `templates/exam/exam_result.html`
- `templates/exam/question_form.html`
- `templates/exam/question_detail.html`

**修复方法**: 
- 将 `if question.question_type in 'single,multiple'` 
- 改为 `if question.question_type == 'single' or question.question_type == 'multiple'`

#### 8.2 链接修复
- 修复后台首页"成绩统计"链接指向错误
- 修复"试卷管理"链接

#### 8.3 图片显示问题修复
- 修复题目详情页图片不显示
- 修复考试页面图形题不显示
- 修复练习页面图形题不显示

#### 8.4 选项编辑问题修复
- 修复编辑题目时选项输入框不显示
- 修复选项为空时不显示默认输入框
- 添加E、F选项支持

---

## 数据库模型

### 核心模型

1. **Question（题目）**
   - 支持单选题、多选题、判断题、主观题
   - 支持图片上传
   - 支持分类和难度设置

2. **Exam（考试）**
   - 考试时间管理
   - 考试状态管理
   - 最大尝试次数限制

3. **Paper（试卷）**
   - 关联考试
   - 包含多个题目

4. **ExamAttempt（考试答题记录）**
   - 记录学生答题过程
   - 计算总分和是否及格

5. **Answer（答案记录）**
   - 记录每道题的答案
   - 自动判分（客观题）

6. **WrongQuestion（错题）**
   - 记录考试和练习的错题
   - 区分来源（exam/practice）

7. **FavoriteQuestion（收藏题目）**
   - 学生收藏的题目

8. **ExamActivityLog（考试活动日志）**
   - 记录防作弊相关事件
   - 支持强制提交

---

## 主要功能模块

### 学生端
- ✅ 在线考试
- ✅ 在线练习
- ✅ 查看成绩
- ✅ 错题本
- ✅ 收藏夹
- ✅ 图形推理题支持

### 教师/管理员端
- ✅ 考试管理
- ✅ 试卷管理
- ✅ 题库管理
- ✅ 题目批量管理
- ✅ 题目图片上传
- ✅ 成绩统计（图表）
- ✅ 题目导入（Excel/CSV/JSON）
- ✅ JSON导入支持图片

### 系统功能
- ✅ 防作弊机制
- ✅ 自动判分
- ✅ 成绩统计可视化
- ✅ 用户权限管理

---

## 文件结构

```
Django_Excem/
├── accounts/              # 用户账户应用
├── exam/                  # 考试应用
│   ├── models.py         # 数据模型
│   ├── views.py          # 视图函数
│   ├── urls.py           # URL路由
│   ├── utils.py          # 工具函数（题目导入）
│   └── migrations/       # 数据库迁移
├── templates/            # 模板文件
│   ├── accounts/        # 账户相关模板
│   └── exam/            # 考试相关模板
├── static/              # 静态文件
│   └── css/
│       └── theme.css    # 全局主题样式
├── media/               # 媒体文件（上传的图片）
│   └── question_images/
├── Django_Excem/        # 项目配置
│   ├── settings.py     # 项目设置
│   └── urls.py         # 根URL配置
└── manage.py           # Django管理脚本
```

---

## 数据库迁移记录

### 迁移文件列表
1. `0001_initial.py` - 初始模型
2. `0002_exam_paper_paperquestion.py` - 考试和试卷模型
3. `0003_answer_examattempt_and_more.py` - 答案和答题记录
4. `0004_alter_question_question_type_examactivitylog.py` - 题目类型和活动日志
5. `0005_practicesession_practicequestion_practiceanswer.py` - 练习相关模型
6. `0006_question_image.py` - 题目图片字段
7. `0007_alter_practicequestion_unique_together_and_more.py` - 练习模型调整
8. `0008_add_answer_favorite.py` - 答案收藏字段
9. `0009_favoritequestion_wrongquestion.py` - 收藏和错题模型
10. `0010_alter_examactivitylog_event_type.py` - 活动日志事件类型扩展

---

## 配置说明

### 媒体文件配置
**文件**: `Django_Excem/settings.py`
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

**文件**: `Django_Excem/urls.py`
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 静态文件配置
所有页面都引入了 `static/css/theme.css` 全局样式文件。

### 图标库配置
使用 Remix Icon CDN:
```html
<link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
```

### 图表库配置
使用 ECharts CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
```

---

## Git部署指南

### 快速部署到Git（GitHub/GitLab/Gitee）

**方法一：使用自动化脚本（推荐）**

Windows用户：
```bash
# 双击运行或在命令行执行
deploy_to_git.bat
```

PowerShell用户：
```powershell
.\deploy_to_git.ps1
```

**方法二：手动部署**

1. **查看详细部署文档**：`GIT_DEPLOYMENT.md`
2. **快速步骤**：
   ```bash
   # 1. 初始化Git仓库（如果还没有）
   git init
   
   # 2. 添加文件（.gitignore会自动排除敏感文件）
   git add .
   
   # 3. 创建提交
   git commit -m "Initial commit: 智能学习系统项目"
   
   # 4. 在GitHub/GitLab创建仓库后，连接远程仓库
   git remote add origin <你的仓库地址>
   git branch -M main
   git push -u origin main
   ```

**重要提示**：
- ✅ `settings.py` 已在 `.gitignore` 中，不会被提交
- ✅ 使用 `settings.example.py` 作为配置模板
- ✅ 敏感信息（密码、密钥）不会泄露
- 📖 详细说明请查看 `GIT_DEPLOYMENT.md`

---

## 使用说明

### 本地运行项目

**首次运行**：
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置数据库（复制示例配置）
cp Django_Excem/settings.example.py Django_Excem/settings.py
# 然后编辑 settings.py，修改数据库密码和SECRET_KEY

# 3. 运行数据库迁移
python manage.py migrate

# 4. 创建超级用户
python manage.py createsuperuser

# 5. 启动开发服务器
python manage.py runserver
```

### 让外部访问（重要！）

**快速方法（推荐）：**
1. 查看 `QUICK_START.md` - 5分钟快速开始指南
2. 使用 ngrok 内网穿透工具（最简单）

**详细部署：**
- 查看 `DEPLOYMENT.md` - 完整部署文档
- 包含：ngrok、局域网访问、云服务器部署、Docker部署等方案

**快速命令：**
```bash
# 局域网访问
python manage.py runserver 0.0.0.0:8000

# 然后使用 ngrok
ngrok http 8000
```

### 创建超级用户
```bash
python manage.py createsuperuser
```

### 导入题目
1. 访问 `/exam/questions/import/`
2. 下载模板（Excel/CSV/JSON）
3. 填写题目信息
4. 上传文件导入

### JSON导入图片
在JSON文件中使用 `image_base64` 字段，值为base64编码的图片字符串。

---

## 待优化功能

- [ ] 主观题批阅功能完善
- [ ] 考试时间倒计时优化
- [ ] 更多图表类型（如成绩趋势图）
- [ ] 题目搜索和筛选优化
- [ ] 移动端适配
- [ ] 考试结果导出（PDF/Excel）

---

## 更新日志

### 2025-12-06
- ✅ 完成UI商业化改造
- ✅ 替换所有emoji为Remix Icon
- ✅ 实现后台首页差异化设计
- ✅ 添加可折叠导航菜单
- ✅ 完成学生在线练习模块
- ✅ 实现错题本和收藏夹功能
- ✅ 添加题目图片上传功能
- ✅ 实现批量管理功能
- ✅ 完成成绩统计功能（图表）
- ✅ 增强防作弊功能
- ✅ JSON导入支持图片
- ✅ 优化登录界面，添加验证码功能
- ✅ 添加外部访问部署文档和配置
- ✅ UI现代化改造：减少圆润度，采用简洁现代设计风格
- ✅ 更新版权信息为"智能学习系统 | 专注在线教育"
- ✅ 修复所有已知Bug

---

## 开发者

本项目由AI助手协助开发，记录了完整的开发历程和每一步修改。

---

## 许可证

本项目仅供学习和研究使用。


# django
noob
756fd8a2540c7f35dd5049677447c8a029d05041

# Git部署指南

本指南将帮助你将智能学习系统项目部署到Git托管平台（GitHub、GitLab、Gitee等）。

---

## ⚠️ 重要提示：安全第一

在提交代码到Git之前，**必须**确保以下敏感信息不会被提交：

1. ✅ **SECRET_KEY** - Django密钥
2. ✅ **数据库密码** - MySQL密码
3. ✅ **CSRF_TRUSTED_ORIGINS** - 包含个人域名的配置
4. ✅ **用户上传的文件** - media目录
5. ✅ **数据库文件** - db.sqlite3
6. ✅ **Python缓存文件** - __pycache__

---

## 📋 部署步骤

### 第一步：检查并准备文件

#### 1.1 确认敏感文件已排除

项目已包含 `.gitignore` 文件，它会自动排除以下内容：
- `settings.py`（包含敏感信息）
- `media/`（用户上传文件）
- `__pycache__/`（Python缓存）
- `db.sqlite3`（数据库文件）
- 其他临时文件

#### 1.2 创建settings.example.py（已完成）

已创建 `settings.example.py` 作为配置模板，不包含敏感信息。

**重要**：如果 `settings.py` 已经被Git跟踪，需要先移除：

```bash
# 从Git中移除settings.py（但保留本地文件）
git rm --cached Django_Excem/settings.py

# 确保settings.py在.gitignore中
echo "Django_Excem/settings.py" >> .gitignore
```

---

### 第二步：初始化Git仓库

#### 2.1 检查是否已有Git仓库

```bash
# 检查是否已有.git目录
ls -la .git
```

如果已有 `.git` 目录，说明已经初始化，可以跳过2.2步骤。

#### 2.2 初始化Git仓库

```bash
# 进入项目目录
cd "C:\Users\C\PycharmProjects\Django Excem"

# 初始化Git仓库
git init
```

---

### 第三步：配置Git用户信息（首次使用需要）

```bash
# 设置用户名（替换为你的GitHub/GitLab用户名）
git config user.name "你的用户名"

# 设置邮箱（替换为你的邮箱）
git config user.email "your.email@example.com"

# 查看配置
git config --list
```

---

### 第四步：添加文件到Git

#### 4.1 查看将要添加的文件

```bash
# 查看Git状态（会显示哪些文件将被添加）
git status

# 查看哪些文件会被忽略
git status --ignored
```

#### 4.2 添加所有文件

```bash
# 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 或者分步添加
git add *.md
git add requirements.txt
git add manage.py
git add accounts/
git add exam/
git add Django_Excem/
git add templates/
git add static/
```

**注意**：`settings.py` 和 `media/` 应该被自动排除，不会出现在 `git status` 中。

---

### 第五步：创建首次提交

```bash
# 创建提交
git commit -m "Initial commit: 智能学习系统项目"

# 或者更详细的提交信息
git commit -m "Initial commit: 智能学习系统

- 完整的Django在线考试平台
- 支持多题型（单选、多选、判断、主观题）
- 反作弊机制
- 错题本和收藏功能
- 深色主题UI
- 完整的文档和ER图"
```

---

### 第六步：在Git托管平台创建仓库

#### GitHub

1. 登录 [GitHub](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name**: `django-exam-platform`（或你喜欢的名字）
   - **Description**: `智能学习系统 - Django在线考试平台`
   - **Visibility**: Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"（因为本地已有代码）
4. 点击 "Create repository"

#### GitLab

1. 登录 [GitLab](https://gitlab.com)
2. 点击 "New project" → "Create blank project"
3. 填写项目信息
4. 点击 "Create project"

#### Gitee（码云）

1. 登录 [Gitee](https://gitee.com)
2. 点击右上角 "+" → "新建仓库"
3. 填写仓库信息
4. 点击 "创建"

---

### 第七步：连接远程仓库并推送

#### 7.1 添加远程仓库

**GitHub示例**：
```bash
# 替换为你的GitHub仓库地址
git remote add origin https://github.com/你的用户名/django-exam-platform.git
```

**GitLab示例**：
```bash
git remote add origin https://gitlab.com/你的用户名/django-exam-platform.git
```

**Gitee示例**：
```bash
git remote add origin https://gitee.com/你的用户名/django-exam-platform.git
```

#### 7.2 查看远程仓库

```bash
# 查看已配置的远程仓库
git remote -v
```

#### 7.3 推送代码到远程仓库

```bash
# 推送主分支（GitHub默认分支是main，GitLab可能是master）
git branch -M main  # 将当前分支重命名为main（如果还没有）

# 首次推送
git push -u origin main

# 如果远程仓库默认分支是master
git branch -M master
git push -u origin master
```

**如果遇到认证问题**：

- **HTTPS方式**：需要输入用户名和Personal Access Token（不是密码）
- **SSH方式**：需要配置SSH密钥

---

## 🔐 安全配置检查清单

在推送代码前，请确认：

- [ ] `settings.py` 不在Git跟踪中（已在.gitignore中）
- [ ] `settings.example.py` 已创建且不包含敏感信息
- [ ] `media/` 目录不在Git跟踪中
- [ ] `db.sqlite3` 不在Git跟踪中
- [ ] `__pycache__/` 目录不在Git跟踪中
- [ ] `.gitignore` 文件已创建
- [ ] 没有硬编码的密码或密钥

**验证方法**：
```bash
# 查看将要提交的文件列表
git ls-files

# 确认settings.py不在列表中
git ls-files | grep settings.py
# 应该没有输出

# 查看.gitignore是否生效
git status --ignored
```

---

## 📝 后续维护

### 日常提交代码

```bash
# 1. 查看修改的文件
git status

# 2. 添加修改的文件
git add .

# 3. 提交
git commit -m "描述你的修改"

# 4. 推送到远程
git push
```

### 创建分支（可选）

```bash
# 创建新分支
git checkout -b feature/new-feature

# 在新分支上开发
# ... 修改代码 ...

# 提交
git add .
git commit -m "添加新功能"

# 推送新分支
git push -u origin feature/new-feature
```

### 更新README.md

建议在GitHub/GitLab仓库中添加项目说明：

1. 项目简介
2. 功能特性
3. 技术栈
4. 安装步骤
5. 使用说明
6. 截图展示

---

## 🚨 常见问题

### 1. 误提交了敏感文件怎么办？

如果已经提交了 `settings.py` 等敏感文件：

```bash
# 从Git历史中移除文件（但保留本地文件）
git rm --cached Django_Excem/settings.py

# 添加到.gitignore
echo "Django_Excem/settings.py" >> .gitignore

# 提交更改
git add .gitignore
git commit -m "Remove sensitive settings.py from Git"

# 如果已经推送到远程，需要强制推送（谨慎使用）
git push --force
```

**注意**：如果敏感信息已经公开，建议：
1. 立即修改所有密码和密钥
2. 使用GitHub的"Security"功能扫描泄露的密钥

### 2. 如何生成新的SECRET_KEY？

```bash
# 在Django项目中运行
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
```

### 3. 如何配置环境变量（推荐）？

更安全的方式是使用环境变量：

```python
# settings.py
import os
from pathlib import Path

SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key-for-development')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'django_exam'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        # ...
    }
}
```

然后在 `.env` 文件中配置（`.env` 已在 `.gitignore` 中）：
```
SECRET_KEY=your-secret-key-here
DB_NAME=django_exam
DB_USER=root
DB_PASSWORD=your-password
```

### 4. 推送时提示认证失败？

**HTTPS方式**：
- GitHub/GitLab已不再支持密码认证
- 需要使用Personal Access Token（PAT）
- 生成方法：GitHub → Settings → Developer settings → Personal access tokens

**SSH方式**：
```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "your.email@example.com"

# 将公钥添加到GitHub/GitLab
cat ~/.ssh/id_ed25519.pub
# 复制输出，添加到GitHub/GitLab的SSH Keys设置中
```

---

## 📚 相关文档

- [Git官方文档](https://git-scm.com/doc)
- [GitHub文档](https://docs.github.com/)
- [GitLab文档](https://docs.gitlab.com/)
- [Django部署检查清单](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

---

## ✅ 部署完成检查

部署完成后，请确认：

- [ ] 代码已成功推送到远程仓库
- [ ] README.md 已更新
- [ ] 敏感文件未提交
- [ ] 其他开发者可以通过 `settings.example.py` 配置项目
- [ ] 项目可以正常克隆和运行

---

**文档生成时间**: 2025-12-09  
**适用平台**: GitHub, GitLab, Gitee


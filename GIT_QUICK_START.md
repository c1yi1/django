# Git部署快速参考

## 🚀 一键部署（推荐）

### Windows
```bash
deploy_to_git.bat
```

### PowerShell
```powershell
.\deploy_to_git.ps1
```

---

## 📝 手动部署（3步）

### 1. 初始化并提交
```bash
git init
git add .
git commit -m "Initial commit: 智能学习系统项目"
```

### 2. 在GitHub/GitLab创建仓库
- GitHub: https://github.com/new
- GitLab: https://gitlab.com/projects/new
- Gitee: https://gitee.com/projects/new

### 3. 连接并推送
```bash
git remote add origin <你的仓库地址>
git branch -M main
git push -u origin main
```

---

## ✅ 安全检查

部署前确认：
- [ ] `settings.py` 不在Git跟踪中
- [ ] `media/` 目录不在Git跟踪中
- [ ] `.gitignore` 文件已创建

验证命令：
```bash
git status
git ls-files | grep settings.py  # 应该没有输出
```

---

## 📚 详细文档

- **完整指南**: `GIT_DEPLOYMENT.md`
- **项目文档**: `README.md`
- **技术栈**: `TECH_STACK.md`
- **ER图**: `ER_DIAGRAM.md`

---

## ⚠️ 常见问题

**Q: 推送时提示认证失败？**  
A: 需要使用Personal Access Token（不是密码），或配置SSH密钥

**Q: 误提交了敏感文件？**  
A: 查看 `GIT_DEPLOYMENT.md` 中的"常见问题"部分

**Q: 如何生成新的SECRET_KEY？**  
A: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`


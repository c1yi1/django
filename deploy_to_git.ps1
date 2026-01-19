# 智能学习系统 - Git部署助手 (PowerShell版本)
# 使用方法：在PowerShell中运行 .\deploy_to_git.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  智能学习系统 - Git部署助手" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否已初始化Git
if (Test-Path .git) {
    Write-Host "[√] Git仓库已初始化" -ForegroundColor Green
} else {
    Write-Host "[*] 正在初始化Git仓库..." -ForegroundColor Yellow
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[×] Git初始化失败，请确保已安装Git" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
    Write-Host "[√] Git仓库初始化成功" -ForegroundColor Green
}

Write-Host ""
Write-Host "[*] 检查敏感文件..." -ForegroundColor Yellow

# 检查settings.py是否在Git跟踪中
$settingsTracked = git ls-files Django_Excem/settings.py 2>$null
if ($settingsTracked) {
    Write-Host "[!] 警告：settings.py已在Git跟踪中，建议移除" -ForegroundColor Yellow
    Write-Host "[*] 正在从Git中移除settings.py（保留本地文件）..." -ForegroundColor Yellow
    git rm --cached Django_Excem/settings.py
    Write-Host "[√] settings.py已从Git跟踪中移除" -ForegroundColor Green
}

Write-Host ""
Write-Host "[*] 查看将要添加的文件..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  请确认以上文件列表" -ForegroundColor Cyan
Write-Host "  确保敏感文件（settings.py, media/等）不在列表中" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "是否继续添加文件？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "已取消" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 0
}

Write-Host ""
Write-Host "[*] 正在添加文件..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[×] 添加文件失败" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host "[√] 文件添加成功" -ForegroundColor Green

Write-Host ""
$commitMsg = Read-Host "请输入提交信息（直接回车使用默认信息）"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Initial commit: 智能学习系统项目"
}

Write-Host ""
Write-Host "[*] 正在创建提交..." -ForegroundColor Yellow
git commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Write-Host "[×] 提交失败" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host "[√] 提交成功" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  下一步操作：" -ForegroundColor Cyan
Write-Host "  1. 在GitHub/GitLab/Gitee创建新仓库" -ForegroundColor Cyan
Write-Host "  2. 复制仓库地址（HTTPS或SSH）" -ForegroundColor Cyan
Write-Host "  3. 运行以下命令连接远程仓库：" -ForegroundColor Cyan
Write-Host ""
Write-Host "  git remote add origin <你的仓库地址>" -ForegroundColor Yellow
Write-Host "  git branch -M main" -ForegroundColor Yellow
Write-Host "  git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "  详细说明请查看 GIT_DEPLOYMENT.md" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$addRemote = Read-Host "是否现在添加远程仓库？(Y/N)"
if ($addRemote -eq "Y" -or $addRemote -eq "y") {
    $remoteUrl = Read-Host "请输入远程仓库地址"
    if (-not [string]::IsNullOrWhiteSpace($remoteUrl)) {
        git remote add origin $remoteUrl
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[×] 添加远程仓库失败（可能已存在）" -ForegroundColor Yellow
            Write-Host "[*] 尝试更新远程仓库地址..." -ForegroundColor Yellow
            git remote set-url origin $remoteUrl
        }
        Write-Host "[√] 远程仓库已添加" -ForegroundColor Green
        
        Write-Host ""
        $pushNow = Read-Host "是否现在推送到远程仓库？(Y/N)"
        if ($pushNow -eq "Y" -or $pushNow -eq "y") {
            git branch -M main 2>$null
            git push -u origin main
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[×] 推送失败，请检查：" -ForegroundColor Red
                Write-Host "    1. 远程仓库地址是否正确" -ForegroundColor Red
                Write-Host "    2. 是否已配置认证（Token或SSH密钥）" -ForegroundColor Red
                Write-Host "    3. 远程仓库是否已创建" -ForegroundColor Red
            } else {
                Write-Host "[√] 代码已成功推送到远程仓库！" -ForegroundColor Green
            }
        }
    }
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
Read-Host "按Enter键退出"


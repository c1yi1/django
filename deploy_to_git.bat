@echo off
chcp 65001 >nul
echo ========================================
echo   智能学习系统 - Git部署助手
echo ========================================
echo.

:: 检查是否已初始化Git
if exist .git (
    echo [√] Git仓库已初始化
) else (
    echo [*] 正在初始化Git仓库...
    git init
    if errorlevel 1 (
        echo [×] Git初始化失败，请确保已安装Git
        pause
        exit /b 1
    )
    echo [√] Git仓库初始化成功
)

echo.
echo [*] 检查敏感文件...

:: 检查settings.py是否在Git跟踪中
git ls-files Django_Excem/settings.py >nul 2>&1
if not errorlevel 1 (
    echo [!] 警告：settings.py已在Git跟踪中，建议移除
    echo [*] 正在从Git中移除settings.py（保留本地文件）...
    git rm --cached Django_Excem/settings.py
    echo [√] settings.py已从Git跟踪中移除
)

echo.
echo [*] 查看将要添加的文件...
git status

echo.
echo ========================================
echo   请确认以上文件列表
echo   确保敏感文件（settings.py, media/等）不在列表中
echo ========================================
echo.
set /p confirm="是否继续添加文件？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo [*] 正在添加文件...
git add .
if errorlevel 1 (
    echo [×] 添加文件失败
    pause
    exit /b 1
)
echo [√] 文件添加成功

echo.
set /p commit_msg="请输入提交信息（直接回车使用默认信息）: "
if "%commit_msg%"=="" (
    set commit_msg=Initial commit: 智能学习系统项目
)

echo.
echo [*] 正在创建提交...
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo [×] 提交失败
    pause
    exit /b 1
)
echo [√] 提交成功

echo.
echo ========================================
echo   下一步操作：
echo   1. 在GitHub/GitLab/Gitee创建新仓库
echo   2. 复制仓库地址（HTTPS或SSH）
echo   3. 运行以下命令连接远程仓库：
echo.
echo   git remote add origin <你的仓库地址>
echo   git branch -M main
echo   git push -u origin main
echo.
echo   详细说明请查看 GIT_DEPLOYMENT.md
echo ========================================
echo.

set /p add_remote="是否现在添加远程仓库？(Y/N): "
if /i "%add_remote%"=="Y" (
    set /p remote_url="请输入远程仓库地址: "
    if not "%remote_url%"=="" (
        git remote add origin "%remote_url%"
        if errorlevel 1 (
            echo [×] 添加远程仓库失败（可能已存在）
            echo [*] 尝试更新远程仓库地址...
            git remote set-url origin "%remote_url%"
        )
        echo [√] 远程仓库已添加
        
        echo.
        set /p push_now="是否现在推送到远程仓库？(Y/N): "
        if /i "%push_now%"=="Y" (
            git branch -M main 2>nul
            git push -u origin main
            if errorlevel 1 (
                echo [×] 推送失败，请检查：
                echo     1. 远程仓库地址是否正确
                echo     2. 是否已配置认证（Token或SSH密钥）
                echo     3. 远程仓库是否已创建
            ) else (
                echo [√] 代码已成功推送到远程仓库！
            )
        )
    )
)

echo.
echo 完成！
pause


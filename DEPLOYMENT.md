# 在线考试平台部署指南

本文档提供多种方式让外部用户访问您的在线考试平台。

---

## 方案一：快速测试（使用内网穿透工具）

### 1.1 使用 ngrok（推荐，最简单）

**步骤：**

1. **下载 ngrok**
   - 访问 https://ngrok.com/download
   - 下载对应系统的版本
   - 解压到任意目录

2. **注册并获取 authtoken**
   - 注册 ngrok 账号（免费）
   - 在 https://dashboard.ngrok.com/get-started/your-authtoken 获取 token
   - 运行：`ngrok config add-authtoken YOUR_TOKEN`

3. **启动 Django 服务器**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. **启动 ngrok**
   ```bash
   ngrok http 8000
   ```

5. **获取公网地址**
   - ngrok 会显示类似：`https://xxxx-xx-xx-xx-xx.ngrok-free.app`
   - 将这个地址分享给外部用户即可访问

**优点：** 快速、简单、免费
**缺点：** 免费版有连接数限制，每次重启地址会变化

---

### 1.2 使用其他内网穿透工具

**花生壳（Oray）**
- 下载：https://hsk.oray.com/
- 注册账号，创建内网穿透映射
- 配置本地端口 8000

**frp（Fast Reverse Proxy）**
- 需要有自己的服务器
- 配置较复杂，但更稳定

---

## 方案二：局域网访问（同一网络）

### 2.1 修改配置

**修改 `Django_Excem/settings.py`：**

```python
# 允许所有主机访问（仅用于局域网）
ALLOWED_HOSTS = ['*']  # 或指定IP ['192.168.1.100']

# 或者更安全的方式，指定具体IP
# ALLOWED_HOSTS = ['192.168.1.100', 'localhost', '127.0.0.1']
```

### 2.2 启动服务器

```bash
# 使用 0.0.0.0 监听所有网络接口
python manage.py runserver 0.0.0.0:8000
```

### 2.3 获取本机IP地址

**Windows:**
```bash
ipconfig
# 查找 IPv4 地址，例如：192.168.1.100
```

**Linux/Mac:**
```bash
ifconfig
# 或
ip addr show
```

### 2.4 访问

- 局域网内其他设备访问：`http://你的IP:8000`
- 例如：`http://192.168.1.100:8000`

**优点：** 简单、快速
**缺点：** 只能在同一局域网内访问

---

## 方案三：云服务器部署（生产环境）

### 3.1 服务器准备

**推荐云服务商：**
- 阿里云
- 腾讯云
- 华为云
- AWS
- 其他VPS服务商

**服务器要求：**
- 最低配置：1核2G内存
- 推荐配置：2核4G内存
- 操作系统：Ubuntu 20.04/22.04 或 CentOS 7/8

### 3.2 服务器环境配置

**1. 更新系统**
```bash
sudo apt update && sudo apt upgrade -y
```

**2. 安装 Python 和 pip**
```bash
sudo apt install python3 python3-pip python3-venv -y
```

**3. 安装 MySQL**
```bash
sudo apt install mysql-server -y
sudo mysql_secure_installation
```

**4. 安装 Nginx**
```bash
sudo apt install nginx -y
```

**5. 安装 Gunicorn**
```bash
pip3 install gunicorn
```

### 3.3 上传项目文件

**方式1：使用 Git**
```bash
git clone YOUR_REPO_URL
cd Django_Excem
```

**方式2：使用 SCP**
```bash
scp -r /本地项目路径 user@服务器IP:/home/user/
```

**方式3：使用 FTP 工具**
- FileZilla
- WinSCP

### 3.4 配置项目

**1. 创建虚拟环境**
```bash
cd /home/user/Django_Excem
python3 -m venv venv
source venv/bin/activate
```

**2. 安装依赖**
```bash
pip install -r requirements.txt
```

**3. 修改 settings.py**

创建 `Django_Excem/settings_production.py`（生产环境配置）：

```python
from .settings import *

# 安全设置
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', '服务器IP']

# 数据库配置（使用环境变量）
import os
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'django_exam'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# 静态文件配置
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# 安全设置
SECURE_SSL_REDIRECT = True  # 如果使用HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

**4. 收集静态文件**
```bash
python manage.py collectstatic --noinput
```

**5. 数据库迁移**
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3.5 配置 Gunicorn

**创建 `gunicorn_config.py`：**
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

**测试运行：**
```bash
gunicorn Django_Excem.wsgi:application --config gunicorn_config.py
```

### 3.6 配置 Systemd 服务

**创建 `/etc/systemd/system/exam-platform.service`：**
```ini
[Unit]
Description=Exam Platform Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/Django_Excem
Environment="PATH=/home/user/Django_Excem/venv/bin"
ExecStart=/home/user/Django_Excem/venv/bin/gunicorn \
    --config /home/user/Django_Excem/gunicorn_config.py \
    Django_Excem.wsgi:application

[Install]
WantedBy=multi-user.target
```

**启动服务：**
```bash
sudo systemctl daemon-reload
sudo systemctl start exam-platform
sudo systemctl enable exam-platform
sudo systemctl status exam-platform
```

### 3.7 配置 Nginx

**创建 `/etc/nginx/sites-available/exam-platform`：**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 重定向到HTTPS（如果配置了SSL）
    # return 301 https://$server_name$request_uri;

    # 静态文件
    location /static/ {
        alias /home/user/Django_Excem/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias /home/user/Django_Excem/media/;
        expires 7d;
    }

    # Django应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 客户端最大上传大小
    client_max_body_size 10M;
}
```

**启用配置：**
```bash
sudo ln -s /etc/nginx/sites-available/exam-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3.8 配置 SSL（HTTPS）

**使用 Let's Encrypt（免费）：**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

**自动续期：**
```bash
sudo certbot renew --dry-run
```

---

## 方案四：Docker 部署（推荐）

### 4.1 创建 Dockerfile

**创建 `Dockerfile`：**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "Django_Excem.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### 4.2 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=your-domain.com,www.your-domain.com
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      - MYSQL_DATABASE=django_exam
      - MYSQL_USER=django_user
      - MYSQL_PASSWORD=your_password
      - MYSQL_ROOT_PASSWORD=root_password
    volumes:
      - mysql_data:/var/lib/mysql

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/usr/share/nginx/html/static
      - ./media:/usr/share/nginx/html/media
    depends_on:
      - web

volumes:
  mysql_data:
```

### 4.3 部署

```bash
docker-compose up -d
```

---

## 安全建议

### 1. 修改 SECRET_KEY
```python
# 生成新的密钥
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 在 settings.py 中使用
SECRET_KEY = '生成的密钥'
```

### 2. 使用环境变量存储敏感信息
```python
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
```

### 3. 配置防火墙
```bash
# Ubuntu
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 4. 定期备份数据库
```bash
# 创建备份脚本
mysqldump -u root -p django_exam > backup_$(date +%Y%m%d).sql
```

---

## 常见问题

### Q1: 外部无法访问？
- 检查防火墙设置
- 检查 ALLOWED_HOSTS 配置
- 确认服务器端口已开放

### Q2: 静态文件无法加载？
- 运行 `python manage.py collectstatic`
- 检查 Nginx 配置中的静态文件路径
- 检查文件权限

### Q3: 数据库连接失败？
- 检查 MySQL 服务是否运行
- 检查数据库用户权限
- 检查防火墙是否允许 MySQL 端口

### Q4: 502 Bad Gateway？
- 检查 Gunicorn 服务是否运行
- 查看日志：`sudo journalctl -u exam-platform -f`
- 检查 Nginx 配置

---

## 快速开始（推荐）

**最简单的方式：使用 ngrok**

1. 修改 `settings.py`：
   ```python
   ALLOWED_HOSTS = ['*']
   ```

2. 启动服务器：
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

3. 启动 ngrok：
   ```bash
   ngrok http 8000
   ```

4. 分享 ngrok 提供的地址即可！

---

## 联系支持

如有问题，请查看项目文档或提交 Issue。






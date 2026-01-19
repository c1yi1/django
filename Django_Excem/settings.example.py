"""
Django settings for Django_Excem project.

这是一个示例配置文件，请复制为 settings.py 并修改其中的敏感信息。

使用方法：
1. 复制此文件：cp settings.example.py settings.py
2. 修改 settings.py 中的 SECRET_KEY 和数据库密码
3. settings.py 已在 .gitignore 中，不会被提交到Git
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# 请生成新的SECRET_KEY，不要使用示例中的值
# 生成方法：python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = 'your-secret-key-here'  # 请替换为你的SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# 允许外部访问的主机列表
# 开发环境：使用 '*' 允许所有主机（不推荐用于生产环境）
# 生产环境：请指定具体的域名或IP地址，例如：['example.com', 'www.example.com', '192.168.1.100']
ALLOWED_HOSTS = ['*']  # 开发测试用，生产环境请修改为具体域名

# CSRF 信任的源（用于 ngrok 等内网穿透工具）
# 注意：Django 不支持通配符（如 'https://*.ngrok-free.app'）
# 
# 解决方案：
# 1. 手动添加你的 ngrok 域名（最可靠，推荐）
# 2. 使用自定义中间件自动添加（已配置，但可能不够及时）
#
# 使用 ngrok 时，请将你的域名添加到这里，例如：
CSRF_TRUSTED_ORIGINS = [
    # 'https://your-ngrok-domain.ngrok-free.dev',  # 替换为你的 ngrok 域名
    # 如果域名变化，添加新的域名到这里
]

# 开发环境配置
if DEBUG:
    # 开发环境下，CSRF Cookie 不需要 HTTPS
    CSRF_COOKIE_SECURE = False
    CSRF_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SECURE = False


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'exam',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 自定义中间件：自动处理 ngrok CSRF（必须在 CSRF 中间件之前）
    'Django_Excem.middleware.NgrokCsrfMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Django_Excem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Django_Excem.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_exam',  # 数据库名称
        'USER': 'root',  # MySQL用户名，请根据实际情况修改
        'PASSWORD': 'your-database-password',  # MySQL密码，请根据实际情况修改
        'HOST': 'localhost',  # 数据库主机
        'PORT': '3306',  # 数据库端口
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 登录相关配置
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


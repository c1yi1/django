"""
自定义中间件：自动处理 ngrok 等内网穿透工具的 CSRF 验证
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class NgrokCsrfMiddleware(MiddlewareMixin):
    """
    自动将 ngrok 域名添加到 CSRF_TRUSTED_ORIGINS
    仅在开发环境下生效
    
    注意：这个中间件需要在 CSRF 中间件之前执行
    """
    
    def process_request(self, request):
        if settings.DEBUG:
            # 获取请求的 Origin 或 Host 头
            origin = request.META.get('HTTP_ORIGIN', '')
            if not origin:
                # 如果没有 Origin，尝试从 Referer 获取
                referer = request.META.get('HTTP_REFERER', '')
                if referer:
                    # 从 Referer 中提取 origin
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}"
            
            # 检查是否是 ngrok 域名
            ngrok_domains = [
                'ngrok-free.app',
                'ngrok-free.dev',
                'ngrok.io',
                'ngrok.app',
            ]
            
            if origin and any(domain in origin for domain in ngrok_domains):
                # 动态添加到 CSRF_TRUSTED_ORIGINS（如果还没有）
                if origin not in settings.CSRF_TRUSTED_ORIGINS:
                    # 注意：直接修改 settings 可能不会立即生效
                    # 更好的方法是使用线程局部存储或全局变量
                    settings.CSRF_TRUSTED_ORIGINS = list(settings.CSRF_TRUSTED_ORIGINS) + [origin]
        
        return None


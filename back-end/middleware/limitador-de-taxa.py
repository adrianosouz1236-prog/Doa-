from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

# Configuração do rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",  # Em produção: redis:// ou memcached://
    strategy="fixed-window"
)

class RateLimiterMiddleware:
    """Middleware para rate limiting personalizado"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        limiter.init_app(app)
        
        # Registrar eventos de rate limit excedido
        @limiter.request_filter
        def request_filter():
            # Pular rate limit para health check
            if request.path == '/health':
                return True
            return False
        
        @app.after_request
        def add_rate_limit_headers(response):
            """Adiciona headers de rate limit na resposta"""
            if hasattr(request, 'view_args'):
                # Implementar lógica de headers se necessário
                pass
            return response
    
    def log_rate_limit_exceeded(self, request):
        """Log quando rate limit é excedido"""
        logger.warning(
            f"Rate limit excedido - IP: {request.remote_addr}, "
            f"Path: {request.path}, User-Agent: {request.headers.get('User-Agent')}"
        )

# Função para obter chave de rate limit personalizada
def get_custom_rate_limit_key():
    """
    Retorna chave personalizada baseada em IP + rota
    Permite limites diferentes por endpoint
    """
    from flask import request
    
    ip = get_remote_address()
    endpoint = request.endpoint or 'unknown'
    
    return f"{ip}:{endpoint}"
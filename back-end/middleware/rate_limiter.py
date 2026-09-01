# middleware/rate_limiter.py - Rate Limiter
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)


class RateLimiterMiddleware:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        limiter.init_app(app)
        
        @limiter.request_filter
        def request_filter():
            if request.path == '/health':
                return True
            return False
        
        @app.after_request
        def add_rate_limit_headers(response):
            return response
    
    def log_rate_limit_exceeded(self, request_obj):
        logger.warning(
            f"Rate limit excedido - IP: {request_obj.remote_addr}, "
            f"Path: {request_obj.path}"
        )


def get_custom_rate_limit_key():
    ip = get_remote_address()
    endpoint = request.endpoint or 'unknown'
    return f"{ip}:{endpoint}"
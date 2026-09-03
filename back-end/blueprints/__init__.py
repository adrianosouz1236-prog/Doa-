# blueprints/__init__.py
from .auth import auth_bp
from .admin import admin_bp
from .doacoes import doacoes_bp
from .doacoes_financeiras import doacoes_financeiras_bp
from .ong import ong_bp
from .doador import doador_bp
from .public import public_bp
from .comunicacoes import comunicacoes_bp
from .chat import chat_bp
from .suporte import suporte_bp
from .feedback import feedback_bp
from .carteira import carteira_bp
from .ajuda import ajuda_bp
from .usuario import usuario_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'doacoes_bp',
    'doacoes_financeiras_bp',
    'ong_bp',
    'doador_bp',
    'public_bp',
    'comunicacoes_bp',
    'chat_bp',
    'suporte_bp',
    'feedback_bp',
    'carteira_bp',
    'ajuda_bp',
    'usuario_bp'
]

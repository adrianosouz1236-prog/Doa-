from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config
import logging

logger = logging.getLogger(__name__)

def token_required(f):
    """
    Decorator para proteger rotas que requerem autenticação
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Extrair token do header Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token de autenticação é obrigatório'}), 401
        
        try:
            # Decodificar token
            payload = jwt.decode(
                token, 
                Config.JWT_SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # Armazenar informações do usuário no contexto
            g.user_id = payload['user_id']
            g.user_type = payload['user_type']
            g.token_payload = payload
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token inválido: {e}")
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def ong_required(f):
    """
    Decorator que exige que o usuário seja uma ONG
    Deve ser usado após @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_type') or g.user_type != 'ong':
            return jsonify({'error': 'Acesso permitido apenas para ONGs'}), 403
        return f(*args, **kwargs)
    return decorated

def doador_required(f):
    """
    Decorator que exige que o usuário seja um doador
    Deve ser usado após @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_type') or g.user_type != 'doador':
            return jsonify({'error': 'Acesso permitido apenas para doadores'}), 403
        return f(*args, **kwargs)
    return decorated
# middleware/auth_middleware.py - Middleware de Autenticação
from functools import wraps
from flask import request, jsonify, g
import jwt
from config import Config
from database.repositories import OngRepository
import logging

logger = logging.getLogger(__name__)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token de autenticação é obrigatório'}), 401
        
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
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
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_type') or g.user_type != 'ong':
            return jsonify({'error': 'Acesso permitido apenas para ONGs'}), 403
        return f(*args, **kwargs)
    return decorated


def doador_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_type') or g.user_type != 'doador':
            return jsonify({'error': 'Acesso permitido apenas para doadores'}), 403
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_type') or g.user_type != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403
        return f(*args, **kwargs)
    return decorated


def ong_verificada_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'user_type') or g.user_type != 'ong':
            return jsonify({'error': 'Acesso permitido apenas para ONGs'}), 403
        
        ong_id = g.user_id
        ong = OngRepository.buscar_por_id(ong_id)
        
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        status = ong.get('status', 'pendente_verificacao')
        
        if status == 'pendente_verificacao':
            from utils.helpers import calcular_dias_restantes
            dias_restantes = calcular_dias_restantes(ong.get('data_cadastro'), 7)
            
            return jsonify({
                'error': 'Sua ONG ainda não foi verificada.',
                'status': status,
                'dias_restantes': dias_restantes,
                'codigo_verificacao': ong.get('codigo_verificacao'),
                'message': f'Aguardando verificação. Prazo estimado: {dias_restantes} dias.'
            }), 403
        
        if status == 'rejeitado':
            return jsonify({
                'error': 'Sua ONG foi rejeitada.',
                'status': status,
                'motivo': ong.get('motivo_rejeicao'),
                'message': 'Entre em contato com o suporte para mais informações.'
            }), 403
        
        if status == 'bloqueado':
            return jsonify({
                'error': 'Sua ONG está bloqueada.',
                'status': status,
                'message': 'Contate o administrador da plataforma.'
            }), 403
        
        return f(*args, **kwargs)
    return decorated
# blueprints/comunicacoes.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required
from database.repositories import comunicacoes_db
import logging

comunicacoes_bp = Blueprint('comunicacoes', __name__)
logger = logging.getLogger(__name__)


@comunicacoes_bp.route('/nao-lidas', methods=['GET'])
@token_required
def comunicacoes_nao_lidas():
    """Retorna o número de comunicações não lidas do usuário"""
    try:
        usuario_id = g.user_id
        usuario_tipo = g.user_type
        
        # Buscar comunicações não lidas para este usuário
        nao_lidas = 0
        for comunicacao in comunicacoes_db:
            if comunicacao.get('lida', False):
                continue
            if comunicacao.get('tipo') == 'todos':
                nao_lidas += 1
            elif comunicacao.get('tipo') == usuario_tipo:
                nao_lidas += 1
            elif (comunicacao.get('tipo') == 'especifico' and 
                  comunicacao.get('destinatario_id') == usuario_id):
                nao_lidas += 1
        
        return jsonify({'nao_lidas': nao_lidas}), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar comunicações não lidas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@comunicacoes_bp.route('/', methods=['GET'])
@token_required
def listar_comunicacoes():
    """Lista todas as comunicações do usuário"""
    try:
        usuario_id = g.user_id
        usuario_tipo = g.user_type
        
        # Filtrar comunicações para este usuário
        minhas_comunicacoes = []
        for comunicacao in comunicacoes_db:
            if comunicacao.get('tipo') == 'todos':
                minhas_comunicacoes.append(comunicacao)
            elif comunicacao.get('tipo') == usuario_tipo:
                minhas_comunicacoes.append(comunicacao)
            elif (comunicacao.get('tipo') == 'especifico' and 
                  comunicacao.get('destinatario_id') == usuario_id):
                minhas_comunicacoes.append(comunicacao)
        
        return jsonify({'comunicacoes': minhas_comunicacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar comunicações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

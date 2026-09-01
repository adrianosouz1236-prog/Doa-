# blueprints/suporte.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required
from database.repositories import suporte_db
import logging
from datetime import datetime

suporte_bp = Blueprint('suporte', __name__)
logger = logging.getLogger(__name__)

next_suporte_id = 1


@suporte_bp.route('/meus', methods=['GET'])
@token_required
def meus_suportes():
    """Lista os chamados de suporte do usuário"""
    try:
        usuario_id = g.user_id
        
        meus = [s for s in suporte_db.values() if s.get('user_id') == usuario_id]
        
        return jsonify({'suportes': meus}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar suportes: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@suporte_bp.route('/', methods=['POST'])
@token_required
def criar_suporte():
    """Cria um novo chamado de suporte"""
    global next_suporte_id
    
    try:
        data = request.get_json()
        assunto = data.get('assunto')
        mensagem = data.get('mensagem')
        categoria = data.get('categoria', 'duvida')
        
        if not assunto or not mensagem:
            return jsonify({'error': 'Assunto e mensagem são obrigatórios'}), 400
        
        novo_suporte = {
            'id': next_suporte_id,
            'user_id': g.user_id,
            'user_type': g.user_type,
            'user_nome': g.token_payload.get('nome', 'Usuário'),
            'user_email': g.token_payload.get('email', ''),
            'assunto': assunto,
            'mensagem': mensagem,
            'categoria': categoria,
            'data': datetime.now().isoformat(),
            'status': 'aberto',
            'resposta': None,
            'data_resposta': None
        }
        suporte_db[next_suporte_id] = novo_suporte
        next_suporte_id += 1
        
        return jsonify({
            'success': True,
            'message': 'Chamado de suporte criado com sucesso',
            'id': novo_suporte['id']
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar suporte: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

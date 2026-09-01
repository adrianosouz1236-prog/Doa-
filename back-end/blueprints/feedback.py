# blueprints/feedback.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required
import logging
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__)
logger = logging.getLogger(__name__)

# Banco de dados em memória para feedbacks
feedback_db = {}
next_feedback_id = 1


@feedback_bp.route('/', methods=['POST'])
@token_required
def criar_feedback():
    """Cria um novo feedback"""
    global next_feedback_id
    
    try:
        data = request.get_json()
        mensagem = data.get('mensagem')
        tipo = data.get('tipo', 'geral')
        anonimo = data.get('anonimo', False)
        
        if not mensagem or len(mensagem) < 3:
            return jsonify({'error': 'Mensagem deve ter pelo menos 3 caracteres'}), 400
        
        # Obter dados do usuário do token
        user_data = g.token_payload
        
        novo_feedback = {
            'id': next_feedback_id,
            'user_id': g.user_id,
            'user_type': g.user_type,
            'user_email': user_data.get('email', '') if not anonimo else '',
            'user_nome': user_data.get('nome', 'Anônimo') if not anonimo else 'Anônimo',
            'mensagem': mensagem,
            'tipo': tipo,
            'anonimo': anonimo,
            'data': datetime.now().isoformat(),
            'status': 'pendente',
            'resposta': None,
            'data_resposta': None
        }
        feedback_db[next_feedback_id] = novo_feedback
        next_feedback_id += 1
        
        return jsonify({
            'success': True,
            'message': 'Feedback enviado com sucesso!',
            'id': novo_feedback['id']
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar feedback: {e}")
        return jsonify({'error': str(e)}), 500


@feedback_bp.route('/meus', methods=['GET'])
@token_required
def meus_feedbacks():
    """Lista os feedbacks do usuário"""
    try:
        usuario_id = g.user_id
        
        meus = [f for f in feedback_db.values() if f.get('user_id') == usuario_id]
        meus.sort(key=lambda x: x.get('data', ''), reverse=True)
        
        return jsonify({'feedbacks': meus}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar feedbacks: {e}")
        return jsonify({'error': str(e)}), 500

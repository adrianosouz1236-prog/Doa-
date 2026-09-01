# blueprints/chat.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required
import logging
from datetime import datetime

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

# Armazenamento em memória para mensagens
mensagens_chat = []
next_mensagem_id = 1


@chat_bp.route('/nao-lidas', methods=['GET'])
@token_required
def chat_nao_lidas():
    """Retorna o número de mensagens não lidas do usuário"""
    try:
        usuario_id = g.user_id
        
        nao_lidas = len([m for m in mensagens_chat if m.get('destinatario_id') == usuario_id and not m.get('lida', False)])
        
        return jsonify({'nao_lidas': nao_lidas}), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar mensagens não lidas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@chat_bp.route('/mensagens', methods=['GET'])
@token_required
def listar_mensagens():
    """Lista mensagens de uma conversa"""
    try:
        contato_id = request.args.get('com')
        contato_tipo = request.args.get('com_tipo')
        
        if not contato_id:
            return jsonify({'error': 'Parâmetro "com" é obrigatório'}), 400
        
        contato_id = int(contato_id)
        usuario_id = g.user_id
        
        # Buscar mensagens entre os dois usuários
        mensagens = []
        for m in mensagens_chat:
            if (m.get('remetente_id') == usuario_id and m.get('destinatario_id') == contato_id) or \
               (m.get('remetente_id') == contato_id and m.get('destinatario_id') == usuario_id):
                mensagens.append({
                    'mensagem': m.get('mensagem'),
                    'data': m.get('data'),
                    'is_remetente': m.get('remetente_id') == usuario_id
                })
                # Marcar como lida
                if m.get('destinatario_id') == usuario_id:
                    m['lida'] = True
        
        return jsonify({'mensagens': mensagens}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar mensagens: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@chat_bp.route('/mensagens', methods=['POST'])
@token_required
def enviar_mensagem():
    """Envia uma mensagem para outro usuário"""
    global next_mensagem_id
    
    try:
        data = request.get_json()
        destinatario_id = data.get('destinatario_id')
        destinatario_tipo = data.get('destinatario_tipo')
        mensagem = data.get('mensagem')
        
        if not destinatario_id or not mensagem:
            return jsonify({'error': 'Destinatário e mensagem são obrigatórios'}), 400
        
        nova_mensagem = {
            'id': next_mensagem_id,
            'remetente_id': g.user_id,
            'remetente_tipo': g.user_type,
            'destinatario_id': int(destinatario_id),
            'destinatario_tipo': destinatario_tipo,
            'mensagem': mensagem,
            'data': datetime.now().isoformat(),
            'lida': False
        }
        mensagens_chat.append(nova_mensagem)
        next_mensagem_id += 1
        
        return jsonify({
            'success': True,
            'message': 'Mensagem enviada com sucesso',
            'id': nova_mensagem['id']
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

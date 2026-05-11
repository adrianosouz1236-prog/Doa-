from flask import Blueprint, request, jsonify, g
from api.middleware.auth_middleware import token_required, doador_required
from services.doacao_service import DoacaoService
from services.audit_service import AuditService
import logging

doacoes_bp = Blueprint('doacoes', __name__)
logger = logging.getLogger(__name__)

@doacoes_bp.route('/', methods=['POST'])
@token_required
@doador_required
def registrar_doacao():
    """
    Registrar uma nova doação
    Body: { "necessidade_id": 1, "quantidade": 5, "mensagem": "opcional" }
    """
    try:
        dados = request.get_json()
        
        if not dados or not dados.get('necessidade_id') or not dados.get('quantidade'):
            return jsonify({'error': 'necessidade_id e quantidade são obrigatórios'}), 400
        
        if dados['quantidade'] <= 0:
            return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
        
        doacao_service = DoacaoService()
        resultado = doacao_service.registrar_doacao(
            doador_id=g.user_id,
            necessidade_id=dados['necessidade_id'],
            quantidade=dados['quantidade'],
            mensagem=dados.get('mensagem')
        )
        
        if resultado['success']:
            # Registrar no log de auditoria
            AuditService.registrar_evento(
                evento='doacao_registrada',
                usuario_id=g.user_id,
                usuario_tipo='doador',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                detalhes={
                    'necessidade_id': dados['necessidade_id'],
                    'quantidade': dados['quantidade'],
                    'doacao_id': resultado['doacao_id']
                }
            )
            
            return jsonify({
                'message': 'Doação registrada com sucesso!',
                'doacao_id': resultado['doacao_id']
            }), 201
        else:
            return jsonify({'error': resultado['error']}), 400
            
    except Exception as e:
        logger.error(f"Erro ao registrar doação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@doacoes_bp.route('/minhas', methods=['GET'])
@token_required
def listar_minhas_doacoes():
    """
    Lista as doações do usuário autenticado
    Query: ?status=pendente&limite=10&offset=0
    """
    try:
        status = request.args.get('status')
        limite = int(request.args.get('limite', 10))
        offset = int(request.args.get('offset', 0))
        
        doacao_service = DoacaoService()
        
        if g.user_type == 'doador':
            doacoes = doacao_service.listar_doacoes_por_doador(
                g.user_id, status, limite, offset
            )
        else:
            doacoes = doacao_service.listar_doacoes_por_ong(
                g.user_id, status, limite, offset
            )
        
        return jsonify({
            'doacoes': doacoes,
            'total': len(doacoes),
            'limite': limite,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@doacoes_bp.route('/<int:doacao_id>/confirmar', methods=['PUT'])
@token_required
def confirmar_doacao(doacao_id):
    """
    Confirma uma doação (apenas ONG pode confirmar)
    """
    try:
        if g.user_type != 'ong':
            return jsonify({'error': 'Apenas ONGs podem confirmar doações'}), 403
        
        doacao_service = DoacaoService()
        resultado = doacao_service.confirmar_doacao(doacao_id, g.user_id)
        
        if resultado['success']:
            return jsonify({'message': 'Doação confirmada com sucesso'}), 200
        else:
            return jsonify({'error': resultado['error']}), 400
            
    except Exception as e:
        logger.error(f"Erro ao confirmar doação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
# blueprints/doador.py - Rotas de Doador (COMPLETO)
from flask import Blueprint, request, jsonify, g, session
from middleware.auth_middleware import token_required, doador_required
from services.audit_service import AuditService
from security import sanitizar_string, validar_senha_forte, gerar_2fa_secret, gerar_qr_code, verificar_2fa
from database.repositories import DoadorRepository, DoacaoRepository, DoacaoFinanceiraRepository
from utils.helpers import enviar_email
import logging

doador_bp = Blueprint('doador', __name__, url_prefix='/api/doador')
logger = logging.getLogger(__name__)


@doador_bp.route('/perfil', methods=['GET'])
@token_required
@doador_required
def obter_perfil():
    try:
        doador = DoadorRepository.buscar_por_id(g.user_id)
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        return jsonify(doador), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter perfil do doador: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doador_bp.route('/perfil', methods=['PUT'])
@token_required
@doador_required
def atualizar_perfil():
    try:
        dados = request.get_json()
        doador = DoadorRepository.buscar_por_id(g.user_id)
        
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        campos_permitidos = ['nome', 'email', 'telefone', 'endereco', 'cidade', 'uf']
        dados_atualizados = {}
        
        for campo in campos_permitidos:
            if campo in dados:
                dados_atualizados[campo] = sanitizar_string(dados[campo])
        
        DoadorRepository.atualizar(g.user_id, dados_atualizados)
        
        return jsonify({'message': 'Perfil atualizado com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil do doador: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doador_bp.route('/conquistas', methods=['GET'])
@token_required
@doador_required
def listar_conquistas():
    try:
        doador = DoadorRepository.buscar_por_id(g.user_id)
        
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        todas_conquistas = [
            {'id': 'primeira_doacao', 'nome': '🌟 Primeira Doação', 'descricao': 'Realizou sua primeira doação'},
            {'id': 'doador_frequente', 'nome': '⭐ Doador Frequente', 'descricao': 'Realizou 5 doações'},
            {'id': 'doador_master', 'nome': '🏆 Doador Master', 'descricao': 'Realizou 20 doações'},
            {'id': '100_pontos', 'nome': '💎 100 Pontos', 'descricao': 'Acumulou 100 pontos'},
            {'id': '500_pontos', 'nome': '👑 500 Pontos', 'descricao': 'Acumulou 500 pontos'},
            {'id': '1000_pontos', 'nome': '🔥 1000 Pontos', 'descricao': 'Acumulou 1000 pontos'}
        ]
        
        conquistas_doador = doador.get('conquistas', [])
        
        return jsonify({
            'conquistas': conquistas_doador,
            'todas_conquistas': todas_conquistas
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar conquistas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doador_bp.route('/2fa/status', methods=['GET'])
@token_required
@doador_required
def status_2fa():
    try:
        doador = DoadorRepository.buscar_por_id(g.user_id)
        return jsonify({'ativo': doador.get('twofa_ativado', False)}), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status 2FA: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doador_bp.route('/2fa/ativar', methods=['POST'])
@token_required
@doador_required
def ativar_2fa():
    try:
        doador = DoadorRepository.buscar_por_id(g.user_id)
        
        secret = gerar_2fa_secret()
        qr_code = gerar_qr_code(doador.get('email'), secret)
        
        session['2fa_secret'] = secret
        session['2fa_user'] = g.user_id
        
        return jsonify({
            'secret': secret,
            'qr_code': qr_code
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao ativar 2FA: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doador_bp.route('/2fa/confirmar', methods=['POST'])
@token_required
@doador_required
def confirmar_2fa():
    try:
        data = request.json
        codigo = data.get('codigo')
        secret = data.get('secret')
        
        if not codigo or not secret:
            return jsonify({'error': 'Código e secret são obrigatórios'}), 400
        
        if not verificar_2fa(secret, codigo):
            return jsonify({'error': 'Código inválido'}), 400
        
        DoadorRepository.atualizar(g.user_id, {
            'twofa_secret': secret,
            'twofa_ativado': True
        })
        
        return jsonify({'message': '2FA ativado com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao confirmar 2FA: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doador_bp.route('/2fa/desativar', methods=['DELETE'])
@token_required
@doador_required
def desativar_2fa():
    try:
        DoadorRepository.atualizar(g.user_id, {
            'twofa_secret': None,
            'twofa_ativado': False
        })
        
        return jsonify({'message': '2FA desativado com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao desativar 2FA: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
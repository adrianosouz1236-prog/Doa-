# blueprints/doacoes_financeiras.py - Rotas de Doações Financeiras
from flask import Blueprint, request, jsonify, g, redirect
from middleware.auth_middleware import token_required, doador_required, ong_required, ong_verificada_required
from services.audit_service import AuditService
from security import sanitizar_html
from database.repositories import OngRepository, DoadorRepository, DoacaoFinanceiraRepository, CarteiraRepository
from utils.helpers import enviar_email
import logging
import os
from datetime import datetime

doacoes_financeiras_bp = Blueprint('doacoes_financeiras', __name__, url_prefix='/api/doacoes/financeiras')
logger = logging.getLogger(__name__)

# TENTAR IMPORTAR MERCADO PAGO
try:
    from apimercadopago import (
        criar_preferencia_doacao,
        obter_status_doacao,
        calcular_taxas
    )
    MERCADO_PAGO_ATIVO = True
except ImportError:
    MERCADO_PAGO_ATIVO = False
    logger.warning("Mercado Pago não disponível")


@doacoes_financeiras_bp.route('/criar', methods=['POST'])
@token_required
@doador_required
def criar_doacao_financeira():
    if not MERCADO_PAGO_ATIVO:
        return jsonify({'error': 'Mercado Pago não configurado'}), 503
    
    try:
        dados = request.get_json()
        
        if not dados or not dados.get('ong_id') or not dados.get('valor'):
            return jsonify({'error': 'ONG e valor são obrigatórios'}), 400
        
        if dados['valor'] < 1:
            return jsonify({'error': 'Valor mínimo é R$ 1,00'}), 400
        
        doador = DoadorRepository.buscar_por_id(g.user_id)
        ong = OngRepository.buscar_por_id(dados['ong_id'])
        
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        if ong.get('status') != 'verificado':
            return jsonify({'error': 'ONG não está verificada para receber doações'}), 400
        
        resultado_mp = criar_preferencia_doacao(
            doador_nome=doador.get('nome', 'Doador'),
            doador_email=doador.get('email', ''),
            doador_cpf=doador.get('cpf', ''),
            ong_id=dados['ong_id'],
            ong_nome=ong.get('nome'),
            valor=float(dados['valor']),
            mensagem=dados.get('mensagem'),
            recorrente=dados.get('recorrente', False)
        )
        
        if not resultado_mp.get('sucesso'):
            return jsonify({'error': resultado_mp.get('error', 'Erro no Mercado Pago')}), 400
        
        doacao_data = {
            'doador_id': g.user_id,
            'ong_id': dados['ong_id'],
            'valor': float(dados['valor']),
            'taxa_servico': resultado_mp.get('taxa_servico', 0),
            'valor_liquido': resultado_mp.get('valor_liquido', 0),
            'mensagem': sanitizar_html(dados.get('mensagem')),
            'recorrente': dados.get('recorrente', False),
            'external_reference': resultado_mp.get('external_reference'),
            'mp_preference_id': resultado_mp.get('id_preferencia'),
            'status': 'pendente'
        }
        
        doacao_id = DoacaoFinanceiraRepository.criar(doacao_data)
        
        return jsonify({
            'success': True,
            'message': 'Doação iniciada!',
            'redirect_url': resultado_mp.get('url_doacao'),
            'doacao_id': doacao_id,
            'external_reference': resultado_mp.get('external_reference')
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar doação financeira: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doacoes_financeiras_bp.route('/minhas', methods=['GET'])
@token_required
def listar_minhas_doacoes_financeiras():
    try:
        if g.user_type == 'doador':
            doacoes = DoacaoFinanceiraRepository.listar_por_doador(g.user_id)
        else:
            doacoes = DoacaoFinanceiraRepository.listar_por_ong(g.user_id)
        
        return jsonify({'doacoes': doacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doações financeiras: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doacoes_financeiras_bp.route('/ong', methods=['GET'])
@token_required
@ong_required
@ong_verificada_required
def listar_doacoes_financeiras_ong():
    try:
        doacoes = DoacaoFinanceiraRepository.listar_por_ong(g.user_id)
        return jsonify({'doacoes': doacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doações financeiras da ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@doacoes_financeiras_bp.route('/estatisticas', methods=['GET'])
@token_required
def estatisticas_doacoes_financeiras():
    try:
        if g.user_type == 'doador':
            stats = DoacaoFinanceiraRepository.estatisticas_por_doador(g.user_id)
        else:
            stats = DoacaoFinanceiraRepository.estatisticas_por_ong(g.user_id)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


def processar_webhook():
    """Processa webhook do Mercado Pago"""
    try:
        if request.method == 'GET':
            return "OK", 200
        
        data = request.json
        
        if data and data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            if payment_id:
                resultado = obter_status_doacao(payment_id)
                
                if resultado.get('success'):
                    status = resultado.get('status')
                    external_reference = resultado.get('external_reference')
                    
                    if external_reference:
                        doacao = DoacaoFinanceiraRepository.buscar_por_external_reference(external_reference)
                        if doacao:
                            doacao_id = doacao.get('id')
                            DoacaoFinanceiraRepository.atualizar_status(doacao_id, status, datetime.now().isoformat())
                            
                            if status == 'approved':
                                ong_id = doacao.get('ong_id')
                                valor_liquido = doacao.get('valor_liquido', doacao.get('valor', 0))
                                CarteiraRepository.atualizar_saldo(ong_id, valor_liquido, 'entrada')
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
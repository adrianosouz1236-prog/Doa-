# blueprints/carteira.py
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required, ong_required
from database.repositories import CarteiraRepository, OngRepository
from security import criptografar, descriptografar
import logging
from datetime import datetime
import secrets

carteira_bp = Blueprint('carteira', __name__)
logger = logging.getLogger(__name__)

# Banco de dados em memória para transações
transacoes_db = {}
next_transacao_id = 1


@carteira_bp.route('/saldo', methods=['GET'])
@token_required
@ong_required
def obter_saldo():
    """Obtém o saldo da carteira da ONG"""
    try:
        ong_id = g.user_id
        
        carteira = CarteiraRepository.buscar_por_ong(ong_id)
        if not carteira:
            # Criar carteira se não existir
            CarteiraRepository.criar(ong_id)
            carteira = CarteiraRepository.buscar_por_ong(ong_id)
        
        # Buscar dados da ONG para obter conta bancária
        ong = OngRepository.buscar_por_id(ong_id)
        conta_bancaria = None
        if ong and ong.get('conta_bancaria_criptografada'):
            conta_bancaria = descriptografar(ong.get('conta_bancaria_criptografada'))
        
        return jsonify({
            'saldo': carteira.get('saldo', 0),
            'total_recebido': carteira.get('total_recebido', 0),
            'total_sacado': carteira.get('total_sacado', 0),
            'conta_bancaria': conta_bancaria
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter saldo: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@carteira_bp.route('/extrato', methods=['GET'])
@token_required
@ong_required
def obter_extrato():
    """Obtém o extrato de transações da ONG"""
    try:
        ong_id = g.user_id
        
        # Filtrar transações da ONG
        extrato = [t for t in transacoes_db.values() if t.get('ong_id') == ong_id]
        extrato.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
        
        return jsonify({'extrato': extrato}), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter extrato: {e}")
        return jsonify({'error': str(e)}), 500


@carteira_bp.route('/sacar', methods=['POST'])
@token_required
@ong_required
def solicitar_saque():
    """Solicita um saque da carteira"""
    global next_transacao_id
    
    try:
        data = request.get_json()
        valor = data.get('valor')
        conta_bancaria = data.get('conta_bancaria')
        
        if not valor:
            return jsonify({'error': 'Valor é obrigatório'}), 400
        
        try:
            valor = float(valor)
        except:
            return jsonify({'error': 'Valor inválido'}), 400
        
        if valor < 10:
            return jsonify({'error': 'Valor mínimo para saque é R$ 10,00'}), 400
        
        ong_id = g.user_id
        
        # Verificar saldo
        carteira = CarteiraRepository.buscar_por_ong(ong_id)
        if not carteira:
            return jsonify({'error': 'Carteira não encontrada'}), 404
        
        saldo = carteira.get('saldo', 0)
        if saldo < valor:
            return jsonify({'error': f'Saldo insuficiente. Disponível: R$ {saldo:.2f}'}), 400
        
        # Se não forneceu conta bancária, buscar a cadastrada
        if not conta_bancaria:
            ong = OngRepository.buscar_por_id(ong_id)
            if ong and ong.get('conta_bancaria_criptografada'):
                conta_bancaria = descriptografar(ong.get('conta_bancaria_criptografada'))
        
        if not conta_bancaria:
            return jsonify({'error': 'Conta bancária não cadastrada. Informe uma conta para saque.'}), 400
        
        # Registrar transação
        transacao = {
            'id': next_transacao_id,
            'transacao_id': f"SAQ{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(4).upper()}",
            'ong_id': ong_id,
            'valor': valor,
            'tipo': 'saida',
            'conta_bancaria': conta_bancaria,
            'status': 'pendente',
            'data_criacao': datetime.now().isoformat(),
            'data_processamento': None
        }
        transacoes_db[next_transacao_id] = transacao
        next_transacao_id += 1
        
        # Atualizar saldo
        CarteiraRepository.atualizar_saldo(ong_id, valor, 'saida')
        
        return jsonify({
            'message': 'Saque solicitado com sucesso!',
            'transacao_id': transacao['transacao_id'],
            'valor': valor
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao solicitar saque: {e}")
        return jsonify({'error': str(e)}), 500

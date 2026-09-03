# blueprints/usuario.py - Rotas de Usuário (Perfil)
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required
from database.repositories import OngRepository, DoadorRepository, AdminRepository
from security import hash_senha, verificar_senha, sanitizar_string
import logging

usuario_bp = Blueprint('usuario', __name__)
logger = logging.getLogger(__name__)

@usuario_bp.route('/dados', methods=['GET'])
@token_required
def obter_dados():
    """Obtém os dados do usuário logado"""
    try:
        user_id = g.user_id
        user_type = g.user_type
        
        if user_type == 'ong':
            usuario = OngRepository.buscar_por_id(user_id)
        elif user_type == 'doador':
            usuario = DoadorRepository.buscar_por_id(user_id)
        elif user_type == 'admin':
            usuario = AdminRepository.buscar_por_id(user_id)
        else:
            return jsonify({'error': 'Tipo de usuário inválido'}), 400
        
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Remove dados sensíveis
        if 'senha' in usuario:
            del usuario['senha']
        if '_senha' in usuario:
            del usuario['_senha']
        
        return jsonify({'dados': usuario}), 200
    except Exception as e:
        logger.error(f"Erro ao obter dados do usuário: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@usuario_bp.route('/atualizar', methods=['PUT'])
@token_required
def atualizar_dados():
    """Atualiza os dados do usuário"""
    try:
        dados = request.get_json()
        user_id = g.user_id
        user_type = g.user_type
        
        campos_permitidos = ['nome', 'email', 'telefone', 'endereco', 'cidade', 'uf']
        dados_atualizados = {}
        
        for campo in campos_permitidos:
            if campo in dados:
                dados_atualizados[campo] = sanitizar_string(dados[campo])
        
        if user_type == 'ong':
            OngRepository.atualizar(user_id, dados_atualizados)
        elif user_type == 'doador':
            DoadorRepository.atualizar(user_id, dados_atualizados)
        elif user_type == 'admin':
            AdminRepository.atualizar(user_id, dados_atualizados)
        else:
            return jsonify({'error': 'Tipo de usuário inválido'}), 400
        
        return jsonify({'message': 'Dados atualizados com sucesso!'}), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar dados: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@usuario_bp.route('/alterar-senha', methods=['PUT'])
@token_required
def alterar_senha():
    """Altera a senha do usuário"""
    try:
        dados = request.get_json()
        senha_atual = dados.get('senha_atual')
        nova_senha = dados.get('nova_senha')
        
        if not senha_atual or not nova_senha:
            return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
        
        user_id = g.user_id
        user_type = g.user_type
        
        if user_type == 'ong':
            usuario = OngRepository.buscar_por_id(user_id)
        elif user_type == 'doador':
            usuario = DoadorRepository.buscar_por_id(user_id)
        elif user_type == 'admin':
            usuario = AdminRepository.buscar_por_id(user_id)
        else:
            return jsonify({'error': 'Tipo de usuário inválido'}), 400
        
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verifica senha atual
        if not verificar_senha(senha_atual, usuario.get('senha')):
            return jsonify({'error': 'Senha atual incorreta'}), 400
        
        # Valida nova senha
        from security import validar_senha_forte
        valida, msg = validar_senha_forte(nova_senha)
        if not valida:
            return jsonify({'error': f'Senha fraca: {msg}'}), 400
        
        # Atualiza senha
        nova_senha_hash = hash_senha(nova_senha)
        
        if user_type == 'ong':
            OngRepository.atualizar(user_id, {'senha': nova_senha_hash})
        elif user_type == 'doador':
            DoadorRepository.atualizar(user_id, {'senha': nova_senha_hash})
        elif user_type == 'admin':
            AdminRepository.atualizar(user_id, {'senha': nova_senha_hash})
        
        return jsonify({'message': 'Senha alterada com sucesso!'}), 200
    except Exception as e:
        logger.error(f"Erro ao alterar senha: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@usuario_bp.route('/excluir', methods=['DELETE'])
@token_required
def excluir_conta():
    """Solicita exclusão da conta"""
    try:
        user_id = g.user_id
        user_type = g.user_type
        
        from database.repositories import solicitacoes_exclusao_db
        from datetime import datetime
        
        # Cria solicitação de exclusão
        solicitacao = {
            'id': len(solicitacoes_exclusao_db) + 1,
            'usuario_id': user_id,
            'usuario_tipo': user_type,
            'usuario_email': g.token_payload.get('email', ''),
            'usuario_nome': g.token_payload.get('nome', ''),
            'data_solicitacao': datetime.now().isoformat(),
            'status': 'pendente'
        }
        solicitacoes_exclusao_db[solicitacao['id']] = solicitacao
        
        return jsonify({
            'message': 'Solicitação de exclusão enviada com sucesso!',
            'prazo': '30 dias',
            'solicitacao_id': solicitacao['id']
        }), 200
    except Exception as e:
        logger.error(f"Erro ao solicitar exclusão: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

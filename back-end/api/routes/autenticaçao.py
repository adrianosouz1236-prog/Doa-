from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService
from services.audit_service import AuditService
from api.middleware.rate_limiter import limiter
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # Limite para evitar brute force
def login():
    """
    Login de usuário (ONG ou Doador)
    Body: { "email": "usuario@email.com", "senha": "******", "tipo": "ong" }
    """
    try:
        dados = request.get_json()
        
        if not dados or not dados.get('email') or not dados.get('senha'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = dados['email']
        senha = dados['senha']
        tipo = dados.get('tipo', 'doador')  # 'ong' ou 'doador'
        
        # Registrar tentativa de login
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Autenticar usuário
        auth_service = AuthService()
        resultado = auth_service.autenticar(email, senha, tipo)
        
        if resultado['success']:
            # Registrar sucesso no log de auditoria
            AuditService.registrar_evento(
                evento='login_sucesso',
                usuario_id=resultado['usuario_id'],
                usuario_tipo=tipo,
                ip=ip,
                user_agent=user_agent,
                detalhes={'email': email}
            )
            
            return jsonify({
                'token': resultado['token'],
                'usuario': resultado['usuario'],
                'tipo': tipo
            }), 200
        else:
            # Registrar falha no log de auditoria
            AuditService.registrar_evento(
                evento='login_falha',
                usuario_id=None,
                usuario_tipo=tipo,
                ip=ip,
                user_agent=user_agent,
                detalhes={'email': email, 'motivo': resultado['error']},
                gravidade='alerta'
            )
            
            return jsonify({'error': resultado['error']}), 401
            
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/cadastro/ong', methods=['POST'])
@limiter.limit("3 per hour")  # Limite para evitar cadastro em massa
def cadastrar_ong():
    """
    Cadastro de nova ONG
    Body: { "nome": "ONG Exemplo", "cnpj": "12.345.678/0001-90", 
            "email": "contato@ong.org", "senha": "******", ... }
    """
    try:
        dados = request.get_json()
        
        # Validação básica
        campos_obrigatorios = ['nome', 'cnpj', 'email', 'senha']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400
        
        auth_service = AuthService()
        resultado = auth_service.cadastrar_ong(dados)
        
        if resultado['success']:
            # Registrar cadastro
            AuditService.registrar_evento(
                evento='cadastro_ong',
                usuario_id=resultado['ong_id'],
                usuario_tipo='ong',
                ip=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                detalhes={'email': dados['email'], 'nome': dados['nome']}
            )
            
            return jsonify({
                'message': 'ONG cadastrada com sucesso!',
                'ong_id': resultado['ong_id']
            }), 201
        else:
            return jsonify({'error': resultado['error']}), 400
            
    except Exception as e:
        logger.error(f"Erro no cadastro de ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/cadastro/doador', methods=['POST'])
@limiter.limit("5 per hour")
def cadastrar_doador():
    """
    Cadastro de novo doador
    Body: { "nome": "João Silva", "email": "joao@email.com", "senha": "******" }
    """
    try:
        dados = request.get_json()
        
        campos_obrigatorios = ['nome', 'email', 'senha']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400
        
        auth_service = AuthService()
        resultado = auth_service.cadastrar_doador(dados)
        
        if resultado['success']:
            return jsonify({
                'message': 'Doador cadastrado com sucesso!',
                'doador_id': resultado['doador_id']
            }), 201
        else:
            return jsonify({'error': resultado['error']}), 400
            
    except Exception as e:
        logger.error(f"Erro no cadastro de doador: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout do usuário"""
    try:
        # O token JWT é invalidado no cliente
        # Aqui podemos adicionar um blacklist se necessário
        return jsonify({'message': 'Logout realizado com sucesso'}), 200
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
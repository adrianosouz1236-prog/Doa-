# blueprints/auth.py - COMPLETO COM VALIDAÇÃO REAL DE CNPJ
from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService
from services.audit_service import AuditService
from middleware.auth_middleware import token_required
from middleware.rate_limiter import limiter
from security import sanitizar_string, sanitizar_html, validar_senha_forte
from utils.validators import validar_email, validar_cnpj
from utils.helpers import calcular_dias_restantes, BANCOS_BRASIL, enviar_email
from utils.cnpj_validator import validar_cnpj_completo, formatar_cnpj, consultar_cnpj_receita
import logging
import os
import secrets
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)


# =====================================================================
# ROTA DE LOGIN
# =====================================================================

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        dados = request.get_json()
        
        if not dados or not dados.get('email') or not dados.get('senha'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = sanitizar_string(dados['email'])
        senha = dados['senha']
        tipo = sanitizar_string(dados.get('tipo', 'doador'))
        
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        auth_service = AuthService()
        resultado = auth_service.autenticar(email, senha, tipo)
        
        if resultado['success']:
            AuditService.registrar_evento(
                evento='login_sucesso',
                usuario_id=resultado['usuario_id'],
                usuario_tipo=tipo,
                ip=ip,
                user_agent=user_agent,
                detalhes={'email': email}
            )
            
            response_data = {
                'token': resultado['token'],
                'usuario': resultado['usuario'],
                'tipo': tipo
            }
            
            if tipo == 'ong':
                status = resultado.get('status', 'pendente_verificacao')
                response_data['status_verificacao'] = status
                
                if status == 'pendente_verificacao':
                    from database.repositories import OngRepository
                    ong = OngRepository.buscar_por_id(resultado['usuario_id'])
                    if ong:
                        response_data['dias_restantes'] = calcular_dias_restantes(
                            ong.get('data_cadastro'), 7
                        )
                        response_data['codigo_verificacao'] = ong.get('codigo_verificacao')
            
            return jsonify(response_data), 200
        else:
            AuditService.registrar_evento(
                evento='login_falha',
                usuario_id=None,
                usuario_tipo=tipo,
                ip=ip,
                user_agent=user_agent,
                detalhes={'email': email, 'motivo': resultado.get('error')},
                gravidade='alerta'
            )
            return jsonify({'error': resultado.get('error', 'Erro no login')}), 401
            
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ROTA DE CADASTRO DE ONG - COM VALIDAÇÃO REAL DE CNPJ
# =====================================================================

@auth_bp.route('/cadastro/ong', methods=['POST'])
@limiter.limit("3 per hour")
def cadastrar_ong():
    try:
        dados = request.get_json()
        
        # ============================================================
        # VALIDAÇÕES BÁSICAS
        # ============================================================
        campos_obrigatorios = ['nome', 'cnpj', 'email', 'senha']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400
        
        if not dados.get('consentimento_lgpd'):
            return jsonify({
                'error': 'É obrigatório concordar com a Política de Privacidade e Termos de Serviço.'
            }), 400
        
        if not validar_email(dados['email']):
            return jsonify({'error': 'Email inválido'}), 400
        
        # ============================================================
        # VALIDAÇÃO REAL DO CNPJ NA RECEITA FEDERAL
        # ============================================================
        cnpj = dados['cnpj']
        
        # Validação local primeiro (rápida)
        from utils.validators import validar_cnpj as validar_cnpj_local
        if not validar_cnpj_local(cnpj):
            return jsonify({'error': 'CNPJ inválido (dígitos verificadores incorretos)'}), 400
        
        # Validação real na Receita Federal (Brasil API)
        try:
            resultado_validacao = validar_cnpj_completo(cnpj, exigir_ong=True)
            
            if not resultado_validacao['valido']:
                return jsonify({'error': resultado_validacao['error']}), 400
            
            # Dados da Receita Federal
            dados_receita = resultado_validacao['dados']
            
            # Preenche automaticamente os dados da ONG se estiverem vazios
            if not dados.get('nome') or dados.get('nome') == dados['cnpj']:
                dados['nome'] = dados_receita.get('nome', '') or dados_receita.get('razao_social', '')
            
            if not dados.get('cidade'):
                dados['cidade'] = dados_receita.get('cidade', '')
            
            if not dados.get('uf'):
                dados['uf'] = dados_receita.get('uf', '')
            
            if not dados.get('endereco'):
                logradouro = dados_receita.get('logradouro', '')
                numero = dados_receita.get('numero', '')
                bairro = dados_receita.get('bairro', '')
                endereco_completo = f"{logradouro}, {numero}"
                if bairro:
                    endereco_completo += f" - {bairro}"
                dados['endereco'] = endereco_completo
            
            if not dados.get('telefone'):
                dados['telefone'] = dados_receita.get('ddd_telefone_1', '')
            
            # Salvar dados da Receita para referência
            dados['dados_receita'] = dados_receita
            dados['cnpj_validado'] = True
            
            logger.info(f"CNPJ validado com sucesso: {cnpj} - {dados_receita.get('nome', '')}")
            
        except Exception as e:
            logger.error(f"Erro na validação do CNPJ: {e}")
            return jsonify({
                'error': 'Erro ao validar CNPJ na Receita Federal. Tente novamente.'
            }), 500
        
        # ============================================================
        # VALIDAÇÃO DA SENHA
        # ============================================================
        senha_valida, msg = validar_senha_forte(dados['senha'])
        if not senha_valida:
            return jsonify({'error': f'Senha fraca: {msg}'}), 400

        # ============================================================
        # VALIDAÇÃO DOS DADOS BANCÁRIOS
        # ============================================================
        tem_banco = dados.get('banco') or dados.get('agencia') or dados.get('conta')
        
        if tem_banco:
            if not dados.get('banco') or not dados.get('agencia') or not dados.get('conta'):
                return jsonify({
                    'error': 'Para cadastrar conta bancária, preencha Banco, Agência e Conta.'
                }), 400
            
            if dados.get('agencia') and not dados.get('agencia').replace('-', '').isdigit():
                return jsonify({'error': 'Agência deve conter apenas números'}), 400
            
            if dados.get('conta') and not dados.get('conta').replace('-', '').isdigit():
                return jsonify({'error': 'Conta deve conter apenas números e hífen'}), 400
        
        # ============================================================
        # MONTAR DADOS BANCÁRIOS PARA CRIPTOGRAFAR
        # ============================================================
        conta_bancaria = None
        if dados.get('banco') and dados.get('agencia') and dados.get('conta'):
            conta_bancaria = f"{dados['banco']}|{dados['agencia']}|{dados['conta']}|{dados.get('tipo_conta', 'corrente')}"
            dados['conta_bancaria'] = conta_bancaria
        
        # ============================================================
        # CADASTRAR ONG
        # ============================================================
        auth_service = AuthService()
        dados['ip_consentimento'] = request.remote_addr
        dados['user_agent_consentimento'] = request.headers.get('User-Agent')
        dados['ip'] = request.remote_addr
        dados['user_agent'] = request.headers.get('User-Agent')
        
        resultado = auth_service.cadastrar_ong(dados)
        
        if not resultado['success']:
            return jsonify({'error': resultado['error']}), 400
        
        # ============================================================
        # ENVIAR EMAIL PARA A ONG
        # ============================================================
        dados_bancarios_texto = "Não informado"
        if dados.get('banco') and dados.get('agencia') and dados.get('conta'):
            dados_bancarios_texto = f"""
   Banco: {dados['banco']}
   Agência: {dados['agencia']}
   Conta: {dados['conta']}
   Tipo: {dados.get('tipo_conta', 'Corrente')}"""
        
        enviar_email(
            dados['email'],
            'Bem-vindo à Doa+! Seu cadastro está em verificação',
            f'''Olá {dados['nome']},
            
Sua ONG foi cadastrada com sucesso na plataforma Doa+!

🔍 IMPORTANTE: Sua conta está em processo de verificação.
⏳ Prazo estimado: até 7 dias úteis para verificação.

📋 Código de verificação: {resultado['codigo_verificacao']}

🏦 Dados bancários cadastrados:
{dados_bancarios_texto}

✅ CNPJ validado na Receita Federal: {formatar_cnpj(cnpj)}

✉️ Você receberá um email quando sua conta for verificada.
✅ Somente após a verificação você poderá:
   • Cadastrar necessidades de doação
   • Receber doações financeiras
   • Solicitar saques

🔗 Acesse: https://doa-b988.onrender.com/dashboard_ong.html

Equipe Doa+'''
        )
        
        # ============================================================
        # NOTIFICAR ADMIN
        # ============================================================
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@doamais.org')
        enviar_email(
            admin_email,
            f'🔍 Nova ONG aguardando verificação: {dados["nome"]}',
            f'''
Olá Admin,

Uma nova ONG se cadastrou e aguarda verificação:

📋 Dados da ONG:
   Nome: {dados['nome']}
   CNPJ: {formatar_cnpj(cnpj)} (✅ validado na Receita)
   Email: {dados['email']}
   Telefone: {dados.get('telefone', 'N/A')}
   Endereço: {dados.get('endereco', 'N/A')}
   Cidade: {dados.get('cidade', 'N/A')}/{dados.get('uf', 'N/A')}
   ID: {resultado['ong_id']}

🏦 Dados Bancários:
   {dados_bancarios_texto if dados_bancarios_texto != "Não informado" else "   NÃO INFORMADO"}

🔑 Código de Verificação: {resultado['codigo_verificacao']}

📌 Para verificar a ONG, acesse o painel administrativo:
   https://doa-b988.onrender.com/admin_plataform.html

Atenciosamente,
Sistema Doa+'''
        )
        
        return jsonify({
            'message': 'ONG cadastrada com sucesso! Aguarde a verificação da sua conta.',
            'ong_id': resultado['ong_id'],
            'status': 'pendente_verificacao',
            'dias_para_verificacao': resultado['dias_para_verificacao'],
            'codigo_verificacao': resultado['codigo_verificacao']
        }), 201
        
    except Exception as e:
        logger.error(f"Erro no cadastro de ONG: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ROTA PARA CONSULTAR CNPJ (VALIDAÇÃO EM TEMPO REAL)
# =====================================================================

@auth_bp.route('/consultar-cnpj', methods=['POST'])
@limiter.limit("10 per minute")
def consultar_cnpj():
    """
    Rota para consultar CNPJ em tempo real (usado pelo frontend)
    Body: { "cnpj": "12.345.678/0001-90" }
    """
    try:
        dados = request.get_json()
        cnpj = dados.get('cnpj', '').strip()
        
        if not cnpj:
            return jsonify({'success': False, 'error': 'CNPJ é obrigatório'}), 400
        
        # Remove caracteres especiais
        import re
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj_limpo) != 14:
            return jsonify({'success': False, 'error': 'CNPJ deve ter 14 dígitos'}), 400
        
        # Validação local primeiro
        from utils.validators import validar_cnpj as validar_cnpj_local
        if not validar_cnpj_local(cnpj):
            return jsonify({'success': False, 'error': 'CNPJ inválido (dígitos verificadores incorretos)'}), 400
        
        # Consulta na Receita Federal
        resultado = consultar_cnpj_receita(cnpj_limpo)
        
        if not resultado['success']:
            return jsonify({
                'success': False,
                'error': resultado['error']
            }), 400
        
        # Verifica se é ONG
        natureza = resultado.get('natureza_codigo', '')
        if natureza not in NATUREZA_ONG:
            return jsonify({
                'success': False,
                'error': f'CNPJ não é de uma ONG/Associação. Natureza: {resultado.get("natureza_descricao", "Desconhecida")}'
            }), 400
        
        # Retorna dados formatados
        return jsonify({
            'success': True,
            'dados': {
                'nome': resultado.get('nome', ''),
                'razao_social': resultado.get('razao_social', ''),
                'cidade': resultado.get('cidade', ''),
                'uf': resultado.get('uf', ''),
                'cep': resultado.get('cep', ''),
                'logradouro': resultado.get('logradouro', ''),
                'numero': resultado.get('numero', ''),
                'bairro': resultado.get('bairro', ''),
                'telefone': resultado.get('telefone', ''),
                'email': resultado.get('email', ''),
                'situacao': resultado.get('situacao', ''),
                'natureza_descricao': resultado.get('natureza_descricao', '')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na consulta de CNPJ: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ROTA DE CADASTRO DE DOADOR
# =====================================================================

@auth_bp.route('/cadastro/doador', methods=['POST'])
@limiter.limit("5 per hour")
def cadastrar_doador():
    try:
        dados = request.get_json()
        
        campos_obrigatorios = ['nome', 'email', 'senha']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400
        
        if not dados.get('consentimento_lgpd'):
            return jsonify({
                'error': 'É obrigatório concordar com a Política de Privacidade e Termos de Serviço.'
            }), 400
        
        if not validar_email(dados['email']):
            return jsonify({'error': 'Email inválido'}), 400
        
        senha_valida, msg = validar_senha_forte(dados['senha'])
        if not senha_valida:
            return jsonify({'error': f'Senha fraca: {msg}'}), 400
        
        dados['ip_consentimento'] = request.remote_addr
        dados['user_agent_consentimento'] = request.headers.get('User-Agent')
        
        auth_service = AuthService()
        resultado = auth_service.cadastrar_doador(dados)
        
        if not resultado['success']:
            return jsonify({'error': resultado['error']}), 400
        
        enviar_email(
            dados['email'],
            'Bem-vindo à Doa+!',
            f'''Olá {dados['nome']},

Seu cadastro na plataforma Doa+ foi realizado com sucesso!

🔗 Acesse: https://doa-b988.onrender.com/login.html

Equipe Doa+'''
        )
        
        return jsonify({
            'message': 'Doador cadastrado com sucesso!',
            'doador_id': resultado['doador_id']
        }), 201
        
    except Exception as e:
        logger.error(f"Erro no cadastro de doador: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ROTA DE LOGOUT
# =====================================================================

@auth_bp.route('/logout', methods=['POST'])
def logout():
    try:
        return jsonify({'message': 'Logout realizado com sucesso'}), 200
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ROTAS DE RECUPERAÇÃO DE SENHA
# =====================================================================

codigos_recuperacao = {}

@auth_bp.route('/recuperar-senha/solicitar', methods=['POST'])
@limiter.limit("3 per hour")
def solicitar_recuperacao_senha():
    try:
        data = request.json
        email = sanitizar_string(data.get('email', ''))
        
        if not email:
            return jsonify({'success': False, 'error': 'E-mail é obrigatório'}), 400
        
        if not validar_email(email):
            return jsonify({'success': False, 'error': 'E-mail inválido'}), 400
        
        from database.repositories import OngRepository, DoadorRepository, AdminRepository
        
        usuario = OngRepository.buscar_por_email(email)
        usuario_tipo = 'ong'
        usuario_id = None
        
        if usuario:
            usuario_id = usuario.get('id')
        else:
            usuario = DoadorRepository.buscar_por_email(email)
            usuario_tipo = 'doador'
            if usuario:
                usuario_id = usuario.get('id')
        
        if not usuario:
            usuario = AdminRepository.buscar_por_email(email)
            if usuario:
                usuario_tipo = 'admin'
                usuario_id = usuario.get('id')
        
        if not usuario:
            return jsonify({'success': False, 'error': 'E-mail não encontrado'}), 404
        
        codigo = ''.join(str(secrets.randbelow(10)) for _ in range(6))
        
        codigos_recuperacao[email] = {
            'codigo': codigo,
            'timestamp': datetime.now(),
            'tentativas': 0,
            'usuario_id': usuario_id,
            'usuario_tipo': usuario_tipo
        }
        
        if os.getenv('FLASK_ENV') == 'development':
            print(f"🔑 Código de recuperação para {email}: {codigo}")
            return jsonify({
                'success': True,
                'message': 'Código enviado com sucesso!',
                'codigo': codigo
            }), 200
        
        enviar_email(
            email,
            '🔑 Código de Recuperação - Doa+',
            f'Olá {usuario.get("nome")},\n\nSeu código de recuperação é: {codigo}\n\nO código é válido por 15 minutos.\n\nEquipe Doa+'
        )
        
        return jsonify({
            'success': True,
            'message': 'Código enviado para seu e-mail!'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao solicitar recuperação: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/recuperar-senha/verificar', methods=['POST'])
@limiter.limit("5 per minute")
def verificar_codigo_recuperacao():
    try:
        data = request.json
        email = sanitizar_string(data.get('email', ''))
        codigo = data.get('codigo', '')
        
        if not email or not codigo:
            return jsonify({'success': False, 'error': 'E-mail e código são obrigatórios'}), 400
        
        if email not in codigos_recuperacao:
            return jsonify({'success': False, 'error': 'Solicitação não encontrada'}), 404
        
        dados = codigos_recuperacao[email]
        
        if (datetime.now() - dados['timestamp']).total_seconds() > 900:
            del codigos_recuperacao[email]
            return jsonify({'success': False, 'error': 'Código expirado. Solicite um novo.'}), 400
        
        if dados['tentativas'] >= 5:
            del codigos_recuperacao[email]
            return jsonify({'success': False, 'error': 'Muitas tentativas. Solicite um novo código.'}), 400
        
        if dados['codigo'] != codigo:
            dados['tentativas'] += 1
            return jsonify({'success': False, 'error': f'Código inválido. Tentativas restantes: {5 - dados["tentativas"]}'}), 400
        
        token_temp = secrets.token_urlsafe(32)
        dados['token_temp'] = token_temp
        
        return jsonify({
            'success': True,
            'message': 'Código verificado com sucesso!',
            'token_id': token_temp
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar código: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


@auth_bp.route('/recuperar-senha/redefinir', methods=['POST'])
def redefinir_senha():
    try:
        data = request.json
        email = sanitizar_string(data.get('email', ''))
        nova_senha = data.get('nova_senha', '')
        token_temp = data.get('token_id', '')
        
        if not email or not nova_senha:
            return jsonify({'success': False, 'error': 'E-mail e nova senha são obrigatórios'}), 400
        
        if email not in codigos_recuperacao:
            return jsonify({'success': False, 'error': 'Solicitação não encontrada'}), 404
        
        dados = codigos_recuperacao[email]
        
        if dados.get('token_temp') != token_temp:
            return jsonify({'success': False, 'error': 'Token inválido'}), 400
        
        if (datetime.now() - dados['timestamp']).total_seconds() > 900:
            del codigos_recuperacao[email]
            return jsonify({'success': False, 'error': 'Sessão expirada. Solicite um novo código.'}), 400
        
        senha_valida, msg = validar_senha_forte(nova_senha)
        if not senha_valida:
            return jsonify({'success': False, 'error': f'Senha fraca: {msg}'}), 400
        
        from security import hash_senha
        from database.repositories import OngRepository, DoadorRepository, AdminRepository
        
        nova_senha_hash = hash_senha(nova_senha)
        
        if dados['usuario_tipo'] == 'ong':
            OngRepository.atualizar(dados['usuario_id'], {'senha': nova_senha_hash})
        elif dados['usuario_tipo'] == 'doador':
            DoadorRepository.atualizar(dados['usuario_id'], {'senha': nova_senha_hash})
        elif dados['usuario_tipo'] == 'admin':
            AdminRepository.atualizar(dados['usuario_id'], {'senha': nova_senha_hash})
        
        del codigos_recuperacao[email]
        
        return jsonify({
            'success': True,
            'message': 'Senha redefinida com sucesso!'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ROTA PARA VERIFICAR STATUS DA CONTA
# =====================================================================

@auth_bp.route('/me', methods=['GET'])
@token_required
def me():
    try:
        user_id = g.user_id
        user_type = g.user_type
        
        if user_type == 'ong':
            from database.repositories import OngRepository
            usuario = OngRepository.buscar_por_id(user_id)
        elif user_type == 'doador':
            from database.repositories import DoadorRepository
            usuario = DoadorRepository.buscar_por_id(user_id)
        elif user_type == 'admin':
            from database.repositories import AdminRepository
            usuario = AdminRepository.buscar_por_id(user_id)
        else:
            return jsonify({'error': 'Tipo de usuário inválido'}), 400
        
        if not usuario:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if 'senha' in usuario:
            del usuario['senha']
        if '_senha' in usuario:
            del usuario['_senha']
        
        return jsonify(usuario), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
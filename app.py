from flask import Flask, jsonify, send_from_directory, request, session, make_response, redirect, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
import jwt
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import re
import json
import secrets
import requests
import bcrypt
import bleach
import random
from config import get_config
from security import (
    sanitizar_html, sanitizar_string, validar_senha_forte,
    criptografar, descriptografar, verificar_recaptcha,
    verificar_tentativas_login, registrar_tentativa_login,
    gerar_csrf_token, verificar_csrf_token, add_security_headers,
    registrar_evento_seguranca, configurar_sessao_segura, logger,
    gerar_2fa_secret, gerar_qr_code, verificar_2fa
)

# =====================================================================
# IMPORTAÇÃO DO MERCADO PAGO
# =====================================================================

try:
    from apimercadopago import (
        criar_preferencia_doacao,
        testar_conexao_direta,
        verificar_ambiente_mercado_pago,
        obter_status_doacao,
        cancelar_doacao,
        calcular_taxas
    )
    MERCADO_PAGO_ATIVO = True
    print("✅ Mercado Pago módulo carregado com sucesso!")
except ImportError as e:
    MERCADO_PAGO_ATIVO = False
    print(f"⚠️ Módulo apimercadopago não encontrado: {e}")
    print("   Funcionalidades de Mercado Pago indisponíveis.")
    criar_preferencia_doacao = None
    testar_conexao_direta = None
    verificar_ambiente_mercado_pago = None
    obter_status_doacao = None
    cancelar_doacao = None
    calcular_taxas = None

# ==================== PDF REPORT ====================
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
    PDF_SUPPORT = True
    print("✅ ReportLab carregado com sucesso!")
except ImportError:
    PDF_SUPPORT = False
    print("⚠️ ReportLab não instalado. Relatórios PDF não estarão disponíveis.")

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# Inicializar app
app = Flask(__name__, static_folder=TEMPLATES_DIR, static_url_path='')

# ==================== CONFIGURAÇÕES ====================
config = get_config()
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
app.config['DEBUG'] = config.DEBUG
app.config['PORT'] = config.PORT
app.config['HOST'] = config.HOST
app.config['GOOGLE_MAPS_API_KEY'] = config.GOOGLE_MAPS_API_KEY

# Configurar sessão segura
configurar_sessao_segura(app)

# Configurar CORS
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# ==================== BANCO DE DADOS SIMULADO ====================
ongs_db = {}
doadores_db = {}
necessidades_db = {}
doacoes_db = {}
doacoes_financeiras_db = {}
transacoes_db = {}
carteiras_db = {}
pagamentos_db = {}
logs_db = []
ong_fotos_db = {}
ong_eventos_db = {}
ong_parcerias_db = {}
advertencias_db = {}
feedback_db = {}
suporte_db = {}
comunicacoes_db = []
avaliacoes_db = {}
metas_db = {}
voluntariado_db = {}
inscricoes_voluntariado_db = {}
chat_mensagens_db = []
relatorios_db = []
solicitacoes_exclusao_db = {}
notificacoes_preferencias_db = {}
relatorios_anuais_db = {}

# =====================================================================
# CARTEIRA DA PLATAFORMA - NOVAS VARIÁVEIS
# =====================================================================
carteira_plataforma = {
    'saldo': 0.0,
    'total_taxas': 0.0,
    'total_sacado': 0.0,
    'extrato': [],
    'data_atualizacao': datetime.now()
}
next_saque_plataforma_id = 1

# IDs auto-incremento
next_ong_id = 1
next_doador_id = 1
next_necessidade_id = 1
next_doacao_id = 1
next_doacao_financeira_id = 1
next_transacao_id = 1
next_carteira_id = 1
next_pagamento_id = 1
next_log_id = 1
next_evento_id = 1
next_parceria_id = 1
next_foto_id = 1
next_advertencia_id = 1
next_feedback_id = 1
next_suporte_id = 1
next_comunicacao_id = 1
next_avaliacao_id = 1
next_meta_id = 1
next_vaga_id = 1
next_inscricao_id = 1
next_mensagem_id = 1
next_relatorio_id = 1
next_solicitacao_id = 1
next_relatorio_anual_id = 1

# ==================== UTILS ====================

def is_development():
    return os.getenv('FLASK_ENV', 'development') == 'development' or app.config['DEBUG']

def gerar_token(usuario_id, email, tipo):
    payload = {
        'user_id': usuario_id,
        'email': email,
        'tipo': tipo,
        'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verificar_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Token não fornecido'}), 401
        
        token = token.split(' ')[1]
        payload = verificar_token(token)
        if not payload:
            return jsonify({'error': 'Token inválido ou expirado'}), 401
        
        request.user_payload = payload
        return f(*args, **kwargs)
    return decorated

def registrar_log(evento, usuario=None, ip=None, gravidade='baixa'):
    global next_log_id
    ip = ip or request.remote_addr if request else 'unknown'
    log = {
        'id': next_log_id,
        'data': datetime.now(),
        'evento': evento,
        'usuario': usuario,
        'ip': ip,
        'gravidade': gravidade
    }
    logs_db.append(log)
    next_log_id += 1
    return log

def hash_senha(senha):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha, hash_armazenado):
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))

def validar_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_cnpj(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    return len(cnpj) == 14

def validar_cpf(cpf):
    if not cpf:
        return True
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    if digito1 == 10:
        digito1 = 0
    if digito1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    if digito2 == 10:
        digito2 = 0
    if digito2 != int(cpf[10]):
        return False
    return True

def enviar_email(destinatario, assunto, mensagem):
    print(f"📧 Email enviado para {destinatario}")
    print(f"   Assunto: {assunto}")
    print(f"   Mensagem: {mensagem[:100]}...")
    return True

def gerar_id_transacao():
    return f"DOA{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(4).upper()}"

# ==================== DECORATOR DE SEGURANÇA ====================

def security_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            ip = request.remote_addr
            pode, mensagem = verificar_tentativas_login(ip)
            if not pode:
                return jsonify({'error': mensagem}), 429
            
            token = request.headers.get('X-CSRF-Token')
            if not token or not verificar_csrf_token(token):
                return jsonify({'error': 'CSRF token inválido'}), 403
        
        return f(*args, **kwargs)
    return decorated

# =====================================================================
# FUNÇÕES DA CARTEIRA DA PLATAFORMA
# =====================================================================

def registrar_taxa_plataforma(valor_taxa, transacao_id, descricao):
    """
    Registra uma taxa na carteira da plataforma
    """
    global carteira_plataforma
    
    carteira_plataforma['saldo'] += valor_taxa
    carteira_plataforma['total_taxas'] += valor_taxa
    carteira_plataforma['data_atualizacao'] = datetime.now()
    
    carteira_plataforma['extrato'].append({
        'id': len(carteira_plataforma['extrato']) + 1,
        'transacao_id': transacao_id,
        'tipo': 'taxa',
        'valor': valor_taxa,
        'descricao': descricao,
        'data': datetime.now()
    })
    
    registrar_log(
        f'Taxa de R$ {valor_taxa:.2f} registrada na carteira da plataforma - {descricao}',
        gravidade='media'
    )

def registrar_saque_plataforma(valor, conta_bancaria, descricao):
    """
    Registra um saque da carteira da plataforma
    """
    global carteira_plataforma
    
    if carteira_plataforma['saldo'] < valor:
        return {'success': False, 'error': 'Saldo insuficiente na carteira da plataforma'}
    
    if valor < 10:
        return {'success': False, 'error': 'Valor mínimo para saque é R$ 10,00'}
    
    carteira_plataforma['saldo'] -= valor
    carteira_plataforma['total_sacado'] += valor
    carteira_plataforma['data_atualizacao'] = datetime.now()
    
    carteira_plataforma['extrato'].append({
        'id': len(carteira_plataforma['extrato']) + 1,
        'transacao_id': gerar_id_transacao(),
        'tipo': 'saque',
        'valor': valor,
        'conta_bancaria': conta_bancaria,
        'descricao': descricao,
        'data': datetime.now()
    })
    
    registrar_log(
        f'Saque de R$ {valor:.2f} da carteira da plataforma - {descricao}',
        gravidade='alta'
    )
    
    return {'success': True, 'saldo_restante': carteira_plataforma['saldo']}

def obter_dados_carteira_plataforma():
    """
    Retorna os dados da carteira da plataforma
    """
    return {
        'saldo': carteira_plataforma['saldo'],
        'total_taxas': carteira_plataforma['total_taxas'],
        'total_sacado': carteira_plataforma['total_sacado'],
        'extrato': carteira_plataforma['extrato'][-50:],  # Últimas 50 transações
        'data_atualizacao': carteira_plataforma['data_atualizacao'].isoformat()
    }

# ==================== ROTAS DE PÁGINAS HTML ====================

@app.route('/')
def index():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(filepath):
        return send_from_directory(TEMPLATES_DIR, filename)
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/index.html')
def index_html():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory(TEMPLATES_DIR, 'login.html')

@app.route('/recuperar_senha.html')
def recuperar_senha_page():
    return send_from_directory(TEMPLATES_DIR, 'recuperar_senha.html')

@app.route('/redefinir_senha.html')
def redefinir_senha_page():
    return send_from_directory(TEMPLATES_DIR, 'redefinir_senha.html')

@app.route('/cadastro.html')
def cadastro_page():
    return send_from_directory(TEMPLATES_DIR, 'cadastro.html')

@app.route('/cadastro_ong.html')
def cadastro_ong_page():
    return send_from_directory(TEMPLATES_DIR, 'cadastro_ong.html')

@app.route('/cadastro_doador.html')
def cadastro_doador_page():
    return send_from_directory(TEMPLATES_DIR, 'cadastro_doador.html')

@app.route('/dashboard_ong.html')
def dashboard_ong_page():
    return send_from_directory(TEMPLATES_DIR, 'dashboard_ong.html')

@app.route('/perfil_ong.html')
def perfil_ong_page():
    return send_from_directory(TEMPLATES_DIR, 'perfil_ong.html')

@app.route('/perfil_doador.html')
def perfil_doador_page():
    return send_from_directory(TEMPLATES_DIR, 'perfil_doador.html')

@app.route('/admin_plataform.html')
def admin_plataform_page():
    return send_from_directory(TEMPLATES_DIR, 'admin_plataform.html')

@app.route('/feedback.html')
def feedback_page():
    return send_from_directory(TEMPLATES_DIR, 'feedback.html')

@app.route('/suporte.html')
def suporte_page():
    return send_from_directory(TEMPLATES_DIR, 'suporte.html')

@app.route('/central_ajuda.html')
def central_ajuda_page():
    return send_from_directory(TEMPLATES_DIR, 'central_ajuda.html')

@app.route('/politicas_privacidade.html')
def politicas_privacidade_page():
    return send_from_directory(TEMPLATES_DIR, 'politicas_privacidade.html')

@app.route('/termos_servico.html')
def termos_uso_page():
    return send_from_directory(TEMPLATES_DIR, 'termos_servico.html')

@app.route('/transparencia.html')
def transparencia_page():
    return send_from_directory(TEMPLATES_DIR, 'transparencia.html')

@app.route('/doacoes_financeiras.html')
def doacoes_financeiras_page():
    return send_from_directory(TEMPLATES_DIR, 'doacoes_financeiras.html')

@app.route('/carteira.html')
def carteira_page():
    return send_from_directory(TEMPLATES_DIR, 'carteira.html')

@app.route('/voluntariado')
def voluntariado_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/ranking')
def ranking_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/necessidades')
def necessidades_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/ongs')
def ongs_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/sobre')
def sobre_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/estilos.css/<path:filename>')
def serve_css(filename):
    css_path = os.path.join(TEMPLATES_DIR, 'estilos.css', filename)
    if os.path.exists(css_path):
        return send_from_directory(os.path.join(TEMPLATES_DIR, 'estilos.css'), filename)
    return '', 404

@app.route('/javascript.js/<path:filename>')
def serve_js(filename):
    js_path = os.path.join(TEMPLATES_DIR, 'javascript.js', filename)
    if os.path.exists(js_path):
        return send_from_directory(os.path.join(TEMPLATES_DIR, 'javascript.js'), filename)
    return '', 404

# ==================== ROTAS DE API ====================

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    total_doacoes_financeiras = len([d for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado'])
    total_valor_financeiro = sum(d.get('valor', 0) for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado')
    total_voluntarios = sum(v.get('vagas_preenchidas', 0) for v in voluntariado_db.values())
    
    return jsonify({
        'total_ongs': len([o for o in ongs_db.values() if o.get('status') == 'ativo']),
        'total_doadores': len([d for d in doadores_db.values() if d.get('status') == 'ativo']),
        'total_doacoes': len(doacoes_db),
        'total_itens': sum(d.get('quantidade', 0) for d in doacoes_db.values()),
        'total_voluntarios': total_voluntarios,
        'total_doacoes_financeiras': total_doacoes_financeiras,
        'total_valor_financeiro': total_valor_financeiro
    }), 200

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/api/auth/login', methods=['POST'])
@security_required
def login():
    data = request.json
    email = sanitizar_string(data.get('email', ''))
    senha = data.get('senha', '')
    tipo = sanitizar_string(data.get('tipo', ''))
    recaptcha_token = data.get('recaptcha_token', '')
    
    ip = request.remote_addr
    
    if not email or not senha or not tipo:
        registrar_tentativa_login(ip, sucesso=False)
        return jsonify({'error': 'Email, senha e tipo são obrigatórios'}), 400
    
    if not verificar_recaptcha(recaptcha_token):
        registrar_tentativa_login(ip, sucesso=False)
        return jsonify({'error': 'Verificação de segurança falhou. Tente novamente.'}), 400
    
    usuario = None
    user_id = None
    
    if tipo == 'admin':
        if email == 'admin@doamais.org' and senha == 'admin123':
            usuario = {
                'id': 999,
                'nome': 'Administrador',
                'email': email
            }
            user_id = 999
    
    elif tipo == 'ong':
        for uid, ong in ongs_db.items():
            if ong.get('email') == email:
                if verificar_senha(senha, ong.get('senha')):
                    usuario = ong
                    user_id = uid
                break
    
    elif tipo == 'doador':
        for uid, doador in doadores_db.items():
            if doador.get('email') == email:
                if verificar_senha(senha, doador.get('senha')):
                    usuario = doador
                    user_id = uid
                break
    
    if not usuario:
        registrar_tentativa_login(ip, sucesso=False)
        registrar_log(f'Tentativa de login falhou: {email}', usuario=email, ip=ip, gravidade='media')
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    
    if tipo == 'ong' and usuario.get('status') == 'bloqueado':
        return jsonify({'error': 'ONG bloqueada. Contate o administrador.'}), 403
    
    registrar_tentativa_login(ip, sucesso=True)
    token = gerar_token(user_id, email, tipo)
    registrar_log(f'Login realizado: {email} ({tipo})', usuario=email, ip=ip)
    
    return jsonify({
        'token': token,
        'usuario': {
            'id': user_id,
            'nome': usuario.get('nome'),
            'email': usuario.get('email')
        },
        'tipo': tipo
    }), 200

@app.route('/api/auth/cadastro/ong', methods=['POST'])
@security_required
def cadastro_ong():
    global next_ong_id
    
    data = request.json
    nome = sanitizar_string(data.get('nome', ''))
    cnpj = sanitizar_string(data.get('cnpj', ''))
    email = sanitizar_string(data.get('email', ''))
    senha = data.get('senha', '')
    telefone = sanitizar_string(data.get('telefone', ''))
    endereco = sanitizar_string(data.get('endereco', ''))
    cidade = sanitizar_string(data.get('cidade', ''))
    uf = sanitizar_string(data.get('uf', ''))
    descricao = sanitizar_string(data.get('descricao', ''))
    conta_bancaria = criptografar(data.get('conta_bancaria', ''))
    recaptcha_token = data.get('recaptcha_token', '')
    
    if not nome or not cnpj or not email or not senha:
        return jsonify({'error': 'Nome, CNPJ, email e senha são obrigatórios'}), 400
    
    if not verificar_recaptcha(recaptcha_token):
        return jsonify({'error': 'Verificação de segurança falhou. Tente novamente.'}), 400
    
    if not validar_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    if not validar_cnpj(cnpj):
        return jsonify({'error': 'CNPJ inválido'}), 400
    
    senha_valida, msg = validar_senha_forte(senha)
    if not senha_valida:
        return jsonify({'error': f'Senha fraca: {msg}'}), 400
    
    for ong in ongs_db.values():
        if ong.get('email') == email:
            return jsonify({'error': 'Email já cadastrado'}), 409
    
    ong_id = next_ong_id
    ongs_db[ong_id] = {
        'id': ong_id,
        'nome': nome,
        'cnpj': cnpj,
        'email': email,
        'senha': hash_senha(senha),
        'telefone': telefone,
        'endereco': endereco,
        'cidade': cidade,
        'uf': uf,
        'descricao': descricao,
        'logo_url': None,
        'status': 'ativo',
        'data_cadastro': datetime.now(),
        'total_advertencias': 0,
        'latitude': None,
        'longitude': None,
        'endereco_completo': None,
        'media_avaliacao': 0,
        'total_avaliacoes': 0,
        'conta_bancaria': conta_bancaria,
        'email_confirmado': False,
        'consentimento_lgpd': False,
        'data_consentimento': None
    }
    
    carteiras_db[ong_id] = {
        'ong_id': ong_id,
        'saldo': 0,
        'total_recebido': 0,
        'total_sacado': 0,
        'data_criacao': datetime.now(),
        'data_atualizacao': datetime.now()
    }
    
    next_ong_id += 1
    registrar_log(f'Nova ONG cadastrada: {nome}', usuario=email)
    
    enviar_email(
        email,
        'Bem-vindo à Doa+! Confirme seu cadastro',
        f'Olá {nome},\n\nSeu cadastro na plataforma Doa+ foi realizado com sucesso!\n\nAcesse: http://localhost:5000/login.html\n\nEquipe Doa+'
    )
    
    return jsonify({'message': 'ONG cadastrada com sucesso!', 'ong_id': ong_id}), 201

@app.route('/api/auth/cadastro/doador', methods=['POST'])
@security_required
def cadastro_doador():
    global next_doador_id
    
    data = request.json
    nome = sanitizar_string(data.get('nome', ''))
    email = sanitizar_string(data.get('email', ''))
    senha = data.get('senha', '')
    telefone = sanitizar_string(data.get('telefone', ''))
    cpf = sanitizar_string(data.get('cpf', ''))
    recaptcha_token = data.get('recaptcha_token', '')
    
    if not nome or not email or not senha:
        return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
    
    if not verificar_recaptcha(recaptcha_token):
        return jsonify({'error': 'Verificação de segurança falhou. Tente novamente.'}), 400
    
    if not validar_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    if cpf and not validar_cpf(cpf):
        return jsonify({'error': 'CPF inválido'}), 400
    
    senha_valida, msg = validar_senha_forte(senha)
    if not senha_valida:
        return jsonify({'error': f'Senha fraca: {msg}'}), 400
    
    for doador in doadores_db.values():
        if doador.get('email') == email:
            return jsonify({'error': 'Email já cadastrado'}), 409
    
    doador_id = next_doador_id
    doadores_db[doador_id] = {
        'id': doador_id,
        'nome': nome,
        'email': email,
        'senha': hash_senha(senha),
        'telefone': telefone,
        'cpf': cpf,
        'status': 'ativo',
        'data_cadastro': datetime.now(),
        'total_doacoes': 0,
        'pontuacao': 0,
        'conquistas': [],
        'email_confirmado': False,
        'consentimento_lgpd': False,
        'data_consentimento': None,
        'endereco': None,
        'cidade': None,
        'uf': None,
        'total_itens': 0,
        '2fa_secret': None,
        '2fa_ativado': False,
        'data_atualizacao': datetime.now()
    }
    
    next_doador_id += 1
    registrar_log(f'Novo doador cadastrado: {nome}', usuario=email)
    
    enviar_email(
        email,
        'Bem-vindo à Doa+! Confirme seu cadastro',
        f'Olá {nome},\n\nSeu cadastro na plataforma Doa+ foi realizado com sucesso!\n\nAcesse: http://localhost:5000/login.html\n\nEquipe Doa+'
    )
    
    return jsonify({'message': 'Doador cadastrado com sucesso!', 'doador_id': doador_id}), 201

# ==================== ROTAS DE RECUPERAÇÃO DE SENHA ====================

codigos_recuperacao = {}

@app.route('/api/auth/recuperar-senha/solicitar', methods=['POST'])
@security_required
def solicitar_recuperacao_senha():
    data = request.json
    email = sanitizar_string(data.get('email', ''))
    
    if not email:
        return jsonify({'success': False, 'error': 'E-mail é obrigatório'}), 400
    
    if not validar_email(email):
        return jsonify({'success': False, 'error': 'E-mail inválido'}), 400
    
    usuario = None
    usuario_tipo = None
    usuario_id = None
    
    for uid, ong in ongs_db.items():
        if ong.get('email') == email:
            usuario = ong
            usuario_tipo = 'ong'
            usuario_id = uid
            break
    
    if not usuario:
        for uid, doador in doadores_db.items():
            if doador.get('email') == email:
                usuario = doador
                usuario_tipo = 'doador'
                usuario_id = uid
                break
    
    if not usuario:
        return jsonify({'success': False, 'error': 'E-mail não encontrado'}), 404
    
    codigo = ''.join(str(random.randint(0, 9)) for _ in range(6))
    
    codigos_recuperacao[email] = {
        'codigo': codigo,
        'timestamp': datetime.now(),
        'tentativas': 0,
        'usuario_id': usuario_id,
        'usuario_tipo': usuario_tipo
    }
    
    if is_development():
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

@app.route('/api/auth/recuperar-senha/verificar', methods=['POST'])
@security_required
def verificar_codigo_recuperacao():
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

@app.route('/api/auth/recuperar-senha/redefinir', methods=['POST'])
@security_required
def redefinir_senha():
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
    
    nova_senha_hash = hash_senha(nova_senha)
    
    if dados['usuario_tipo'] == 'ong':
        ong = ongs_db.get(dados['usuario_id'])
        if ong:
            ong['senha'] = nova_senha_hash
            ong['data_atualizacao'] = datetime.now()
    elif dados['usuario_tipo'] == 'doador':
        doador = doadores_db.get(dados['usuario_id'])
        if doador:
            doador['senha'] = nova_senha_hash
            doador['data_atualizacao'] = datetime.now()
    
    del codigos_recuperacao[email]
    
    registrar_log(f'Senha redefinida para {email}', usuario=email, gravidade='media')
    
    return jsonify({
        'success': True,
        'message': 'Senha redefinida com sucesso!'
    }), 200

# ==================== ROTAS DE CONFIGURAÇÃO ====================

@app.route('/api/config/csrf-token', methods=['GET'])
def get_csrf_token():
    token = gerar_csrf_token()
    return jsonify({'csrf_token': token}), 200

@app.route('/api/config/recaptcha-key', methods=['GET'])
def get_recaptcha_key():
    site_key = os.getenv('RECAPTCHA_SITE_KEY', '')
    if is_development() and not site_key:
        site_key = 'dev-key-not-required'
    return jsonify({'site_key': site_key}), 200

# ==================== ROTAS DE NECESSIDADES (PÚBLICAS) ====================

@app.route('/api/necessidades', methods=['GET'])
def listar_necessidades():
    params = request.args
    cidade = params.get('cidade', '').lower()
    categoria = params.get('categoria', '')
    page = int(params.get('page', 1))
    limit = int(params.get('limit', 10))
    urgent = params.get('urgente', 'false').lower() == 'true'
    busca = params.get('busca', '').lower()
    
    necessidades_lista = []
    for nec_id, nec in necessidades_db.items():
        if nec.get('status') != 'aberta':
            continue
        
        ong = ongs_db.get(nec.get('ong_id'))
        if not ong or ong.get('status') != 'ativo':
            continue
        
        if cidade and cidade not in ong.get('cidade', '').lower():
            continue
        if categoria and nec.get('categoria') != categoria:
            continue
        if urgent and nec.get('urgencia') != 'alta':
            continue
        if busca and busca not in nec.get('titulo', '').lower() and busca not in nec.get('descricao', '').lower():
            continue
        
        necessidades_lista.append({
            'id': nec_id,
            'ong_id': nec.get('ong_id'),
            'ong_nome': ong.get('nome'),
            'cidade': ong.get('cidade'),
            'titulo': nec.get('titulo'),
            'descricao': nec.get('descricao'),
            'categoria': nec.get('categoria'),
            'quantidade_necessaria': nec.get('quantidade_necessaria'),
            'quantidade_recebida': nec.get('quantidade_recebida', 0),
            'urgencia': nec.get('urgencia'),
            'status': nec.get('status'),
            'data_criacao': nec.get('data_criacao'),
            'media_avaliacao_ong': ong.get('media_avaliacao', 0)
        })
    
    start = (page - 1) * limit
    end = start + limit
    paginated = necessidades_lista[start:end]
    
    return jsonify({
        'necessidades': paginated,
        'total': len(necessidades_lista),
        'page': page,
        'limit': limit,
        'has_more': end < len(necessidades_lista)
    }), 200

# ==================== ROTAS DE DOAÇÕES (ITENS) ====================

@app.route('/api/doacoes', methods=['POST'])
@token_required
@security_required
def registrar_doacao():
    global next_doacao_id
    
    data = request.json
    necessidade_id = data.get('necessidade_id')
    quantidade = data.get('quantidade')
    mensagem = sanitizar_html(data.get('mensagem', ''))
    
    user_type = request.user_payload.get('tipo')
    if user_type != 'doador':
        return jsonify({'error': 'Apenas doadores podem registrar doações'}), 403
    
    doador_id = request.user_payload.get('user_id')
    doador = doadores_db.get(doador_id)
    
    if not doador:
        return jsonify({'error': 'Doador não encontrado'}), 404
    
    necessidade = necessidades_db.get(necessidade_id)
    if not necessidade or necessidade.get('status') != 'aberta':
        return jsonify({'error': 'Necessidade não encontrada ou inativa'}), 404
    
    if quantidade <= 0:
        return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
    
    doacao_id = next_doacao_id
    doacoes_db[doacao_id] = {
        'id': doacao_id,
        'doador_id': doador_id,
        'doador_nome': doador.get('nome'),
        'ong_id': necessidade.get('ong_id'),
        'necessidade_id': necessidade_id,
        'item': necessidade.get('titulo'),
        'quantidade': quantidade,
        'mensagem': mensagem,
        'status': 'pendente',
        'data': datetime.now()
    }
    
    necessidade['quantidade_recebida'] = necessidade.get('quantidade_recebida', 0) + quantidade
    doador['total_doacoes'] = doador.get('total_doacoes', 0) + 1
    doador['pontuacao'] = doador.get('pontuacao', 0) + (quantidade * 10)
    doador['total_itens'] = doador.get('total_itens', 0) + quantidade
    
    verificar_conquistas(doador_id)
    
    for meta in metas_db.values():
        if meta.get('ong_id') == necessidade.get('ong_id') and meta.get('status') == 'ativa':
            if meta.get('categoria') == 'geral' or meta.get('categoria') == necessidade.get('categoria'):
                meta['quantidade_atual'] = meta.get('quantidade_atual', 0) + quantidade
                if meta['quantidade_atual'] >= meta['meta_quantidade']:
                    meta['status'] = 'concluida'
    
    if necessidade['quantidade_recebida'] >= necessidade['quantidade_necessaria']:
        necessidade['status'] = 'encerrada'
    
    next_doacao_id += 1
    registrar_log(f'Nova doação registrada: {quantidade} itens', usuario=doador.get('email'))
    
    ong = ongs_db.get(necessidade.get('ong_id'))
    if ong and ong.get('email'):
        enviar_email(
            ong.get('email'),
            f'Nova doação para {necessidade.get("titulo")}',
            f'Olá {ong.get("nome")},\n\nVocê recebeu uma nova doação!\n\nItem: {necessidade.get("titulo")}\nQuantidade: {quantidade}\nDoador: {doador.get("nome")}\n\nAcesse o dashboard para confirmar a doação.'
        )
    
    return jsonify({'message': 'Doação registrada com sucesso!', 'doacao_id': doacao_id}), 201

@app.route('/api/doacoes/minhas', methods=['GET'])
@token_required
def listar_minhas_doacoes_itens():
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Acesso restrito a doadores'}), 403
    
    doador_id = request.user_payload.get('user_id')
    doacoes = []
    
    for doc_id, doc in doacoes_db.items():
        if doc.get('doador_id') == doador_id:
            ong = ongs_db.get(doc.get('ong_id'))
            doacoes.append({
                'id': doc_id,
                'data': doc.get('data').isoformat() if hasattr(doc.get('data'), 'isoformat') else str(doc.get('data')),
                'ong_nome': ong.get('nome') if ong else 'Desconhecida',
                'item': doc.get('item'),
                'quantidade': doc.get('quantidade'),
                'status': doc.get('status')
            })
    
    doacoes.sort(key=lambda x: x.get('data', ''), reverse=True)
    return jsonify({'doacoes': doacoes}), 200

def verificar_conquistas(doador_id):
    doador = doadores_db.get(doador_id)
    if not doador:
        return
    
    conquistas = doador.get('conquistas', [])
    total_doacoes = doador.get('total_doacoes', 0)
    pontuacao = doador.get('pontuacao', 0)
    
    if total_doacoes >= 1 and 'primeira_doacao' not in conquistas:
        conquistas.append('primeira_doacao')
    if total_doacoes >= 5 and 'doador_frequente' not in conquistas:
        conquistas.append('doador_frequente')
    if total_doacoes >= 20 and 'doador_master' not in conquistas:
        conquistas.append('doador_master')
    if pontuacao >= 100 and '100_pontos' not in conquistas:
        conquistas.append('100_pontos')
    if pontuacao >= 500 and '500_pontos' not in conquistas:
        conquistas.append('500_pontos')
    if pontuacao >= 1000 and '1000_pontos' not in conquistas:
        conquistas.append('1000_pontos')
    
    doador['conquistas'] = conquistas

# ==================== ROTAS DE ONGs (PÚBLICAS) ====================

@app.route('/api/ongs', methods=['GET'])
def listar_ongs():
    params = request.args
    cidade = params.get('cidade', '').lower()
    
    ongs_lista = []
    for ong_id, ong in ongs_db.items():
        if ong.get('status') != 'ativo':
            continue
        
        if cidade and cidade not in ong.get('cidade', '').lower():
            continue
        
        ongs_lista.append({
            'id': ong_id,
            'nome': ong.get('nome'),
            'cidade': ong.get('cidade'),
            'uf': ong.get('uf'),
            'descricao': ong.get('descricao'),
            'logo_url': ong.get('logo_url'),
            'latitude': ong.get('latitude'),
            'longitude': ong.get('longitude'),
            'media_avaliacao': ong.get('media_avaliacao', 0),
            'total_avaliacoes': ong.get('total_avaliacoes', 0)
        })
    
    return jsonify({'ongs': ongs_lista}), 200

@app.route('/api/ongs/<int:ong_id>', methods=['GET'])
def get_ong_public_profile(ong_id):
    ong = ongs_db.get(ong_id)
    
    if not ong or ong.get('status') != 'ativo':
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    fotos = [f for f in ong_fotos_db.values() if f.get('ong_id') == ong_id]
    eventos = [e for e in ong_eventos_db.values() 
               if e.get('ong_id') == ong_id and e.get('status') == 'ativo'
               and e.get('data_evento') > datetime.now()]
    eventos.sort(key=lambda x: x.get('data_evento'))
    parcerias = [p for p in ong_parcerias_db.values() 
                 if p.get('ong_id') == ong_id and p.get('status') == 'ativa']
    necessidades_ativas = [n for n in necessidades_db.values() 
                          if n.get('ong_id') == ong_id and n.get('status') == 'aberta']
    
    avaliacoes = [a for a in avaliacoes_db.values() if a.get('ong_id') == ong_id]
    
    return jsonify({
        'id': ong_id,
        'nome': ong.get('nome'),
        'email': ong.get('email'),
        'telefone': ong.get('telefone'),
        'endereco': ong.get('endereco'),
        'cidade': ong.get('cidade'),
        'uf': ong.get('uf'),
        'descricao': ong.get('descricao'),
        'logo_url': ong.get('logo_url'),
        'latitude': ong.get('latitude'),
        'longitude': ong.get('longitude'),
        'endereco_completo': ong.get('endereco_completo'),
        'fotos': fotos,
        'eventos': eventos,
        'parcerias': parcerias,
        'necessidades': necessidades_ativas,
        'avaliacoes': [{
            'id': a.get('id'),
            'doador_nome': a.get('doador_nome'),
            'nota': a.get('nota'),
            'comentario': a.get('comentario'),
            'data': a.get('data').isoformat() if hasattr(a.get('data'), 'isoformat') else str(a.get('data'))
        } for a in avaliacoes],
        'media_avaliacao': ong.get('media_avaliacao', 0),
        'total_avaliacoes': ong.get('total_avaliacoes', 0)
    }), 200

# ==================== ROTAS DE ONG - DASHBOARD ====================

@app.route('/api/ongs/dashboard', methods=['GET'])
@token_required
def ong_dashboard():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    total_necessidades = len([n for n in necessidades_db.values() if n.get('ong_id') == ong_id])
    total_doacoes = len([d for d in doacoes_db.values() if d.get('ong_id') == ong_id])
    total_itens = sum(d.get('quantidade', 0) for d in doacoes_db.values() if d.get('ong_id') == ong_id)
    total_doadores = len(set(d.get('doador_id') for d in doacoes_db.values() if d.get('ong_id') == ong_id))
    total_eventos = len([e for e in ong_eventos_db.values() if e.get('ong_id') == ong_id])
    total_doacoes_financeiras = len([d for d in doacoes_financeiras_db.values() if d.get('ong_id') == ong_id and d.get('status') == 'confirmado'])
    
    carteira = carteiras_db.get(ong_id, {})
    
    return jsonify({
        'total_necessidades': total_necessidades,
        'total_doacoes': total_doacoes,
        'total_itens': total_itens,
        'total_doadores': total_doadores,
        'total_eventos': total_eventos,
        'total_doacoes_financeiras': total_doacoes_financeiras,
        'saldo_carteira': carteira.get('saldo', 0)
    }), 200

# ==================== ROTAS DE ONG - PERFIL ====================

@app.route('/api/ongs/perfil', methods=['GET'])
@token_required
def get_ong_perfil():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    ong = ongs_db.get(ong_id)
    
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    return jsonify({
        'nome': ong.get('nome'),
        'email': ong.get('email'),
        'telefone': ong.get('telefone'),
        'endereco': ong.get('endereco'),
        'cidade': ong.get('cidade'),
        'uf': ong.get('uf'),
        'descricao': ong.get('descricao'),
        'logo_url': ong.get('logo_url'),
        'conta_bancaria': descriptografar(ong.get('conta_bancaria', ''))
    }), 200

@app.route('/api/ongs/perfil', methods=['PUT'])
@token_required
def update_ong_perfil():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    data = request.json
    ong_id = request.user_payload.get('user_id')
    ong = ongs_db.get(ong_id)
    
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    ong['nome'] = data.get('nome', ong.get('nome'))
    ong['email'] = data.get('email', ong.get('email'))
    ong['telefone'] = data.get('telefone', ong.get('telefone'))
    ong['endereco'] = data.get('endereco', ong.get('endereco'))
    ong['cidade'] = data.get('cidade', ong.get('cidade'))
    ong['uf'] = data.get('uf', ong.get('uf'))
    ong['descricao'] = data.get('descricao', ong.get('descricao'))
    ong['logo_url'] = data.get('logo_url', ong.get('logo_url'))
    if data.get('conta_bancaria'):
        ong['conta_bancaria'] = criptografar(data.get('conta_bancaria'))
    ong['data_atualizacao'] = datetime.now()
    
    registrar_log(f'Perfil da ONG atualizado', usuario=ong.get('email'))
    
    return jsonify({'message': 'Perfil atualizado com sucesso!'}), 200

# ==================== ROTAS DE ONG - NECESSIDADES ====================

@app.route('/api/ongs/necessidades', methods=['GET'])
@token_required
def listar_necessidades_ong():
    """Lista todas as necessidades de uma ONG específica"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    necessidades = []
    for nec_id, nec in necessidades_db.items():
        if nec.get('ong_id') == ong_id:
            necessidades.append({
                'id': nec_id,
                'titulo': nec.get('titulo'),
                'descricao': nec.get('descricao'),
                'categoria': nec.get('categoria'),
                'quantidade_necessaria': nec.get('quantidade_necessaria'),
                'quantidade_recebida': nec.get('quantidade_recebida', 0),
                'urgencia': nec.get('urgencia'),
                'status': nec.get('status'),
                'data_criacao': nec.get('data_criacao').isoformat() if hasattr(nec.get('data_criacao'), 'isoformat') else str(nec.get('data_criacao'))
            })
    
    return jsonify({'necessidades': necessidades}), 200

@app.route('/api/ongs/necessidades', methods=['POST'])
@token_required
@security_required
def criar_necessidade_ong():
    """Cria uma nova necessidade para a ONG"""
    global next_necessidade_id
    
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    data = request.json
    ong_id = request.user_payload.get('user_id')
    
    titulo = sanitizar_string(data.get('titulo', ''))
    descricao = sanitizar_html(data.get('descricao', ''))
    categoria = data.get('categoria', '')
    quantidade_necessaria = data.get('quantidade_necessaria')
    urgencia = data.get('urgencia', 'media')
    
    if not titulo or not categoria or not quantidade_necessaria:
        return jsonify({'error': 'Título, categoria e quantidade são obrigatórios'}), 400
    
    if quantidade_necessaria <= 0:
        return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
    
    ong = ongs_db.get(ong_id)
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    necessidade = {
        'id': next_necessidade_id,
        'ong_id': ong_id,
        'titulo': titulo,
        'descricao': descricao,
        'categoria': categoria,
        'quantidade_necessaria': quantidade_necessaria,
        'quantidade_recebida': 0,
        'urgencia': urgencia,
        'status': 'aberta',
        'data_criacao': datetime.now()
    }
    
    necessidades_db[next_necessidade_id] = necessidade
    next_necessidade_id += 1
    
    registrar_log(f'Nova necessidade criada: {titulo}', usuario=ong.get('email'))
    
    return jsonify({
        'message': 'Necessidade criada com sucesso!',
        'necessidade_id': necessidade['id']
    }), 201

@app.route('/api/ongs/necessidades/<int:necessidade_id>', methods=['GET'])
@token_required
def obter_necessidade_ong(necessidade_id):
    """Obtém uma necessidade específica da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    necessidade = necessidades_db.get(necessidade_id)
    
    if not necessidade:
        return jsonify({'error': 'Necessidade não encontrada'}), 404
    
    if necessidade.get('ong_id') != ong_id:
        return jsonify({'error': 'Você não tem permissão para acessar esta necessidade'}), 403
    
    return jsonify({
        'id': necessidade_id,
        'titulo': necessidade.get('titulo'),
        'descricao': necessidade.get('descricao'),
        'categoria': necessidade.get('categoria'),
        'quantidade_necessaria': necessidade.get('quantidade_necessaria'),
        'quantidade_recebida': necessidade.get('quantidade_recebida', 0),
        'urgencia': necessidade.get('urgencia'),
        'status': necessidade.get('status'),
        'data_criacao': necessidade.get('data_criacao').isoformat() if hasattr(necessidade.get('data_criacao'), 'isoformat') else str(necessidade.get('data_criacao'))
    }), 200

@app.route('/api/ongs/necessidades/<int:necessidade_id>', methods=['PUT'])
@token_required
@security_required
def atualizar_necessidade_ong(necessidade_id):
    """Atualiza uma necessidade existente"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    necessidade = necessidades_db.get(necessidade_id)
    
    if not necessidade:
        return jsonify({'error': 'Necessidade não encontrada'}), 404
    
    if necessidade.get('ong_id') != ong_id:
        return jsonify({'error': 'Você não tem permissão para editar esta necessidade'}), 403
    
    data = request.json
    
    necessidade['titulo'] = sanitizar_string(data.get('titulo', necessidade.get('titulo')))
    necessidade['descricao'] = sanitizar_html(data.get('descricao', necessidade.get('descricao')))
    necessidade['categoria'] = data.get('categoria', necessidade.get('categoria'))
    
    if data.get('quantidade_necessaria'):
        necessidade['quantidade_necessaria'] = data.get('quantidade_necessaria')
    
    necessidade['urgencia'] = data.get('urgencia', necessidade.get('urgencia'))
    
    registrar_log(f'Necessidade atualizada: {necessidade.get("titulo")}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Necessidade atualizada com sucesso!'}), 200

@app.route('/api/ongs/necessidades/<int:necessidade_id>/encerrar', methods=['PUT'])
@token_required
@security_required
def encerrar_necessidade_ong(necessidade_id):
    """Encerra uma necessidade (marca como concluída)"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    necessidade = necessidades_db.get(necessidade_id)
    
    if not necessidade:
        return jsonify({'error': 'Necessidade não encontrada'}), 404
    
    if necessidade.get('ong_id') != ong_id:
        return jsonify({'error': 'Você não tem permissão para encerrar esta necessidade'}), 403
    
    necessidade['status'] = 'encerrada'
    
    registrar_log(f'Necessidade encerrada: {necessidade.get("titulo")}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Necessidade encerrada com sucesso!'}), 200

# ==================== ROTAS DE ONG - DOAÇÕES (ITENS) ====================

@app.route('/api/ongs/doacoes', methods=['GET'])
@token_required
def listar_doacoes_ong():
    """Lista todas as doações recebidas pela ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    doacoes = []
    for doc_id, doc in doacoes_db.items():
        if doc.get('ong_id') == ong_id:
            doador = doadores_db.get(doc.get('doador_id'))
            necessidade = necessidades_db.get(doc.get('necessidade_id'))
            
            doacoes.append({
                'id': doc_id,
                'doador_nome': doador.get('nome') if doador else 'Anônimo',
                'necessidade_titulo': necessidade.get('titulo') if necessidade else 'N/A',
                'quantidade': doc.get('quantidade'),
                'mensagem': doc.get('mensagem'),
                'status': doc.get('status', 'pendente'),
                'data': doc.get('data').isoformat() if hasattr(doc.get('data'), 'isoformat') else str(doc.get('data'))
            })
    
    return jsonify({'doacoes': doacoes}), 200

@app.route('/api/ongs/doacoes/<int:doacao_id>/confirmar', methods=['PUT'])
@token_required
@security_required
def confirmar_doacao_ong(doacao_id):
    """Confirma uma doação recebida pela ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    doacao = doacoes_db.get(doacao_id)
    
    if not doacao:
        return jsonify({'error': 'Doação não encontrada'}), 404
    
    if doacao.get('ong_id') != ong_id:
        return jsonify({'error': 'Você não tem permissão para confirmar esta doação'}), 403
    
    doacao['status'] = 'confirmada'
    
    registrar_log(f'Doação confirmada: #{doacao_id}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Doação confirmada com sucesso!'}), 200

# ==================== ROTAS DE ONG - DOAÇÕES FINANCEIRAS ====================

@app.route('/api/doacoes/financeiras/ong', methods=['GET'])
@token_required
def listar_doacoes_financeiras_ong():
    """Lista todas as doações financeiras recebidas pela ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    doacoes = []
    for df in doacoes_financeiras_db.values():
        if df.get('ong_id') == ong_id:
            doacoes.append({
                'id': df.get('id'),
                'transacao_id': df.get('transacao_id'),
                'doador_nome': df.get('doador_nome', 'Anônimo'),
                'valor': df.get('valor'),
                'valor_liquido': df.get('valor_liquido', df.get('valor')),
                'taxa_servico': df.get('taxa_servico', 0),
                'mensagem': df.get('mensagem'),
                'metodo_pagamento': df.get('metodo_pagamento'),
                'recorrente': df.get('recorrente', False),
                'status': df.get('status'),
                'data_criacao': df.get('data_criacao').isoformat() if hasattr(df.get('data_criacao'), 'isoformat') else str(df.get('data_criacao')),
                'data_confirmacao': df.get('data_confirmacao').isoformat() if hasattr(df.get('data_confirmacao'), 'isoformat') else str(df.get('data_confirmacao'))
            })
    
    doacoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
    
    return jsonify({'doacoes': doacoes}), 200

# ==================== ROTAS DE ONG - FOTOS ====================

@app.route('/api/ongs/fotos', methods=['GET'])
@token_required
def listar_fotos_ong():
    """Lista todas as fotos da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    fotos = []
    for foto_id, foto in ong_fotos_db.items():
        if foto.get('ong_id') == ong_id:
            fotos.append({
                'id': foto_id,
                'foto_url': foto.get('foto_url'),
                'descricao': foto.get('descricao'),
                'data_upload': foto.get('data_upload').isoformat() if hasattr(foto.get('data_upload'), 'isoformat') else str(foto.get('data_upload'))
            })
    
    return jsonify({'fotos': fotos}), 200

@app.route('/api/ongs/fotos', methods=['POST'])
@token_required
@security_required
def adicionar_foto_ong():
    """Adiciona uma nova foto para a ONG"""
    global next_foto_id
    
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    data = request.json
    ong_id = request.user_payload.get('user_id')
    
    foto_url = data.get('foto_url')
    descricao = sanitizar_string(data.get('descricao', ''))
    
    if not foto_url:
        return jsonify({'error': 'URL da foto é obrigatória'}), 400
    
    # Verificar se a ONG já tem 3 fotos
    fotos_ong = [f for f in ong_fotos_db.values() if f.get('ong_id') == ong_id]
    if len(fotos_ong) >= 3:
        return jsonify({'error': 'Máximo de 3 fotos por ONG'}), 400
    
    foto = {
        'id': next_foto_id,
        'ong_id': ong_id,
        'foto_url': foto_url,
        'descricao': descricao,
        'data_upload': datetime.now()
    }
    
    ong_fotos_db[next_foto_id] = foto
    next_foto_id += 1
    
    registrar_log(f'Nova foto adicionada para ONG #{ong_id}', usuario=request.user_payload.get('email'))
    
    return jsonify({
        'message': 'Foto adicionada com sucesso!',
        'foto_id': foto['id']
    }), 201

@app.route('/api/ongs/fotos/<int:foto_id>', methods=['DELETE'])
@token_required
@security_required
def remover_foto_ong(foto_id):
    """Remove uma foto da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    foto = ong_fotos_db.get(foto_id)
    
    if not foto:
        return jsonify({'error': 'Foto não encontrada'}), 404
    
    if foto.get('ong_id') != ong_id:
        return jsonify({'error': 'Você não tem permissão para remover esta foto'}), 403
    
    del ong_fotos_db[foto_id]
    
    registrar_log(f'Foto removida para ONG #{ong_id}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Foto removida com sucesso!'}), 200

# ==================== ROTAS DE ONG - EVENTOS ====================

@app.route('/api/ongs/eventos', methods=['GET'])
@token_required
def listar_eventos_ong():
    """Lista todos os eventos da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    eventos = []
    for ev_id, ev in ong_eventos_db.items():
        if ev.get('ong_id') == ong_id:
            eventos.append({
                'id': ev_id,
                'titulo': ev.get('titulo'),
                'descricao': ev.get('descricao'),
                'data_evento': ev.get('data_evento').isoformat() if hasattr(ev.get('data_evento'), 'isoformat') else str(ev.get('data_evento')),
                'local_evento': ev.get('local_evento'),
                'endereco': ev.get('endereco'),
                'cidade': ev.get('cidade'),
                'uf': ev.get('uf'),
                'imagem_url': ev.get('imagem_url'),
                'status': ev.get('status')
            })
    
    eventos.sort(key=lambda x: x.get('data_evento', ''))
    
    return jsonify({'eventos': eventos}), 200

@app.route('/api/ongs/eventos', methods=['POST'])
@token_required
@security_required
def criar_evento_ong():
    """Cria um novo evento para a ONG"""
    global next_evento_id
    
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    data = request.json
    ong_id = request.user_payload.get('user_id')
    
    titulo = sanitizar_string(data.get('titulo', ''))
    descricao = sanitizar_html(data.get('descricao', ''))
    data_evento = data.get('data_evento')
    local_evento = sanitizar_string(data.get('local_evento', ''))
    endereco = sanitizar_string(data.get('endereco', ''))
    cidade = sanitizar_string(data.get('cidade', ''))
    uf = sanitizar_string(data.get('uf', ''))
    imagem_url = data.get('imagem_url', '')
    
    if not titulo or not data_evento:
        return jsonify({'error': 'Título e data do evento são obrigatórios'}), 400
    
    try:
        data_evento_parsed = datetime.fromisoformat(data_evento)
    except ValueError:
        return jsonify({'error': 'Data do evento inválida'}), 400
    
    evento = {
        'id': next_evento_id,
        'ong_id': ong_id,
        'titulo': titulo,
        'descricao': descricao,
        'data_evento': data_evento_parsed,
        'local_evento': local_evento,
        'endereco': endereco,
        'cidade': cidade,
        'uf': uf,
        'imagem_url': imagem_url,
        'status': 'ativo',
        'data_criacao': datetime.now()
    }
    
    ong_eventos_db[next_evento_id] = evento
    next_evento_id += 1
    
    registrar_log(f'Novo evento criado: {titulo}', usuario=request.user_payload.get('email'))
    
    return jsonify({
        'message': 'Evento criado com sucesso!',
        'evento_id': evento['id']
    }), 201

@app.route('/api/ongs/eventos/<int:evento_id>/cancelar', methods=['PUT'])
@token_required
@security_required
def cancelar_evento_ong(evento_id):
    """Cancela um evento"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    evento = ong_eventos_db.get(evento_id)
    
    if not evento:
        return jsonify({'error': 'Evento não encontrado'}), 404
    
    if evento.get('ong_id') != ong_id:
        return jsonify({'error': 'Sem permissão'}), 403
    
    evento['status'] = 'cancelado'
    
    registrar_log(f'Evento cancelado: {evento.get("titulo")}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Evento cancelado com sucesso!'}), 200

# ==================== ROTAS DE ONG - PARCERIAS ====================

@app.route('/api/ongs/parcerias', methods=['GET'])
@token_required
def listar_parcerias_ong():
    """Lista todas as parcerias da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    parcerias = []
    for par_id, par in ong_parcerias_db.items():
        if par.get('ong_id') == ong_id:
            parcerias.append({
                'id': par_id,
                'parceiro_nome': par.get('parceiro_nome'),
                'tipo_parceria': par.get('tipo_parceria'),
                'descricao': par.get('descricao'),
                'logo_url': par.get('logo_url'),
                'website_url': par.get('website_url'),
                'status': par.get('status')
            })
    
    return jsonify({'parcerias': parcerias}), 200

@app.route('/api/ongs/parcerias', methods=['POST'])
@token_required
@security_required
def criar_parceria_ong():
    """Cria uma nova parceria para a ONG"""
    global next_parceria_id
    
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    data = request.json
    ong_id = request.user_payload.get('user_id')
    
    parceiro_nome = sanitizar_string(data.get('parceiro_nome', ''))
    tipo_parceria = sanitizar_string(data.get('tipo_parceria', 'empresa'))
    descricao = sanitizar_html(data.get('descricao', ''))
    logo_url = data.get('logo_url', '')
    website_url = data.get('website_url', '')
    
    if not parceiro_nome:
        return jsonify({'error': 'Nome do parceiro é obrigatório'}), 400
    
    parceria = {
        'id': next_parceria_id,
        'ong_id': ong_id,
        'parceiro_nome': parceiro_nome,
        'tipo_parceria': tipo_parceria,
        'descricao': descricao,
        'logo_url': logo_url,
        'website_url': website_url,
        'status': 'ativa',
        'data_cadastro': datetime.now()
    }
    
    ong_parcerias_db[next_parceria_id] = parceria
    next_parceria_id += 1
    
    registrar_log(f'Nova parceria criada: {parceiro_nome}', usuario=request.user_payload.get('email'))
    
    return jsonify({
        'message': 'Parceria criada com sucesso!',
        'parceria_id': parceria['id']
    }), 201

@app.route('/api/ongs/parcerias/<int:parceria_id>/encerrar', methods=['PUT'])
@token_required
@security_required
def encerrar_parceria_ong(parceria_id):
    """Encerra uma parceria"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    parceria = ong_parcerias_db.get(parceria_id)
    
    if not parceria:
        return jsonify({'error': 'Parceria não encontrada'}), 404
    
    if parceria.get('ong_id') != ong_id:
        return jsonify({'error': 'Sem permissão'}), 403
    
    parceria['status'] = 'encerrada'
    
    registrar_log(f'Parceria encerrada: {parceria.get("parceiro_nome")}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Parceria encerrada com sucesso!'}), 200

# ==================== ROTAS DE CARTEIRA ====================

@app.route('/api/carteira/saldo', methods=['GET'])
@token_required
def obter_saldo_carteira():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    carteira = carteiras_db.get(ong_id)
    
    if not carteira:
        return jsonify({
            'saldo': 0,
            'total_recebido': 0,
            'total_sacado': 0,
            'conta_bancaria': '',
            'data_atualizacao': datetime.now().isoformat()
        }), 200
    
    return jsonify({
        'saldo': carteira.get('saldo', 0),
        'total_recebido': carteira.get('total_recebido', 0),
        'total_sacado': carteira.get('total_sacado', 0),
        'conta_bancaria': descriptografar(ongs_db.get(ong_id, {}).get('conta_bancaria', '')),
        'data_atualizacao': carteira.get('data_atualizacao').isoformat() if hasattr(carteira.get('data_atualizacao'), 'isoformat') else str(carteira.get('data_atualizacao'))
    }), 200

@app.route('/api/carteira/sacar', methods=['POST'])
@token_required
@security_required
def sacar_carteira():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    data = request.json
    valor = data.get('valor')
    conta_bancaria = data.get('conta_bancaria')
    
    if not valor or not conta_bancaria:
        return jsonify({'error': 'Valor e conta bancária são obrigatórios'}), 400
    
    if valor < 10:
        return jsonify({'error': 'Valor mínimo para saque é R$ 10,00'}), 400
    
    ong_id = request.user_payload.get('user_id')
    carteira = carteiras_db.get(ong_id)
    
    if not carteira or carteira.get('saldo', 0) < valor:
        return jsonify({'error': 'Saldo insuficiente'}), 400
    
    global next_transacao_id
    atualizar_carteira_ong(ong_id, valor, 'saida')
    
    transacao_saque = {
        'id': next_transacao_id,
        'transacao_id': gerar_id_transacao(),
        'ong_id': ong_id,
        'valor': valor,
        'tipo': 'saque',
        'status': 'processando',
        'conta_bancaria': conta_bancaria,
        'data_criacao': datetime.now(),
        'data_processamento': None
    }
    transacoes_db[next_transacao_id] = transacao_saque
    next_transacao_id += 1
    
    registrar_log(
        f'Saque de R$ {valor:.2f} solicitado pela ONG #{ong_id}',
        usuario=request.user_payload.get('email'),
        gravidade='media'
    )
    
    return jsonify({
        'message': 'Saque solicitado com sucesso!',
        'transacao_id': transacao_saque['transacao_id'],
        'valor': valor,
        'status': 'processando'
    }), 200

@app.route('/api/carteira/extrato', methods=['GET'])
@token_required
def obter_extrato():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    transacoes = []
    for t in transacoes_db.values():
        if t.get('ong_id') == ong_id:
            transacoes.append({
                'id': t.get('id'),
                'transacao_id': t.get('transacao_id'),
                'valor': t.get('valor'),
                'tipo': t.get('tipo'),
                'status': t.get('status'),
                'data_criacao': t.get('data_criacao').isoformat() if hasattr(t.get('data_criacao'), 'isoformat') else str(t.get('data_criacao')),
                'data_processamento': t.get('data_processamento').isoformat() if hasattr(t.get('data_processamento'), 'isoformat') else str(t.get('data_processamento'))
            })
    
    transacoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
    
    return jsonify({'extrato': transacoes[:50]}), 200

def atualizar_carteira_ong(ong_id, valor, tipo):
    if ong_id not in carteiras_db:
        carteiras_db[ong_id] = {
            'ong_id': ong_id,
            'saldo': 0,
            'total_recebido': 0,
            'total_sacado': 0,
            'data_criacao': datetime.now(),
            'data_atualizacao': datetime.now()
        }
    
    carteira = carteiras_db[ong_id]
    if tipo == 'entrada':
        carteira['saldo'] += valor
        carteira['total_recebido'] += valor
    elif tipo == 'saida':
        carteira['saldo'] -= valor
        carteira['total_sacado'] += valor
    
    carteira['data_atualizacao'] = datetime.now()

# ==================== ROTAS DE DOAÇÕES FINANCEIRAS ====================

@app.route('/api/doacoes/financeiras/criar', methods=['POST'])
@token_required
@security_required
def criar_doacao_financeira():
    global next_doacao_financeira_id, next_transacao_id, next_pagamento_id
    
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Apenas doadores podem fazer doações financeiras'}), 403
    
    data = request.json
    ong_id = data.get('ong_id')
    valor = data.get('valor')
    mensagem = sanitizar_html(data.get('mensagem', ''))
    metodo_pagamento = data.get('metodo_pagamento', 'cartao')
    recorrente = data.get('recorrente', False)
    
    if not ong_id or not valor:
        return jsonify({'error': 'ONG e valor são obrigatórios'}), 400
    
    if valor < 1:
        return jsonify({'error': 'Valor mínimo é R$ 1,00'}), 400
    
    ong = ongs_db.get(ong_id)
    if not ong or ong.get('status') != 'ativo':
        return jsonify({'error': 'ONG não encontrada ou inativa'}), 404
    
    doador_id = request.user_payload.get('user_id')
    doador = doadores_db.get(doador_id)
    
    transacao_id = gerar_id_transacao()
    
    taxa_servico = valor * 0.0399 + 0.60
    valor_liquido = valor - taxa_servico
    
    doacao_financeira = {
        'id': next_doacao_financeira_id,
        'transacao_id': transacao_id,
        'doador_id': doador_id,
        'doador_nome': doador.get('nome', 'Doador'),
        'ong_id': ong_id,
        'ong_nome': ong.get('nome'),
        'valor': valor,
        'valor_liquido': valor_liquido,
        'taxa_servico': taxa_servico,
        'mensagem': mensagem,
        'metodo_pagamento': metodo_pagamento,
        'recorrente': recorrente,
        'status': 'pendente',
        'data_criacao': datetime.now(),
        'data_confirmacao': None
    }
    doacoes_financeiras_db[next_doacao_financeira_id] = doacao_financeira
    doacao_financeira_id = next_doacao_financeira_id
    next_doacao_financeira_id += 1
    
    # =====================================================================
    # REGISTRAR TAXA NA CARTEIRA DA PLATAFORMA
    # =====================================================================
    registrar_taxa_plataforma(
        valor_taxa=taxa_servico,
        transacao_id=transacao_id,
        descricao=f'Taxa de doação para {ong.get("nome")} - Doador: {doador.get("nome")}'
    )
    
    transacao = {
        'id': next_transacao_id,
        'transacao_id': transacao_id,
        'doador_id': doador_id,
        'ong_id': ong_id,
        'valor': valor,
        'tipo': 'doacao_financeira',
        'status': 'pendente',
        'metodo': metodo_pagamento,
        'data_criacao': datetime.now(),
        'data_processamento': None
    }
    transacoes_db[next_transacao_id] = transacao
    transacao_id_db = next_transacao_id
    next_transacao_id += 1
    
    resultado_pagamento = processar_pagamento_simulado(transacao_id, doacao_financeira_id)
    
    if resultado_pagamento['success']:
        doacao_financeira['status'] = 'confirmado'
        doacao_financeira['data_confirmacao'] = datetime.now()
        transacao['status'] = 'confirmado'
        transacao['data_processamento'] = datetime.now()
        
        atualizar_carteira_ong(ong_id, valor_liquido, 'entrada')
        
        registrar_log(
            f'Doação financeira de R$ {valor:.2f} para {ong.get("nome")}',
            usuario=doador.get('email'),
            gravidade='media'
        )
        
        enviar_email(
            ong.get('email'),
            f'💰 Nova doação financeira de R$ {valor:.2f}',
            f'Olá {ong.get("nome")},\n\nVocê recebeu uma doação financeira!\n\nValor: R$ {valor:.2f}\nTaxa: R$ {taxa_servico:.2f}\nValor líquido: R$ {valor_liquido:.2f}\nDoador: {doador.get("nome")}\nMensagem: {mensagem or "Sem mensagem"}'
        )
        
        return jsonify({
            'message': 'Doação financeira realizada com sucesso!',
            'transacao_id': transacao_id,
            'doacao_id': doacao_financeira_id,
            'status': 'confirmado'
        }), 201
    else:
        doacao_financeira['status'] = 'cancelado'
        transacao['status'] = 'cancelado'
        
        return jsonify({
            'error': 'Falha no processamento do pagamento',
            'transacao_id': transacao_id
        }), 400

def processar_pagamento_simulado(transacao_id, doacao_financeira_id):
    global next_pagamento_id
    sucesso = random.random() < 0.95
    
    pagamento = {
        'id': next_pagamento_id,
        'transacao_id': transacao_id,
        'doacao_financeira_id': doacao_financeira_id,
        'status': 'aprovado' if sucesso else 'recusado',
        'data_processamento': datetime.now(),
        'codigo_autorizacao': secrets.token_hex(8).upper() if sucesso else None
    }
    pagamentos_db[next_pagamento_id] = pagamento
    next_pagamento_id += 1
    
    return {'success': sucesso, 'pagamento_id': pagamento['id']}

@app.route('/api/doacoes/financeiras/minhas', methods=['GET'])
@token_required
def listar_minhas_doacoes_financeiras():
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Acesso restrito a doadores'}), 403
    
    doador_id = request.user_payload.get('user_id')
    
    doacoes = []
    for df in doacoes_financeiras_db.values():
        if df.get('doador_id') == doador_id:
            ong = ongs_db.get(df.get('ong_id'))
            doacoes.append({
                'id': df.get('id'),
                'transacao_id': df.get('transacao_id'),
                'ong_nome': ong.get('nome') if ong else 'Desconhecida',
                'valor': df.get('valor'),
                'mensagem': df.get('mensagem'),
                'metodo_pagamento': df.get('metodo_pagamento'),
                'recorrente': df.get('recorrente', False),
                'status': df.get('status'),
                'data_criacao': df.get('data_criacao').isoformat() if hasattr(df.get('data_criacao'), 'isoformat') else str(df.get('data_criacao')),
                'data_confirmacao': df.get('data_confirmacao').isoformat() if hasattr(df.get('data_confirmacao'), 'isoformat') else str(df.get('data_confirmacao'))
            })
    
    doacoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
    
    return jsonify({'doacoes': doacoes}), 200

@app.route('/api/doacoes/financeiras/estatisticas', methods=['GET'])
@token_required
def estatisticas_doacoes_financeiras():
    user_type = request.user_payload.get('tipo')
    user_id = request.user_payload.get('user_id')
    
    if user_type == 'ong':
        doacoes = [d for d in doacoes_financeiras_db.values() if d.get('ong_id') == user_id and d.get('status') == 'confirmado']
        total_doacoes = len(doacoes)
        total_valor = sum(d.get('valor_liquido', d.get('valor', 0)) for d in doacoes)
        media_valor = total_valor / total_doacoes if total_doacoes > 0 else 0
        
        return jsonify({
            'total_doacoes': total_doacoes,
            'total_valor': total_valor,
            'media_valor': round(media_valor, 2),
            'carteira': carteiras_db.get(user_id, {}).get('saldo', 0)
        }), 200
    
    elif user_type == 'doador':
        doacoes = [d for d in doacoes_financeiras_db.values() if d.get('doador_id') == user_id and d.get('status') == 'confirmado']
        total_doacoes = len(doacoes)
        total_valor = sum(d.get('valor', 0) for d in doacoes)
        recorrentes = [d for d in doacoes if d.get('recorrente', False)]
        
        return jsonify({
            'total_doacoes': total_doacoes,
            'total_valor': total_valor,
            'media_valor': round(total_valor / total_doacoes if total_doacoes > 0 else 0, 2),
            'doacoes_recorrentes': len(recorrentes)
        }), 200
    
    return jsonify({'error': 'Tipo de usuário inválido'}), 400

# ==================== ROTAS DE USUÁRIO ====================

@app.route('/api/usuario/dados', methods=['GET'])
@token_required
def obter_dados_usuario():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    if user_type == 'ong':
        ong = ongs_db.get(user_id)
        if not ong:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        return jsonify({'dados': ong}), 200
    elif user_type == 'doador':
        doador = doadores_db.get(user_id)
        if not doador:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        return jsonify({'dados': doador}), 200
    
    return jsonify({'error': 'Tipo de usuário inválido'}), 400

@app.route('/api/usuario/atualizar', methods=['PUT'])
@token_required
def atualizar_dados_usuario():
    data = request.json
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    if user_type == 'doador':
        doador = doadores_db.get(user_id)
        if not doador:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        doador['nome'] = data.get('nome', doador.get('nome'))
        doador['email'] = data.get('email', doador.get('email'))
        doador['telefone'] = data.get('telefone', doador.get('telefone'))
        doador['endereco'] = data.get('endereco', doador.get('endereco'))
        doador['cidade'] = data.get('cidade', doador.get('cidade'))
        doador['uf'] = data.get('uf', doador.get('uf'))
        doador['data_atualizacao'] = datetime.now()
        
        registrar_log('Dados do doador atualizados', usuario=doador.get('email'))
        return jsonify({'message': 'Dados atualizados com sucesso!'}), 200
    
    elif user_type == 'ong':
        ong = ongs_db.get(user_id)
        if not ong:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        ong['nome'] = data.get('nome', ong.get('nome'))
        ong['email'] = data.get('email', ong.get('email'))
        ong['telefone'] = data.get('telefone', ong.get('telefone'))
        ong['endereco'] = data.get('endereco', ong.get('endereco'))
        ong['cidade'] = data.get('cidade', ong.get('cidade'))
        ong['uf'] = data.get('uf', ong.get('uf'))
        ong['descricao'] = data.get('descricao', ong.get('descricao'))
        ong['data_atualizacao'] = datetime.now()
        
        registrar_log('Dados da ONG atualizados', usuario=ong.get('email'))
        return jsonify({'message': 'Dados atualizados com sucesso!'}), 200
    
    return jsonify({'error': 'Tipo de usuário inválido'}), 400

@app.route('/api/usuario/alterar-senha', methods=['PUT'])
@token_required
def alterar_senha_usuario():
    data = request.json
    senha_atual = data.get('senha_atual')
    nova_senha = data.get('nova_senha')
    
    if not senha_atual or not nova_senha:
        return jsonify({'error': 'Senha atual e nova senha são obrigatórias'}), 400
    
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    if user_type == 'doador':
        doador = doadores_db.get(user_id)
        if not doador:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if not verificar_senha(senha_atual, doador.get('senha')):
            return jsonify({'error': 'Senha atual incorreta'}), 401
        
        senha_valida, msg = validar_senha_forte(nova_senha)
        if not senha_valida:
            return jsonify({'error': f'Senha fraca: {msg}'}), 400
        
        doador['senha'] = hash_senha(nova_senha)
        doador['data_atualizacao'] = datetime.now()
        
        registrar_log('Senha alterada pelo doador', usuario=doador.get('email'), gravidade='media')
        return jsonify({'message': 'Senha alterada com sucesso!'}), 200
    
    elif user_type == 'ong':
        ong = ongs_db.get(user_id)
        if not ong:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        if not verificar_senha(senha_atual, ong.get('senha')):
            return jsonify({'error': 'Senha atual incorreta'}), 401
        
        senha_valida, msg = validar_senha_forte(nova_senha)
        if not senha_valida:
            return jsonify({'error': f'Senha fraca: {msg}'}), 400
        
        ong['senha'] = hash_senha(nova_senha)
        ong['data_atualizacao'] = datetime.now()
        
        registrar_log('Senha alterada pela ONG', usuario=ong.get('email'), gravidade='media')
        return jsonify({'message': 'Senha alterada com sucesso!'}), 200
    
    return jsonify({'error': 'Tipo de usuário inválido'}), 400

@app.route('/api/usuario/consentimento', methods=['PUT'])
@token_required
def atualizar_consentimento():
    data = request.json
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    consentimento = data.get('consentimento', False)
    
    if user_type == 'ong':
        ong = ongs_db.get(user_id)
        if ong:
            ong['consentimento_lgpd'] = consentimento
            ong['data_consentimento'] = datetime.now() if consentimento else None
    elif user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            doador['consentimento_lgpd'] = consentimento
            doador['data_consentimento'] = datetime.now() if consentimento else None
    
    registrar_log(f'Consentimento LGPD atualizado para {user_type}: {consentimento}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Consentimento atualizado com sucesso!'}), 200

@app.route('/api/usuario/excluir', methods=['DELETE'])
@token_required
def excluir_conta():
    global next_solicitacao_id
    
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    email = request.user_payload.get('email')
    
    nome = 'Usuário'
    if user_type == 'ong':
        ong = ongs_db.get(user_id)
        if ong:
            nome = ong.get('nome', 'ONG')
    elif user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            nome = doador.get('nome', 'Doador')
    
    solicitacao = {
        'id': next_solicitacao_id,
        'usuario_id': user_id,
        'usuario_nome': nome,
        'usuario_email': email,
        'usuario_tipo': user_type,
        'data_solicitacao': datetime.now(),
        'status': 'pendente'
    }
    solicitacoes_exclusao_db[next_solicitacao_id] = solicitacao
    next_solicitacao_id += 1
    
    registrar_log(
        f'Solicitação de exclusão de conta: {email} ({user_type})',
        usuario=email,
        gravidade='alta'
    )
    
    notificar_admin_nova_exclusao(email, nome, user_type)
    
    enviar_email(
        email,
        'Solicitação de exclusão de conta - Doa+',
        f'Olá {nome},\n\nRecebemos sua solicitação de exclusão de conta.\n\nSua conta será excluída em até 30 dias, conforme a LGPD.\n\nCaso tenha sido um engano, entre em contato conosco.\n\nEquipe Doa+'
    )
    
    return jsonify({
        'message': 'Solicitação de exclusão recebida. Você receberá um email com as instruções.',
        'prazo': '30 dias para exclusão definitiva',
        'solicitacao_id': solicitacao['id']
    }), 200

def notificar_admin_nova_exclusao(email, nome, tipo):
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@doamais.org')
    enviar_email(
        admin_email,
        f'🔴 Nova solicitação de exclusão de conta - {nome}',
        f'''
        Olá Admin,
        
        Um usuário solicitou a exclusão da conta:
        
        Nome: {nome}
        Email: {email}
        Tipo: {tipo}
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        Acesse o painel administrativo para gerenciar esta solicitação.
        
        Atenciosamente,
        Sistema Doa+
        '''
    )

# ==================== ROTAS DE 2FA ====================

@app.route('/api/usuario/2fa/status', methods=['GET'])
@token_required
def status_2fa():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    if user_type == 'doador':
        doador = doadores_db.get(user_id)
        return jsonify({'ativo': doador.get('2fa_ativado', False)}), 200
    
    return jsonify({'ativo': False}), 200

@app.route('/api/usuario/2fa/ativar', methods=['POST'])
@token_required
def ativar_2fa():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    email = request.user_payload.get('email')
    
    secret = gerar_2fa_secret()
    qr_code = gerar_qr_code(email, secret)
    
    session['2fa_secret'] = secret
    session['2fa_user'] = user_id
    
    return jsonify({
        'secret': secret,
        'qr_code': qr_code
    }), 200

@app.route('/api/usuario/2fa/confirmar', methods=['POST'])
@token_required
def confirmar_2fa():
    data = request.json
    codigo = data.get('codigo')
    secret = data.get('secret')
    
    if not codigo or not secret:
        return jsonify({'error': 'Código e secret são obrigatórios'}), 400
    
    if not verificar_2fa(secret, codigo):
        return jsonify({'error': 'Código inválido'}), 400
    
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    if user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            doador['2fa_secret'] = secret
            doador['2fa_ativado'] = True
            doador['data_atualizacao'] = datetime.now()
            
            registrar_log('2FA ativado para doador', usuario=doador.get('email'), gravidade='media')
            return jsonify({'message': '2FA ativado com sucesso!'}), 200
    
    return jsonify({'error': 'Usuário não encontrado'}), 404

@app.route('/api/usuario/2fa/desativar', methods=['DELETE'])
@token_required
def desativar_2fa():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    if user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            doador['2fa_secret'] = None
            doador['2fa_ativado'] = False
            doador['data_atualizacao'] = datetime.now()
            
            registrar_log('2FA desativado para doador', usuario=doador.get('email'), gravidade='media')
            return jsonify({'message': '2FA desativado com sucesso!'}), 200
    
    return jsonify({'error': 'Usuário não encontrado'}), 404

@app.route('/api/usuario/exportar-dados', methods=['POST'])
@token_required
def exportar_dados_usuario():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    email = request.user_payload.get('email')
    
    dados = {}
    
    if user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            dados['dados_pessoais'] = {
                'nome': doador.get('nome'),
                'email': doador.get('email'),
                'telefone': doador.get('telefone'),
                'cpf': doador.get('cpf'),
                'endereco': doador.get('endereco'),
                'cidade': doador.get('cidade'),
                'uf': doador.get('uf'),
                'data_cadastro': doador.get('data_cadastro').isoformat() if hasattr(doador.get('data_cadastro'), 'isoformat') else str(doador.get('data_cadastro'))
            }
            
            doacoes = [d for d in doacoes_db.values() if d.get('doador_id') == user_id]
            dados['historico_doacoes'] = [{
                'data': d.get('data').isoformat() if hasattr(d.get('data'), 'isoformat') else str(d.get('data')),
                'item': d.get('item'),
                'quantidade': d.get('quantidade'),
                'status': d.get('status')
            } for d in doacoes]
            
            doacoes_fin = [d for d in doacoes_financeiras_db.values() if d.get('doador_id') == user_id]
            dados['doacoes_financeiras'] = [{
                'data': d.get('data_criacao').isoformat() if hasattr(d.get('data_criacao'), 'isoformat') else str(d.get('data_criacao')),
                'valor': d.get('valor'),
                'ong_nome': d.get('ong_nome'),
                'status': d.get('status')
            } for d in doacoes_fin]
    
    registrar_log('Exportação de dados solicitada', usuario=email, gravidade='media')
    
    return jsonify({'dados': dados}), 200

# ==================== ROTAS DE CONQUISTAS ====================

@app.route('/api/doador/conquistas', methods=['GET'])
@token_required
def listar_conquistas_doador():
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Acesso restrito a doadores'}), 403
    
    doador_id = request.user_payload.get('user_id')
    doador = doadores_db.get(doador_id)
    
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

# ==================== ROTAS DE NOTIFICAÇÕES ====================

@app.route('/api/notificacoes/preferencias', methods=['GET'])
@token_required
def get_preferencias_notificacoes():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    email = request.user_payload.get('email')
    
    key = f"{user_type}_{user_id}"
    
    if key not in notificacoes_preferencias_db:
        notificacoes_preferencias_db[key] = {
            'email_doacoes': True,
            'email_novas_necessidades': True,
            'email_eventos': True,
            'email_newsletter': False,
            'push_doacoes': True,
            'push_novas_necessidades': True,
            'push_eventos': True,
            'push_mensagens': True
        }
    
    return jsonify(notificacoes_preferencias_db[key]), 200

@app.route('/api/notificacoes/preferencias', methods=['PUT'])
@token_required
def atualizar_preferencias_notificacoes():
    data = request.json
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    email = request.user_payload.get('email')
    
    key = f"{user_type}_{user_id}"
    
    preferencias = {
        'email_doacoes': data.get('email_doacoes', True),
        'email_novas_necessidades': data.get('email_novas_necessidades', True),
        'email_eventos': data.get('email_eventos', True),
        'email_newsletter': data.get('email_newsletter', False),
        'push_doacoes': data.get('push_doacoes', True),
        'push_novas_necessidades': data.get('push_novas_necessidades', True),
        'push_eventos': data.get('push_eventos', True),
        'push_mensagens': data.get('push_mensagens', True)
    }
    
    notificacoes_preferencias_db[key] = preferencias
    
    registrar_log(f'Preferências de notificação atualizadas para {user_type}', usuario=email, gravidade='baixa')
    
    return jsonify({
        'message': 'Preferências atualizadas com sucesso!',
        'preferencias': preferencias
    }), 200

# ==================== ROTAS DE VOLUNTARIADO ====================

@app.route('/api/voluntariado/vagas', methods=['GET'])
def listar_vagas_voluntariado():
    vagas = []
    for v in voluntariado_db.values():
        if v.get('status') != 'aberta':
            continue
        
        ong = ongs_db.get(v.get('ong_id'))
        if not ong or ong.get('status') != 'ativo':
            continue
        
        vagas.append({
            'id': v.get('id'),
            'ong_id': v.get('ong_id'),
            'ong_nome': v.get('ong_nome'),
            'titulo': v.get('titulo'),
            'descricao': v.get('descricao'),
            'data_evento': v.get('data_evento').isoformat() if hasattr(v.get('data_evento'), 'isoformat') else str(v.get('data_evento')),
            'local': v.get('local'),
            'vagas_disponiveis': v.get('vagas_disponiveis'),
            'vagas_preenchidas': v.get('vagas_preenchidas', 0),
            'habilidades': v.get('habilidades'),
            'status': v.get('status')
        })
    
    return jsonify({'vagas': vagas}), 200

@app.route('/api/voluntariado/vagas/<int:vaga_id>/inscrever', methods=['POST'])
@token_required
def inscrever_voluntariado(vaga_id):
    global next_inscricao_id
    
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Apenas doadores podem se inscrever'}), 403
    
    vaga = voluntariado_db.get(vaga_id)
    if not vaga or vaga.get('status') != 'aberta':
        return jsonify({'error': 'Vaga não encontrada ou encerrada'}), 404
    
    if vaga.get('vagas_preenchidas', 0) >= vaga.get('vagas_disponiveis', 0):
        return jsonify({'error': 'Vagas esgotadas'}), 400
    
    doador_id = request.user_payload.get('user_id')
    
    for insc in inscricoes_voluntariado_db.values():
        if insc.get('vaga_id') == vaga_id and insc.get('doador_id') == doador_id:
            return jsonify({'error': 'Você já está inscrito nesta vaga'}), 409
    
    inscricao = {
        'id': next_inscricao_id,
        'vaga_id': vaga_id,
        'doador_id': doador_id,
        'doador_nome': doadores_db.get(doador_id, {}).get('nome', 'Doador'),
        'data_inscricao': datetime.now(),
        'status': 'confirmada'
    }
    inscricoes_voluntariado_db[next_inscricao_id] = inscricao
    next_inscricao_id += 1
    
    vaga['vagas_preenchidas'] = vaga.get('vagas_preenchidas', 0) + 1
    
    if vaga['vagas_preenchidas'] >= vaga['vagas_disponiveis']:
        vaga['status'] = 'completa'
    
    registrar_log(f'Nova inscrição para voluntariado: {vaga.get("titulo")}', usuario=request.user_payload.get('email'))
    
    return jsonify({'message': 'Inscrição realizada com sucesso!'}), 201

# ==================== ROTAS DE AVALIAÇÕES ====================

@app.route('/api/avaliacoes', methods=['POST'])
@token_required
def avaliar_ong():
    global next_avaliacao_id
    
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Apenas doadores podem avaliar ONGs'}), 403
    
    data = request.json
    ong_id = data.get('ong_id')
    nota = data.get('nota')
    comentario = sanitizar_html(data.get('comentario', ''))
    
    if not ong_id or not nota:
        return jsonify({'error': 'ONG e nota são obrigatórios'}), 400
    
    if nota < 1 or nota > 5:
        return jsonify({'error': 'Nota deve ser entre 1 e 5'}), 400
    
    ong = ongs_db.get(ong_id)
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    doador_id = request.user_payload.get('user_id')
    
    for av in avaliacoes_db.values():
        if av.get('ong_id') == ong_id and av.get('doador_id') == doador_id:
            return jsonify({'error': 'Você já avaliou esta ONG'}), 409
    
    avaliacao = {
        'id': next_avaliacao_id,
        'ong_id': ong_id,
        'doador_id': doador_id,
        'doador_nome': doadores_db.get(doador_id, {}).get('nome', 'Anônimo'),
        'nota': nota,
        'comentario': comentario,
        'data': datetime.now()
    }
    avaliacoes_db[next_avaliacao_id] = avaliacao
    next_avaliacao_id += 1
    
    avaliacoes_ong = [a for a in avaliacoes_db.values() if a.get('ong_id') == ong_id]
    total_avaliacoes = len(avaliacoes_ong)
    soma_notas = sum(a.get('nota', 0) for a in avaliacoes_ong)
    ong['media_avaliacao'] = round(soma_notas / total_avaliacoes, 1) if total_avaliacoes > 0 else 0
    ong['total_avaliacoes'] = total_avaliacoes
    
    registrar_log(f'Nova avaliação para ONG #{ong_id}: {nota} estrelas', usuario=request.user_payload.get('email'))
    
    return jsonify({
        'message': 'Avaliação registrada com sucesso!',
        'media_avaliacao': ong['media_avaliacao'],
        'total_avaliacoes': total_avaliacoes
    }), 201

# ==================== ROTAS DE RANKING ====================

@app.route('/api/ranking/doadores', methods=['GET'])
def ranking_doadores():
    limit = int(request.args.get('limit', 10))
    
    doadores_ativos = [d for d in doadores_db.values() if d.get('status') == 'ativo']
    doadores_ordenados = sorted(doadores_ativos, key=lambda x: x.get('pontuacao', 0), reverse=True)
    
    ranking = []
    for i, doador in enumerate(doadores_ordenados[:limit], 1):
        ranking.append({
            'posicao': i,
            'id': doador.get('id'),
            'nome': doador.get('nome'),
            'total_doacoes': doador.get('total_doacoes', 0),
            'pontuacao': doador.get('pontuacao', 0),
            'conquistas': doador.get('conquistas', [])
        })
    
    return jsonify({'ranking': ranking}), 200

# ==================== ROTAS DE EVENTOS (PÚBLICOS) ====================

@app.route('/api/eventos', methods=['GET'])
def listar_eventos_publicos():
    eventos = []
    for ev in ong_eventos_db.values():
        if ev.get('status') == 'ativo':
            ong = ongs_db.get(ev.get('ong_id'))
            eventos.append({
                'id': ev.get('id'),
                'ong_id': ev.get('ong_id'),
                'ong_nome': ong.get('nome') if ong else 'ONG',
                'titulo': ev.get('titulo'),
                'descricao': ev.get('descricao'),
                'data_evento': ev.get('data_evento').isoformat() if hasattr(ev.get('data_evento'), 'isoformat') else str(ev.get('data_evento')),
                'local_evento': ev.get('local_evento'),
                'cidade': ev.get('cidade'),
                'uf': ev.get('uf'),
                'imagem_url': ev.get('imagem_url')
            })
    eventos.sort(key=lambda x: x.get('data_evento', ''))
    return jsonify({'eventos': eventos}), 200

# ==================== ROTAS DE FEEDBACK ====================

@app.route('/api/feedback', methods=['POST'])
@token_required
def enviar_feedback():
    global next_feedback_id
    
    data = request.json
    mensagem = sanitizar_html(data.get('mensagem', ''))
    tipo = data.get('tipo', 'geral')
    anonimo = data.get('anonimo', False)
    
    if not mensagem or len(mensagem.strip()) < 3:
        return jsonify({'error': 'Mensagem deve ter pelo menos 3 caracteres'}), 400
    
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    user_email = request.user_payload.get('email')
    
    nome = 'Anônimo'
    if user_type == 'ong':
        ong = ongs_db.get(user_id)
        if ong:
            nome = ong.get('nome', 'ONG')
    elif user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            nome = doador.get('nome', 'Doador')
    
    feedback = {
        'id': next_feedback_id,
        'user_id': user_id,
        'user_type': user_type,
        'user_email': user_email,
        'user_nome': nome if not anonimo else 'Anônimo',
        'mensagem': mensagem.strip(),
        'tipo': tipo,
        'anonimo': anonimo,
        'data': datetime.now(),
        'status': 'pendente',
        'resposta': None,
        'data_resposta': None
    }
    
    feedback_db[next_feedback_id] = feedback
    next_feedback_id += 1
    
    registrar_log(f'Novo feedback enviado por {user_type}', usuario=user_email)
    
    return jsonify({
        'message': 'Feedback enviado com sucesso!',
        'feedback_id': feedback['id']
    }), 201

@app.route('/api/feedback/meus', methods=['GET'])
@token_required
def listar_meus_feedbacks():
    user_id = request.user_payload.get('user_id')
    
    meus_feedbacks = []
    for fid, fb in feedback_db.items():
        if fb.get('user_id') == user_id:
            meus_feedbacks.append({
                'id': fid,
                'mensagem': fb.get('mensagem'),
                'tipo': fb.get('tipo'),
                'status': fb.get('status'),
                'data': fb.get('data').isoformat() if hasattr(fb.get('data'), 'isoformat') else str(fb.get('data')),
                'resposta': fb.get('resposta'),
                'data_resposta': fb.get('data_resposta').isoformat() if hasattr(fb.get('data_resposta'), 'isoformat') else str(fb.get('data_resposta'))
            })
    
    return jsonify({'feedbacks': meus_feedbacks}), 200

# ==================== ROTAS DE SUPORTE ====================

@app.route('/api/suporte', methods=['POST'])
@token_required
def enviar_suporte():
    global next_suporte_id
    
    data = request.json
    assunto = sanitizar_string(data.get('assunto', ''))
    mensagem = sanitizar_html(data.get('mensagem', ''))
    categoria = data.get('categoria', 'duvida')
    
    if not assunto or len(assunto.strip()) < 3:
        return jsonify({'error': 'Assunto deve ter pelo menos 3 caracteres'}), 400
    
    if not mensagem or len(mensagem.strip()) < 5:
        return jsonify({'error': 'Mensagem deve ter pelo menos 5 caracteres'}), 400
    
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    user_email = request.user_payload.get('email')
    
    nome = 'Usuário'
    if user_type == 'ong':
        ong = ongs_db.get(user_id)
        if ong:
            nome = ong.get('nome', 'ONG')
    elif user_type == 'doador':
        doador = doadores_db.get(user_id)
        if doador:
            nome = doador.get('nome', 'Doador')
    
    suporte = {
        'id': next_suporte_id,
        'user_id': user_id,
        'user_type': user_type,
        'user_email': user_email,
        'user_nome': nome,
        'assunto': assunto.strip(),
        'mensagem': mensagem.strip(),
        'categoria': categoria,
        'data': datetime.now(),
        'status': 'aberto',
        'resposta': None,
        'data_resposta': None,
        'responsavel': None
    }
    
    suporte_db[next_suporte_id] = suporte
    next_suporte_id += 1
    
    registrar_log(f'Nova solicitação de suporte de {user_type}', usuario=user_email, gravidade='media')
    
    return jsonify({
        'message': 'Solicitação de suporte enviada com sucesso!',
        'suporte_id': suporte['id']
    }), 201

@app.route('/api/suporte/meus', methods=['GET'])
@token_required
def listar_meus_suportes():
    user_id = request.user_payload.get('user_id')
    
    meus_suportes = []
    for sid, sp in suporte_db.items():
        if sp.get('user_id') == user_id:
            meus_suportes.append({
                'id': sid,
                'assunto': sp.get('assunto'),
                'mensagem': sp.get('mensagem'),
                'categoria': sp.get('categoria'),
                'status': sp.get('status'),
                'data': sp.get('data').isoformat() if hasattr(sp.get('data'), 'isoformat') else str(sp.get('data')),
                'resposta': sp.get('resposta'),
                'data_resposta': sp.get('data_resposta').isoformat() if hasattr(sp.get('data_resposta'), 'isoformat') else str(sp.get('data_resposta'))
            })
    
    return jsonify({'suportes': meus_suportes}), 200

# ==================== ROTAS DE AJUDA ====================

@app.route('/api/ajuda', methods=['GET'])
def obter_ajuda():
    artigos = [
        {
            'id': 1,
            'titulo': 'Como funciona a plataforma Doa+?',
            'categoria': 'geral',
            'conteudo': 'A Doa+ é uma plataforma que conecta doadores a ONGs. Você pode se cadastrar como doador ou ONG e começar a ajudar ou receber doações.'
        },
        {
            'id': 2,
            'titulo': 'Como faço para doar?',
            'categoria': 'doador',
            'conteudo': '1. Faça login como doador\n2. Navegue pelas necessidades das ONGs\n3. Clique em "Quero Doar"\n4. Informe a quantidade e confirme'
        },
        {
            'id': 3,
            'titulo': 'Como minha ONG pode receber doações?',
            'categoria': 'ong',
            'conteudo': '1. Cadastre sua ONG\n2. Crie uma necessidade (anúncio)\n3. Aguarde os doadores contribuírem\n4. Confirme as doações recebidas'
        },
        {
            'id': 4,
            'titulo': 'Como funcionam as doações financeiras?',
            'categoria': 'financeiro',
            'conteudo': 'As doações financeiras permitem que você doe dinheiro diretamente para as ONGs. O valor é processado de forma segura e a ONG recebe o valor na carteira digital da plataforma.'
        },
        {
            'id': 5,
            'titulo': 'Como sacar o dinheiro das doações?',
            'categoria': 'ong',
            'conteudo': '1. Acesse o dashboard da ONG\n2. Vá em "Carteira"\n3. Clique em "Sacar"\n4. Informe o valor e a conta bancária\n5. O dinheiro será transferido em até 3 dias úteis'
        },
        {
            'id': 6,
            'titulo': 'O que fazer se tiver um problema?',
            'categoria': 'suporte',
            'conteudo': 'Utilize a opção "Suporte" no menu para reportar problemas. Nossa equipe responderá o mais rápido possível.'
        }
    ]
    
    categoria = request.args.get('categoria')
    if categoria:
        artigos = [a for a in artigos if a['categoria'] == categoria]
    
    return jsonify({'artigos': artigos}), 200

# ==================== ROTAS DE COMUNICAÇÕES ====================

@app.route('/api/comunicacoes', methods=['GET'])
@token_required
def usuario_listar_comunicacoes():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    comunicacoes_usuario = []
    for c in comunicacoes_db:
        if c.get('tipo') == 'todos':
            comunicacoes_usuario.append(c)
        elif c.get('tipo') == user_type + 's':
            comunicacoes_usuario.append(c)
        elif c.get('tipo') == 'especifico' and c.get('destinatario_id') == user_id and c.get('destinatario_tipo') == user_type:
            comunicacoes_usuario.append(c)
    
    comunicacoes_usuario.sort(key=lambda x: x.get('data_envio'), reverse=True)
    
    resultado = []
    for c in comunicacoes_usuario:
        if not c.get('lida', False):
            c['lida'] = True
            c['data_leitura'] = datetime.now()
        
        resultado.append({
            'id': c['id'],
            'titulo': c.get('titulo'),
            'mensagem': c.get('mensagem'),
            'prioridade': c.get('prioridade', 'normal'),
            'data_envio': c.get('data_envio').isoformat() if hasattr(c.get('data_envio'), 'isoformat') else str(c.get('data_envio')),
            'lida': c.get('lida', True)
        })
    
    return jsonify({'comunicacoes': resultado}), 200

@app.route('/api/comunicacoes/nao-lidas', methods=['GET'])
@token_required
def usuario_comunicacoes_nao_lidas():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    
    nao_lidas = 0
    for c in comunicacoes_db:
        if c.get('lida', False):
            continue
        
        if c.get('tipo') == 'todos':
            nao_lidas += 1
        elif c.get('tipo') == user_type + 's':
            nao_lidas += 1
        elif c.get('tipo') == 'especifico' and c.get('destinatario_id') == user_id and c.get('destinatario_tipo') == user_type:
            nao_lidas += 1
    
    return jsonify({'nao_lidas': nao_lidas}), 200

# ==================== ROTAS DE CHAT ====================

@app.route('/api/chat/mensagens', methods=['POST'])
@token_required
def enviar_mensagem_chat():
    global next_mensagem_id
    
    data = request.json
    destinatario_id = data.get('destinatario_id')
    destinatario_tipo = data.get('destinatario_tipo')
    mensagem = sanitizar_html(data.get('mensagem', ''))
    
    if not destinatario_id or not mensagem:
        return jsonify({'error': 'Destinatário e mensagem são obrigatórios'}), 400
    
    remetente_id = request.user_payload.get('user_id')
    remetente_tipo = request.user_payload.get('tipo')
    
    if destinatario_tipo == 'ong':
        destinatario = ongs_db.get(destinatario_id)
    else:
        destinatario = doadores_db.get(destinatario_id)
    
    if not destinatario:
        return jsonify({'error': 'Destinatário não encontrado'}), 404
    
    msg = {
        'id': next_mensagem_id,
        'remetente_id': remetente_id,
        'remetente_tipo': remetente_tipo,
        'destinatario_id': destinatario_id,
        'destinatario_tipo': destinatario_tipo,
        'mensagem': mensagem,
        'data': datetime.now(),
        'lida': False
    }
    chat_mensagens_db.append(msg)
    next_mensagem_id += 1
    
    return jsonify({
        'message': 'Mensagem enviada!',
        'mensagem_id': msg['id']
    }), 201

@app.route('/api/chat/mensagens', methods=['GET'])
@token_required
def listar_mensagens_chat():
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    com = request.args.get('com')
    com_tipo = request.args.get('com_tipo')
    
    if not com or not com_tipo:
        return jsonify({'error': 'Parâmetros "com" e "com_tipo" são obrigatórios'}), 400
    
    com = int(com)
    
    mensagens = []
    for msg in chat_mensagens_db:
        if (msg.get('remetente_id') == user_id and msg.get('destinatario_id') == com and msg.get('destinatario_tipo') == com_tipo) or \
           (msg.get('destinatario_id') == user_id and msg.get('remetente_id') == com and msg.get('remetente_tipo') == com_tipo):
            mensagens.append({
                'id': msg.get('id'),
                'remetente_id': msg.get('remetente_id'),
                'remetente_tipo': msg.get('remetente_tipo'),
                'destinatario_id': msg.get('destinatario_id'),
                'destinatario_tipo': msg.get('destinatario_tipo'),
                'mensagem': msg.get('mensagem'),
                'data': msg.get('data').isoformat() if hasattr(msg.get('data'), 'isoformat') else str(msg.get('data')),
                'lida': msg.get('lida', False),
                'is_remetente': msg.get('remetente_id') == user_id
            })
    
    mensagens.sort(key=lambda x: x.get('data'))
    
    for msg in chat_mensagens_db:
        if msg.get('destinatario_id') == user_id and msg.get('remetente_id') == com:
            msg['lida'] = True
    
    return jsonify({'mensagens': mensagens}), 200

@app.route('/api/chat/nao-lidas', methods=['GET'])
@token_required
def chat_nao_lidas():
    user_id = request.user_payload.get('user_id')
    
    nao_lidas = 0
    for msg in chat_mensagens_db:
        if msg.get('destinatario_id') == user_id and not msg.get('lida', False):
            nao_lidas += 1
    
    return jsonify({'nao_lidas': nao_lidas}), 200

# ==================== ROTAS DE ADMIN ====================

@app.route('/api/admin/dashboard', methods=['GET'])
@token_required
def admin_dashboard():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    total_ongs = len(ongs_db)
    total_doadores = len(doadores_db)
    total_anuncios = len(necessidades_db)
    total_advertencias = len(advertencias_db)
    total_doacoes = len(doacoes_db)
    total_doacoes_financeiras = len([d for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado'])
    total_valor_financeiro = sum(d.get('valor', 0) for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado')
    total_comunicacoes = len(comunicacoes_db)
    ongs_bloqueadas = len([o for o in ongs_db.values() if o.get('status') == 'bloqueado'])
    solicitacoes_exclusao = len([s for s in solicitacoes_exclusao_db.values() if s.get('status') == 'pendente'])
    
    logs_recentes = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:10]
    
    return jsonify({
        'total_ongs': total_ongs,
        'total_doadores': total_doadores,
        'total_anuncios': total_anuncios,
        'total_advertencias': total_advertencias,
        'total_doacoes': total_doacoes,
        'total_doacoes_financeiras': total_doacoes_financeiras,
        'total_valor_financeiro': total_valor_financeiro,
        'total_comunicacoes': total_comunicacoes,
        'ongs_bloqueadas': ongs_bloqueadas,
        'solicitacoes_exclusao_pendentes': solicitacoes_exclusao,
        'logs_recentes': [{
            'data': l.get('data').isoformat() if hasattr(l.get('data'), 'isoformat') else str(l.get('data')),
            'evento': l.get('evento'),
            'usuario': l.get('usuario'),
            'ip': l.get('ip')
        } for l in logs_recentes]
    }), 200

# =====================================================================
# ROTA ADMIN - CARTEIRA DA PLATAFORMA
# =====================================================================

@app.route('/api/admin/carteira', methods=['GET'])
@token_required
def admin_carteira_plataforma():
    """
    Retorna os dados da carteira da plataforma para o painel administrativo
    """
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    dados = obter_dados_carteira_plataforma()
    return jsonify(dados), 200

@app.route('/api/admin/carteira/sacar', methods=['POST'])
@token_required
@security_required
def admin_sacar_carteira_plataforma():
    """
    Realiza um saque da carteira da plataforma
    """
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    data = request.json
    valor = data.get('valor')
    conta_bancaria = sanitizar_string(data.get('conta_bancaria', ''))
    
    if not valor or not conta_bancaria:
        return jsonify({'error': 'Valor e conta bancária são obrigatórios'}), 400
    
    try:
        valor = float(valor)
    except ValueError:
        return jsonify({'error': 'Valor inválido'}), 400
    
    if valor < 10:
        return jsonify({'error': 'Valor mínimo para saque é R$ 10,00'}), 400
    
    if carteira_plataforma['saldo'] < valor:
        return jsonify({'error': f'Saldo insuficiente. Disponível: R$ {carteira_plataforma["saldo"]:.2f}'}), 400
    
    resultado = registrar_saque_plataforma(
        valor=valor,
        conta_bancaria=conta_bancaria,
        descricao=f'Saque administrativo - Admin: {request.user_payload.get("email")}'
    )
    
    if not resultado['success']:
        return jsonify({'error': resultado['error']}), 400
    
    registrar_log(
        f'Saque da carteira da plataforma: R$ {valor:.2f} para conta {conta_bancaria}',
        usuario=request.user_payload.get('email'),
        gravidade='alta'
    )
    
    return jsonify({
        'message': f'Saque de R$ {valor:.2f} realizado com sucesso!',
        'saldo_restante': resultado['saldo_restante'],
        'transacao_id': f"SAQ{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(4).upper()}"
    }), 200

@app.route('/api/admin/carteira/extrato', methods=['GET'])
@token_required
def admin_carteira_extrato_plataforma():
    """
    Retorna o extrato da carteira da plataforma
    """
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    limit = int(request.args.get('limit', 50))
    extrato = carteira_plataforma['extrato'][-limit:]
    extrato.reverse()  # Mais recentes primeiro
    
    return jsonify({
        'extrato': [{
            'id': e.get('id'),
            'transacao_id': e.get('transacao_id'),
            'tipo': e.get('tipo'),
            'valor': e.get('valor'),
            'descricao': e.get('descricao'),
            'data': e.get('data').isoformat() if hasattr(e.get('data'), 'isoformat') else str(e.get('data'))
        } for e in extrato],
        'total': len(extrato)
    }), 200

# ==================== ROTAS ADMIN - ANÚNCIOS ====================

@app.route('/api/admin/anuncios', methods=['GET'])
@token_required
def admin_anuncios():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    anuncios_lista = []
    for nec_id, nec in necessidades_db.items():
        ong = ongs_db.get(nec.get('ong_id'))
        if ong:
            anuncios_lista.append({
                'id': nec_id,
                'ong_id': nec.get('ong_id'),
                'ong_nome': ong.get('nome'),
                'titulo': nec.get('titulo'),
                'descricao': nec.get('descricao'),
                'categoria': nec.get('categoria'),
                'urgencia': nec.get('urgencia'),
                'status': nec.get('status'),
                'total_advertencias': len([a for a in advertencias_db.values() if a.get('anuncio_id') == nec_id]),
                'data_criacao': nec.get('data_criacao'),
                'excluido': nec.get('status') == 'excluido'
            })
    
    return jsonify({'anuncios': anuncios_lista}), 200

@app.route('/api/admin/anuncios/<int:anuncio_id>/excluir', methods=['DELETE'])
@token_required
def admin_excluir_anuncio(anuncio_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    anuncio = necessidades_db.get(anuncio_id)
    if not anuncio:
        return jsonify({'error': 'Anúncio não encontrado'}), 404
    
    anuncio['status'] = 'excluido'
    registrar_log(f'Anúncio #{anuncio_id} excluído pelo admin', gravidade='alta')
    
    return jsonify({'message': 'Anúncio excluído com sucesso!'}), 200

# ==================== ROTAS ADMIN - ONGs ====================

@app.route('/api/admin/ongs', methods=['GET'])
@token_required
def admin_ongs():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    ongs_lista = []
    for ong_id, ong in ongs_db.items():
        carteira = carteiras_db.get(ong_id, {})
        ongs_lista.append({
            'id': ong_id,
            'nome': ong.get('nome'),
            'cnpj': ong.get('cnpj'),
            'email': ong.get('email'),
            'telefone': ong.get('telefone'),
            'endereco': ong.get('endereco'),
            'cidade': ong.get('cidade'),
            'status': ong.get('status'),
            'total_advertencias': len([a for a in advertencias_db.values() if a.get('ong_id') == ong_id]),
            'data_cadastro': ong.get('data_cadastro'),
            'media_avaliacao': ong.get('media_avaliacao', 0),
            'total_avaliacoes': ong.get('total_avaliacoes', 0),
            'saldo_carteira': carteira.get('saldo', 0),
            'total_recebido': carteira.get('total_recebido', 0),
            'total_sacado': carteira.get('total_sacado', 0),
            'data_atualizacao': carteira.get('data_atualizacao')
        })
    
    return jsonify({'ongs': ongs_lista}), 200

@app.route('/api/admin/ongs/<int:ong_id>/bloquear', methods=['PUT'])
@token_required
def admin_bloquear_ong(ong_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    ong = ongs_db.get(ong_id)
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    ong['status'] = 'bloqueado'
    registrar_log(f'ONG #{ong_id} ({ong.get("nome")}) bloqueada por admin', gravidade='alta')
    
    return jsonify({'message': 'ONG bloqueada com sucesso!'}), 200

@app.route('/api/admin/ongs/<int:ong_id>/desbloquear', methods=['PUT'])
@token_required
def admin_desbloquear_ong(ong_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    ong = ongs_db.get(ong_id)
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    ong['status'] = 'ativo'
    registrar_log(f'ONG #{ong_id} ({ong.get("nome")}) desbloqueada por admin')
    
    return jsonify({'message': 'ONG desbloqueada com sucesso!'}), 200

# ==================== ROTAS ADMIN - DOADORES ====================

@app.route('/api/admin/doadores', methods=['GET'])
@token_required
def admin_doadores():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doadores_lista = []
    for doador_id, doador in doadores_db.items():
        doadores_lista.append({
            'id': doador_id,
            'nome': doador.get('nome'),
            'email': doador.get('email'),
            'telefone': doador.get('telefone'),
            'status': doador.get('status'),
            'total_doacoes': doador.get('total_doacoes', 0),
            'pontuacao': doador.get('pontuacao', 0),
            'conquistas': doador.get('conquistas', []),
            'data_cadastro': doador.get('data_cadastro')
        })
    
    return jsonify({'doadores': doadores_lista}), 200

@app.route('/api/admin/doadores/<int:doador_id>/bloquear', methods=['PUT'])
@token_required
def admin_bloquear_doador(doador_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doador = doadores_db.get(doador_id)
    if not doador:
        return jsonify({'error': 'Doador não encontrado'}), 404
    
    doador['status'] = 'bloqueado'
    registrar_log(f'Doador #{doador_id} ({doador.get("nome")}) bloqueado por admin', gravidade='media')
    
    return jsonify({'message': 'Doador bloqueado com sucesso!'}), 200

# ==================== ROTAS ADMIN - DOAÇÕES ====================

@app.route('/api/admin/doacoes', methods=['GET'])
@token_required
def admin_doacoes():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doacoes_lista = []
    for doc_id, doc in doacoes_db.items():
        ong = ongs_db.get(doc.get('ong_id'))
        doador = doadores_db.get(doc.get('doador_id'))
        
        doacoes_lista.append({
            'id': doc_id,
            'data': doc.get('data'),
            'doador_nome': doc.get('doador_nome'),
            'ong_nome': ong.get('nome') if ong else 'Desconhecida',
            'item': doc.get('item'),
            'quantidade': doc.get('quantidade'),
            'status': doc.get('status')
        })
    
    return jsonify({'doacoes': doacoes_lista}), 200

@app.route('/api/admin/doacoes/financeiras', methods=['GET'])
@token_required
def admin_doacoes_financeiras():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doacoes = []
    for df in doacoes_financeiras_db.values():
        doador = doadores_db.get(df.get('doador_id'))
        ong = ongs_db.get(df.get('ong_id'))
        doacoes.append({
            'id': df.get('id'),
            'transacao_id': df.get('transacao_id'),
            'doador_nome': doador.get('nome') if doador else 'Desconhecido',
            'ong_nome': ong.get('nome') if ong else 'Desconhecida',
            'valor': df.get('valor'),
            'taxa_servico': df.get('taxa_servico', 0),
            'valor_liquido': df.get('valor_liquido', df.get('valor', 0)),
            'mensagem': df.get('mensagem'),
            'metodo_pagamento': df.get('metodo_pagamento'),
            'recorrente': df.get('recorrente', False),
            'status': df.get('status'),
            'data_criacao': df.get('data_criacao').isoformat() if hasattr(df.get('data_criacao'), 'isoformat') else str(df.get('data_criacao')),
            'data_confirmacao': df.get('data_confirmacao').isoformat() if hasattr(df.get('data_confirmacao'), 'isoformat') else str(df.get('data_confirmacao'))
        })
    
    doacoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
    
    return jsonify({'doacoes': doacoes}), 200

# ==================== ROTAS ADMIN - ADVERTÊNCIAS ====================

@app.route('/api/admin/advertencias', methods=['POST'])
@token_required
def admin_adicionar_advertencia():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    global next_advertencia_id
    
    data = request.json
    anuncio_id = data.get('anuncio_id')
    ong_id = data.get('ong_id')
    motivo = data.get('motivo')
    descricao = data.get('descricao')
    acao = data.get('acao', 'apenas_advertir')
    
    if not anuncio_id or not ong_id or not motivo:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    advertencia = {
        'id': next_advertencia_id,
        'anuncio_id': anuncio_id,
        'ong_id': ong_id,
        'motivo': motivo,
        'descricao': descricao,
        'data': datetime.now(),
        'admin': request.user_payload.get('email')
    }
    advertencias_db[next_advertencia_id] = advertencia
    next_advertencia_id += 1
    
    ong = ongs_db.get(ong_id)
    if ong:
        total_advertencias = len([a for a in advertencias_db.values() if a.get('ong_id') == ong_id])
        ong['total_advertencias'] = total_advertencias
        
        if total_advertencias >= 3:
            ong['status'] = 'bloqueado'
            registrar_log(f'ONG #{ong_id} ({ong.get("nome")}) bloqueada por atingir 3 advertências', gravidade='alta')
    
    if acao == 'remover_anuncio':
        anuncio = necessidades_db.get(anuncio_id)
        if anuncio:
            anuncio['status'] = 'excluido'
    elif acao == 'bloquear_ong' and ong:
        ong['status'] = 'bloqueado'
    
    registrar_log(f'Advertência aplicada ao anúncio #{anuncio_id} - Motivo: {motivo}', gravidade='media')
    
    return jsonify({'message': 'Advertência aplicada com sucesso!'}), 200

# ==================== ROTAS ADMIN - SOLICITAÇÕES DE EXCLUSÃO ====================

@app.route('/api/admin/solicitacoes/exclusao', methods=['GET'])
@token_required
def admin_listar_solicitacoes_exclusao():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    solicitacoes = []
    for sid, sol in solicitacoes_exclusao_db.items():
        if sol.get('status') == 'pendente':
            solicitacoes.append({
                'id': sid,
                'usuario_id': sol.get('usuario_id'),
                'usuario_nome': sol.get('usuario_nome'),
                'usuario_email': sol.get('usuario_email'),
                'usuario_tipo': sol.get('usuario_tipo'),
                'data_solicitacao': sol.get('data_solicitacao').isoformat() if hasattr(sol.get('data_solicitacao'), 'isoformat') else str(sol.get('data_solicitacao')),
                'status': sol.get('status')
            })
    
    return jsonify({'solicitacoes': solicitacoes}), 200

@app.route('/api/admin/solicitacoes/exclusao/<int:solicitacao_id>/confirmar', methods=['DELETE'])
@token_required
def admin_confirmar_exclusao(solicitacao_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    solicitacao = solicitacoes_exclusao_db.get(solicitacao_id)
    if not solicitacao:
        return jsonify({'error': 'Solicitação não encontrada'}), 404
    
    user_id = solicitacao.get('usuario_id')
    user_type = solicitacao.get('usuario_tipo')
    
    if user_type == 'doador':
        if user_id in doadores_db:
            del doadores_db[user_id]
    elif user_type == 'ong':
        if user_id in ongs_db:
            del ongs_db[user_id]
    
    solicitacao['status'] = 'confirmado'
    solicitacao['data_confirmacao'] = datetime.now()
    solicitacao['admin'] = request.user_payload.get('email')
    
    registrar_log(
        f'Admin confirmou exclusão da conta {solicitacao.get("usuario_email")}',
        usuario=request.user_payload.get('email'),
        gravidade='alta'
    )
    
    return jsonify({'message': 'Conta excluída com sucesso!'}), 200

@app.route('/api/admin/solicitacoes/exclusao/<int:solicitacao_id>/cancelar', methods=['PUT'])
@token_required
def admin_cancelar_exclusao(solicitacao_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    solicitacao = solicitacoes_exclusao_db.get(solicitacao_id)
    if not solicitacao:
        return jsonify({'error': 'Solicitação não encontrada'}), 404
    
    solicitacao['status'] = 'cancelado'
    solicitacao['data_cancelamento'] = datetime.now()
    solicitacao['admin'] = request.user_payload.get('email')
    
    registrar_log(
        f'Admin cancelou exclusão da conta {solicitacao.get("usuario_email")}',
        usuario=request.user_payload.get('email'),
        gravidade='media'
    )
    
    return jsonify({'message': 'Solicitação cancelada com sucesso!'}), 200

# ==================== ROTAS ADMIN - LOGS ====================

@app.route('/api/admin/logs', methods=['GET'])
@token_required
def admin_logs():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    limit = int(request.args.get('limit', 100))
    
    logs_ordenados = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:limit]
    
    return jsonify({
        'logs': [{
            'data': l.get('data').isoformat() if hasattr(l.get('data'), 'isoformat') else str(l.get('data')),
            'evento': l.get('evento'),
            'usuario': l.get('usuario'),
            'ip': l.get('ip'),
            'gravidade': l.get('gravidade', 'baixa')
        } for l in logs_ordenados]
    }), 200

# ==================== MIDDLEWARE DE SEGURANÇA ====================

@app.after_request
def add_security_headers_to_response(response):
    return add_security_headers(response)

# =====================================================================
# ROTAS DE DOAÇÃO COM MERCADO PAGO
# =====================================================================

@app.route('/api/doacoes/mercadopago/criar', methods=['POST'])
@token_required
@security_required
def criar_doacao_mercadopago():
    """
    Cria uma doação usando Mercado Pago
    Body: {
        "ong_id": 1,
        "valor": 50.00,
        "mensagem": "Mensagem opcional",
        "recorrente": false
    }
    """
    if not MERCADO_PAGO_ATIVO:
        return jsonify({'error': 'Mercado Pago não configurado. Configure MP_ACCESS_TOKEN no .env'}), 503
    
    try:
        if request.user_payload.get('tipo') != 'doador':
            return jsonify({'error': 'Apenas doadores podem fazer doações'}), 403
        
        data = request.json
        ong_id = data.get('ong_id')
        valor = data.get('valor')
        mensagem = data.get('mensagem', '')
        recorrente = data.get('recorrente', False)
        
        if not ong_id or not valor:
            return jsonify({'error': 'ONG e valor são obrigatórios'}), 400
        
        if valor < 1:
            return jsonify({'error': 'Valor mínimo é R$ 1,00'}), 400
        
        # Buscar ONG
        ong = ongs_db.get(ong_id)
        if not ong or ong.get('status') != 'ativo':
            return jsonify({'error': 'ONG não encontrada ou inativa'}), 404
        
        # Buscar doador
        doador_id = request.user_payload.get('user_id')
        doador = doadores_db.get(doador_id)
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        # Criar preferência no Mercado Pago
        resultado_mp = criar_preferencia_doacao(
            doador_nome=doador.get('nome', 'Doador'),
            doador_email=doador.get('email', ''),
            doador_cpf=doador.get('cpf', ''),
            ong_id=ong_id,
            ong_nome=ong.get('nome'),
            valor=valor,
            mensagem=mensagem,
            recorrente=recorrente
        )
        
        if not resultado_mp.get('sucesso'):
            return jsonify({
                'error': f'Erro no Mercado Pago: {resultado_mp.get("error")}'
            }), 400
        
        # Salvar doação pendente
        global next_doacao_financeira_id, next_transacao_id
        
        transacao_id = resultado_mp.get('external_reference')
        taxa_servico = resultado_mp.get('taxa_servico', 0)
        valor_liquido = resultado_mp.get('valor_liquido', valor)
        
        doacao_financeira = {
            'id': next_doacao_financeira_id,
            'transacao_id': transacao_id,
            'doador_id': doador_id,
            'doador_nome': doador.get('nome', 'Doador'),
            'ong_id': ong_id,
            'ong_nome': ong.get('nome'),
            'valor': valor,
            'valor_liquido': valor_liquido,
            'taxa_servico': taxa_servico,
            'mensagem': mensagem,
            'metodo_pagamento': 'mercadopago',
            'recorrente': recorrente,
            'status': 'pendente',
            'data_criacao': datetime.now(),
            'data_confirmacao': None,
            'mp_preference_id': resultado_mp.get('id_preferencia'),
            'mp_status': 'pending'
        }
        doacoes_financeiras_db[next_doacao_financeira_id] = doacao_financeira
        doacao_financeira_id = next_doacao_financeira_id
        next_doacao_financeira_id += 1
        
        # Registrar taxa na carteira da plataforma (aguardando confirmação)
        # A taxa só será registrada de fato quando a doação for confirmada
        # Por enquanto, salvamos para uso posterior
        
        # Salvar transação
        transacao = {
            'id': next_transacao_id,
            'transacao_id': transacao_id,
            'doador_id': doador_id,
            'ong_id': ong_id,
            'valor': valor,
            'tipo': 'doacao_financeira',
            'status': 'pendente',
            'metodo': 'mercadopago',
            'data_criacao': datetime.now(),
            'data_processamento': None,
            'mp_preference_id': resultado_mp.get('id_preferencia'),
            'taxa_servico': taxa_servico,
            'valor_liquido': valor_liquido
        }
        transacoes_db[next_transacao_id] = transacao
        transacao_id_db = next_transacao_id
        next_transacao_id += 1
        
        registrar_log(
            f'Doação via Mercado Pago criada: R$ {valor:.2f} para {ong.get("nome")}',
            usuario=doador.get('email'),
            gravidade='media'
        )
        
        return jsonify({
            'success': True,
            'message': 'Doação iniciada!',
            'redirect_url': resultado_mp.get('url_doacao'),
            'doacao_id': doacao_financeira_id,
            'transacao_id': transacao_id,
            'external_reference': transacao_id,
            'valor': valor,
            'ong_nome': ong.get('nome')
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar doação com Mercado Pago: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/doacoes/mercadopago/status/<transacao_id>', methods=['GET'])
@token_required
def verificar_status_doacao_mp(transacao_id):
    """
    Verifica o status de uma doação no Mercado Pago
    """
    if not MERCADO_PAGO_ATIVO:
        return jsonify({'error': 'Mercado Pago não configurado'}), 503
    
    try:
        # Buscar doação no banco
        doacao = None
        for df in doacoes_financeiras_db.values():
            if df.get('transacao_id') == transacao_id:
                doacao = df
                break
        
        if not doacao:
            return jsonify({'error': 'Doação não encontrada'}), 404
        
        # Verificar se é doação via Mercado Pago
        if doacao.get('metodo_pagamento') != 'mercadopago':
            return jsonify({'error': 'Doação não foi feita via Mercado Pago'}), 400
        
        # Buscar status no Mercado Pago
        payment_id = doacao.get('mp_payment_id')
        if not payment_id:
            return jsonify({
                'status': doacao.get('status'),
                'mensagem': 'Aguardando confirmação do pagamento'
            }), 200
        
        resultado = obter_status_doacao(payment_id)
        
        if not resultado.get('success'):
            return jsonify({'error': resultado.get('error')}), 400
        
        # Atualizar status se necessário
        status_mp = resultado.get('status')
        if status_mp == 'approved' and doacao.get('status') != 'confirmado':
            doacao['status'] = 'confirmado'
            doacao['data_confirmacao'] = datetime.now()
            doacao['mp_status'] = status_mp
            
            # REGISTRAR TAXA NA CARTEIRA DA PLATAFORMA
            valor_taxa = doacao.get('taxa_servico', 0)
            if valor_taxa > 0:
                registrar_taxa_plataforma(
                    valor_taxa=valor_taxa,
                    transacao_id=transacao_id,
                    descricao=f'Taxa de doação via Mercado Pago para {doacao.get("ong_nome")} - Doador: {doacao.get("doador_nome")}'
                )
            
            # Atualizar transação
            for t in transacoes_db.values():
                if t.get('transacao_id') == transacao_id:
                    t['status'] = 'confirmado'
                    t['data_processamento'] = datetime.now()
            
            # Atualizar carteira da ONG
            ong_id = doacao.get('ong_id')
            valor_liquido = doacao.get('valor_liquido', doacao.get('valor', 0))
            if ong_id in carteiras_db:
                carteiras_db[ong_id]['saldo'] = carteiras_db[ong_id].get('saldo', 0) + valor_liquido
                carteiras_db[ong_id]['total_recebido'] = carteiras_db[ong_id].get('total_recebido', 0) + valor_liquido
            
            registrar_log(
                f'Doação via Mercado Pago confirmada: R$ {doacao.get("valor"):.2f} para {doacao.get("ong_nome")}',
                usuario=doacao.get('doador_email'),
                gravidade='alta'
            )
        
        return jsonify({
            'success': True,
            'status': doacao.get('status'),
            'mp_status': status_mp,
            'detalhes': resultado
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status da doação: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/doacao/success')
def doacao_success():
    """Callback de sucesso do Mercado Pago"""
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_reference = request.args.get('external_reference')
    preference_id = request.args.get('preference_id')
    
    print(f"✅ DOAÇÃO APROVADA - ref: {external_reference}, status: {status}")
    
    # Buscar informações da doação
    doacao_info = None
    for df in doacoes_financeiras_db.values():
        if df.get('transacao_id') == external_reference:
            doacao_info = df
            break
    
    # Atualizar status da doação
    if external_reference:
        for df_id, df in doacoes_financeiras_db.items():
            if df.get('transacao_id') == external_reference:
                df['status'] = 'confirmado'
                df['data_confirmacao'] = datetime.now()
                df['mp_status'] = status or 'approved'
                df['mp_payment_id'] = payment_id
                
                # REGISTRAR TAXA NA CARTEIRA DA PLATAFORMA
                valor_taxa = df.get('taxa_servico', 0)
                if valor_taxa > 0:
                    registrar_taxa_plataforma(
                        valor_taxa=valor_taxa,
                        transacao_id=external_reference,
                        descricao=f'Taxa de doação via Mercado Pago para {df.get("ong_nome")} - Doador: {df.get("doador_nome")}'
                    )
                
                # Atualizar transação
                for t in transacoes_db.values():
                    if t.get('transacao_id') == external_reference:
                        t['status'] = 'confirmado'
                        t['data_processamento'] = datetime.now()
                
                # Atualizar carteira da ONG
                ong_id = df.get('ong_id')
                valor_liquido = df.get('valor_liquido', df.get('valor', 0))
                if ong_id in carteiras_db:
                    carteiras_db[ong_id]['saldo'] = carteiras_db[ong_id].get('saldo', 0) + valor_liquido
                    carteiras_db[ong_id]['total_recebido'] = carteiras_db[ong_id].get('total_recebido', 0) + valor_liquido
                
                registrar_log(
                    f'Doação via Mercado Pago confirmada: R$ {df.get("valor"):.2f} para {df.get("ong_nome")}',
                    usuario=df.get('doador_email'),
                    gravidade='alta'
                )
                
                break
    
    params = {
        'doacao_id': external_reference,
        'status': status or 'approved',
        'ong_nome': doacao_info.get('ong_nome', 'ONG') if doacao_info else 'ONG',
        'valor': f"R$ {doacao_info.get('valor', 0):.2f}" if doacao_info else 'R$ 0,00'
    }
    params = {k: v for k, v in params.items() if v is not None}
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    return redirect(f'/doacao_aprovada.html?{query_string}')


@app.route('/doacao/failure')
def doacao_failure():
    """Callback de falha do Mercado Pago"""
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_reference = request.args.get('external_reference')
    preference_id = request.args.get('preference_id')
    
    print(f"❌ DOAÇÃO RECUSADA - ref: {external_reference}, status: {status}")
    
    # Buscar informações da doação
    doacao_info = None
    for df in doacoes_financeiras_db.values():
        if df.get('transacao_id') == external_reference:
            doacao_info = df
            break
    
    # Atualizar status da doação
    if external_reference:
        for df_id, df in doacoes_financeiras_db.items():
            if df.get('transacao_id') == external_reference:
                df['status'] = 'cancelado'
                df['mp_status'] = status or 'rejected'
                df['mp_payment_id'] = payment_id
                
                # Atualizar transação
                for t in transacoes_db.values():
                    if t.get('transacao_id') == external_reference:
                        t['status'] = 'cancelado'
                        t['data_processamento'] = datetime.now()
                
                registrar_log(
                    f'Doação via Mercado Pago recusada: R$ {df.get("valor"):.2f} para {df.get("ong_nome")}',
                    usuario=df.get('doador_email'),
                    gravidade='media'
                )
                break
    
    params = {
        'doacao_id': external_reference,
        'status': status or 'rejected',
        'ong_nome': doacao_info.get('ong_nome', 'ONG') if doacao_info else 'ONG',
        'valor': f"R$ {doacao_info.get('valor', 0):.2f}" if doacao_info else 'R$ 0,00'
    }
    params = {k: v for k, v in params.items() if v is not None}
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    return redirect(f'/doacao_recusada.html?{query_string}')


@app.route('/doacao/pending')
def doacao_pending():
    """Callback de pendência do Mercado Pago"""
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    external_reference = request.args.get('external_reference')
    preference_id = request.args.get('preference_id')
    
    print(f"⏳ DOAÇÃO PENDENTE - ref: {external_reference}, status: {status}")
    
    # Buscar informações da doação
    doacao_info = None
    for df in doacoes_financeiras_db.values():
        if df.get('transacao_id') == external_reference:
            doacao_info = df
            break
    
    # Atualizar status da doação
    if external_reference:
        for df_id, df in doacoes_financeiras_db.items():
            if df.get('transacao_id') == external_reference:
                df['mp_status'] = status or 'pending'
                df['mp_payment_id'] = payment_id
                break
    
    params = {
        'doacao_id': external_reference,
        'status': status or 'pending',
        'ong_nome': doacao_info.get('ong_nome', 'ONG') if doacao_info else 'ONG',
        'valor': f"R$ {doacao_info.get('valor', 0):.2f}" if doacao_info else 'R$ 0,00'
    }
    params = {k: v for k, v in params.items() if v is not None}
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    return redirect(f'/doacao_pendente.html?{query_string}')


@app.route('/webhook/mercadopago', methods=['POST', 'GET'])
def webhook_mercadopago():
    """
    Webhook para receber notificações do Mercado Pago
    """
    if not MERCADO_PAGO_ATIVO:
        return jsonify({"success": False, "error": "Mercado Pago não configurado"}), 503
    
    try:
        if request.method == 'GET':
            topic = request.args.get('topic')
            payment_id = request.args.get('id')
            print(f"📩 Webhook GET: topic={topic}, payment_id={payment_id}")
            return "OK", 200
        
        data = request.json
        print(f"📩 Webhook POST recebido: {data}")
        
        if data and data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            if payment_id:
                resultado = obter_status_doacao(payment_id)
                
                if resultado.get('success'):
                    status = resultado.get('status')
                    external_reference = resultado.get('external_reference')
                    
                    if external_reference:
                        # Atualizar status da doação
                        for df_id, df in doacoes_financeiras_db.items():
                            if df.get('transacao_id') == external_reference:
                                df['mp_status'] = status
                                df['mp_payment_id'] = payment_id
                                
                                if status == 'approved' and df.get('status') != 'confirmado':
                                    df['status'] = 'confirmado'
                                    df['data_confirmacao'] = datetime.now()
                                    
                                    # REGISTRAR TAXA NA CARTEIRA DA PLATAFORMA
                                    valor_taxa = df.get('taxa_servico', 0)
                                    if valor_taxa > 0:
                                        registrar_taxa_plataforma(
                                            valor_taxa=valor_taxa,
                                            transacao_id=external_reference,
                                            descricao=f'Webhook - Taxa de doação para {df.get("ong_nome")} - Doador: {df.get("doador_nome")}'
                                        )
                                    
                                    # Atualizar transação
                                    for t in transacoes_db.values():
                                        if t.get('transacao_id') == external_reference:
                                            t['status'] = 'confirmado'
                                            t['data_processamento'] = datetime.now()
                                    
                                    # Atualizar carteira da ONG
                                    ong_id = df.get('ong_id')
                                    valor_liquido = df.get('valor_liquido', df.get('valor', 0))
                                    if ong_id in carteiras_db:
                                        carteiras_db[ong_id]['saldo'] = carteiras_db[ong_id].get('saldo', 0) + valor_liquido
                                        carteiras_db[ong_id]['total_recebido'] = carteiras_db[ong_id].get('total_recebido', 0) + valor_liquido
                                    
                                    registrar_log(
                                        f'Webhook: Doação confirmada: R$ {df.get("valor"):.2f} para {df.get("ong_nome")}',
                                        usuario=df.get('doador_email'),
                                        gravidade='alta'
                                    )
                                    
                                    print(f"✅ Webhook: Doação {external_reference} CONFIRMADA")
                                
                                elif status == 'rejected':
                                    df['status'] = 'cancelado'
                                    print(f"❌ Webhook: Doação {external_reference} RECUSADA")
                                
                                elif status == 'pending':
                                    print(f"⏳ Webhook: Doação {external_reference} PENDENTE")
                                
                                break
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/mercadopago/test', methods=['GET'])
def test_mercadopago():
    """Endpoint para testar a conexão com o Mercado Pago"""
    if not MERCADO_PAGO_ATIVO:
        return jsonify({'error': 'Mercado Pago não configurado. Configure MP_ACCESS_TOKEN no .env'}), 503
    
    try:
        resultado = testar_conexao_direta()
        return jsonify({
            'success': True,
            'resultado': resultado
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== RELATÓRIOS ANUAIS ====================

@app.route('/api/relatorios/anual/gerar', methods=['POST'])
@token_required
def gerar_relatorio_anual():
    global next_relatorio_anual_id
    
    if not PDF_SUPPORT:
        return jsonify({'error': 'Relatório PDF não disponível. Instale reportlab.'}), 503
    
    user_id = request.user_payload.get('user_id')
    user_type = request.user_payload.get('tipo')
    email = request.user_payload.get('email')
    ano = request.json.get('ano', datetime.now().year)
    
    if user_type != 'doador':
        return jsonify({'error': 'Apenas doadores podem gerar relatório anual'}), 403
    
    doador = doadores_db.get(user_id)
    if not doador:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    relatorio = {
        'id': next_relatorio_anual_id,
        'usuario_id': user_id,
        'usuario_type': user_type,
        'usuario_email': email,
        'ano': ano,
        'data_geracao': datetime.now(),
        'status': 'gerado'
    }
    relatorios_anuais_db[next_relatorio_anual_id] = relatorio
    next_relatorio_anual_id += 1
    
    return jsonify({
        'message': 'Relatório gerado com sucesso!',
        'relatorio_id': relatorio['id'],
        'ano': ano,
        'download_url': f'/api/relatorios/anual/{relatorio["id"]}/download'
    }), 200

@app.route('/api/relatorios/anual/<int:relatorio_id>/download', methods=['GET'])
@token_required
def download_relatorio_anual(relatorio_id):
    relatorio = relatorios_anuais_db.get(relatorio_id)
    
    if not relatorio:
        return jsonify({'error': 'Relatório não encontrado'}), 404
    
    user_id = request.user_payload.get('user_id')
    if relatorio.get('usuario_id') != user_id and request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    return jsonify({
        'message': 'Download disponível em breve',
        'relatorio_id': relatorio_id
    }), 200

# ==================== INICIALIZAR DADOS DE TESTE ====================

def init_test_data():
    global next_ong_id, next_doador_id, next_necessidade_id, next_evento_id, next_parceria_id, next_feedback_id, next_suporte_id, next_comunicacao_id, next_carteira_id, next_meta_id, next_vaga_id, next_doacao_financeira_id
    
    # Criar ONG de teste
    if not ongs_db:
        ong_id = next_ong_id
        ongs_db[ong_id] = {
            'id': ong_id,
            'nome': 'ONG Solidária Brasil',
            'cnpj': '12.345.678/0001-90',
            'email': 'ong@solidaria.org',
            'senha': hash_senha('Ong@123456'),
            'telefone': '(11) 99999-9999',
            'endereco': 'Rua da Solidariedade, 100',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'descricao': 'ONG dedicada a ajudar pessoas em situação de vulnerabilidade social.',
            'logo_url': None,
            'status': 'ativo',
            'data_cadastro': datetime.now(),
            'total_advertencias': 0,
            'latitude': -23.550520,
            'longitude': -46.633308,
            'endereco_completo': 'Rua da Solidariedade, 100 - São Paulo, SP',
            'media_avaliacao': 0,
            'total_avaliacoes': 0,
            'conta_bancaria': criptografar('Banco do Brasil - Ag: 1234 - CC: 56789-0'),
            'email_confirmado': True,
            'consentimento_lgpd': True,
            'data_consentimento': datetime.now()
        }
        
        carteiras_db[ong_id] = {
            'ong_id': ong_id,
            'saldo': 250.50,
            'total_recebido': 1250.50,
            'total_sacado': 1000.00,
            'data_criacao': datetime.now() - timedelta(days=30),
            'data_atualizacao': datetime.now()
        }
        next_carteira_id += 1
        next_ong_id += 1
        
        # Criar necessidade de teste
        necessidades_db[next_necessidade_id] = {
            'id': next_necessidade_id,
            'ong_id': ong_id,
            'titulo': 'Arrecadação de Alimentos',
            'descricao': 'Precisamos de alimentos não perecíveis para distribuir para 100 famílias.',
            'categoria': 'alimentos',
            'quantidade_necessaria': 500,
            'quantidade_recebida': 150,
            'urgencia': 'alta',
            'status': 'aberta',
            'data_criacao': datetime.now()
        }
        next_necessidade_id += 1
        
        # Criar evento de teste
        ong_eventos_db[next_evento_id] = {
            'id': next_evento_id,
            'ong_id': ong_id,
            'titulo': 'Dia da Solidariedade',
            'descricao': 'Venha participar do nosso evento de arrecadação de alimentos e roupas.',
            'data_evento': datetime.now() + timedelta(days=15),
            'local_evento': 'Parque da Cidade',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'status': 'ativo'
        }
        next_evento_id += 1
        
        # Criar parceria de teste
        ong_parcerias_db[next_parceria_id] = {
            'id': next_parceria_id,
            'ong_id': ong_id,
            'parceiro_nome': 'Mercado Popular',
            'tipo_parceria': 'empresa',
            'descricao': 'Parceiro na arrecadação de alimentos mensalmente.',
            'logo_url': None,
            'website_url': 'https://mercadopopular.com.br',
            'status': 'ativa'
        }
        next_parceria_id += 1
    
    # Criar doador de teste
    if not doadores_db:
        doador_id = next_doador_id
        doadores_db[doador_id] = {
            'id': doador_id,
            'nome': 'João Silva',
            'email': 'joao@email.com',
            'senha': hash_senha('Doador@123456'),
            'telefone': '(11) 98888-7777',
            'cpf': '123.456.789-00',
            'status': 'ativo',
            'data_cadastro': datetime.now(),
            'total_doacoes': 0,
            'pontuacao': 0,
            'conquistas': [],
            'email_confirmado': True,
            'consentimento_lgpd': True,
            'data_consentimento': datetime.now(),
            'endereco': 'Rua das Flores, 123',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'total_itens': 0,
            '2fa_secret': None,
            '2fa_ativado': False,
            'data_atualizacao': datetime.now()
        }
        next_doador_id += 1

init_test_data()

# ==================== EXECUTAR APP ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Servidor Doa+ iniciado!")
    print("="*60)
    print(f"📁 Servindo arquivos da pasta: {TEMPLATES_DIR}")
    print(f"📍 Acesse: http://localhost:{app.config['PORT']}")
    print("\n📝 Credenciais de teste:")
    print("  🏢 ONG: ong@solidaria.org / Ong@123456")
    print("  👤 Doador: joao@email.com / Doador@123456")
    print("  👑 Admin: admin@doamais.org / admin123")
    print("\n📋 FUNCIONALIDADES IMPLEMENTADAS:")
    print("  ⭐ Avaliação de ONGs (1-5 estrelas)")
    print("  📊 Histórico de Doações")
    print("  🔍 Busca Avançada por texto")
    print("  🏆 Ranking de Doadores")
    print("  📧 Notificações por Email")
    print("  🎯 Sistema de Metas e Campanhas")
    print("  💬 Chat em Tempo Real")
    print("  📈 Relatórios para Admin")
    print("  🤝 Sistema de Voluntariado")
    print("  💰 Doações Financeiras")
    print("  💳 Carteira Digital para ONGs")
    print("  💰 Carteira da Plataforma (Taxas)")
    print("  📝 Feedback e Suporte")
    print("  📨 Comunicação em Massa")
    print("  📅 Eventos")
    print("  🤝 Parcerias")
    print("  🔐 reCAPTCHA (com fallback para desenvolvimento)")
    print("  🔒 Proteção CSRF, SQL Injection, XSS")
    print("  📋 Logs de Auditoria")
    print("  🛡️ Rate Limiting")
    print("  🔑 Hash de senhas com bcrypt")
    print("  📜 Política de Privacidade (LGPD)")
    print("  📜 Termos de Uso")
    print("  🔐 Recuperação de Senha (3 etapas)")
    print("  👤 Perfil do Doador com Conquistas")
    print("  📊 Relatório Anual de Doações (PDF)")
    print("  🔔 Preferências de Notificação (Email/Push)")
    print("  🗑️ Solicitação de Exclusão de Conta (LGPD)")
    print("  🔐 Autenticação de Dois Fatores (2FA)")
    print("  💳 MERCADO PAGO - DOAÇÕES ONLINE")
    print("="*60)
    print("\n⚠️  Use http://localhost:5000 (não https)")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
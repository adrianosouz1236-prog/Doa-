from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
import jwt
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import re
import logging
from logging.handlers import RotatingFileHandler

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLETES_DIR = os.path.join(BASE_DIR, 'templetes')

# Criar pasta templetes se não existir
if not os.path.exists(TEMPLETES_DIR):
    os.makedirs(TEMPLETES_DIR)
    print(f"📁 Pasta 'templetes' criada em: {TEMPLETES_DIR}")

print(f"📁 Servindo arquivos estáticos de: {TEMPLETES_DIR}")

# Inicializar app
app = Flask(__name__, static_folder=TEMPLETES_DIR, static_url_path='')

# ==================== CONFIGURAÇÕES ====================
IS_PRODUCTION = os.getenv('FLASK_ENV', 'development') == 'production'

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-chave-secreta-mude')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', 2)))
app.config['DEBUG'] = not IS_PRODUCTION
app.config['ENV'] = 'production' if IS_PRODUCTION else 'development'
app.config['PORT'] = int(os.getenv('PORT', 5000))
app.config['HOST'] = os.getenv('HOST', '0.0.0.0')

# Configurar CORS
if IS_PRODUCTION:
    allowed_origins = os.getenv('CORS_ORIGINS', 'https://seudominio.com').split(',')
    CORS(app, origins=allowed_origins)
else:
    CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# Configurar logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# ==================== BANCO DE DADOS SIMULADO ====================
users_db = {}
ongs_db = {}
doadores_db = {}
necessidades_db = {}
doacoes_db = {}
logs_db = []
anuncios_db = {}
advertencias_db = {}

# IDs auto-incremento
next_user_id = 1
next_ong_id = 1
next_doador_id = 1
next_necessidade_id = 1
next_doacao_id = 1
next_log_id = 1
next_anuncio_id = 1
next_advertencia_id = 1

# ==================== UTILS ====================

def gerar_token(usuario_id, email, tipo):
    """Gera token JWT"""
    payload = {
        'user_id': usuario_id,
        'email': email,
        'tipo': tipo,
        'exp': datetime.utcnow() + app.config['JWT_ACCESS_TOKEN_EXPIRES']
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verificar_token(token):
    """Verifica e decodifica o token JWT"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except:
        return None

def token_required(f):
    """Decorator para verificar token"""
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
    """Registra log de segurança"""
    global next_log_id
    log = {
        'id': next_log_id,
        'data': datetime.now(),
        'evento': evento,
        'usuario': usuario,
        'ip': ip or request.remote_addr,
        'gravidade': gravidade
    }
    logs_db.append(log)
    next_log_id += 1
    app.logger.info(f'LOG: {evento} - Usuário: {usuario}')
    return log

def hash_senha(senha):
    """Hash de senha"""
    return hashlib.sha256(senha.encode()).hexdigest()

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_cnpj(cnpj):
    """Validação simples de CNPJ"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    return len(cnpj) == 14

# ==================== ROTAS DE PÁGINAS HTML ====================

@app.route('/')
def index():
    """Página inicial"""
    try:
        return send_from_directory(TEMPLETES_DIR, 'index.html')
    except Exception as e:
        app.logger.error(f'Erro ao servir index.html: {e}')
        files = os.listdir(TEMPLETES_DIR) if os.path.exists(TEMPLETES_DIR) else []
        return jsonify({
            'error': 'Arquivo index.html não encontrado',
            'caminho_procurado': TEMPLETES_DIR,
            'arquivos_encontrados': files
        }), 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos (HTML, CSS, JS)"""
    file_path = os.path.join(TEMPLETES_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(TEMPLETES_DIR, filename)
    return jsonify({'error': f'Arquivo {filename} não encontrado'}), 404

@app.route('/login')
@app.route('/login.html')
def login_page():
    return send_from_directory(TEMPLETES_DIR, 'login.html')

@app.route('/cadastro')
@app.route('/cadastro.html')
def cadastro_page():
    return send_from_directory(TEMPLETES_DIR, 'cadastro.html')

@app.route('/cadastro_ong.html')
def cadastro_ong_page():
    return send_from_directory(TEMPLETES_DIR, 'cadastro_ong.html')

@app.route('/cadastro_doador.html')
def cadastro_doador_page():
    return send_from_directory(TEMPLETES_DIR, 'cadastro_doador.html')

@app.route('/dashboard_ong.html')
def dashboard_ong_page():
    return send_from_directory(TEMPLETES_DIR, 'dashboard_ong.html')

@app.route('/dashboard_org.html')
def dashboard_org_page():
    return send_from_directory(TEMPLETES_DIR, 'dashboard_org.html')

@app.route('/admin.html')
def admin_page():
    return send_from_directory(TEMPLETES_DIR, 'admin.html')

@app.route('/admin_plataform.html')
def admin_plataform_page():
    return send_from_directory(TEMPLETES_DIR, 'admin_plataform.html')

@app.route('/<path:filename>.css')
def serve_css(filename):
    """Serve arquivos CSS"""
    css_file = f"{filename}.css"
    file_path = os.path.join(TEMPLETES_DIR, css_file)
    if os.path.exists(file_path):
        return send_from_directory(TEMPLETES_DIR, css_file)
    return jsonify({'error': f'CSS {css_file} não encontrado'}), 404

# ==================== ROTAS DE API ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check do servidor"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'environment': app.config['ENV'],
        'static_dir': TEMPLETES_DIR,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    """Retorna estatísticas gerais da plataforma"""
    total_ongs = len([o for o in ongs_db.values() if o.get('status') == 'ativa'])
    total_doadores = len(doadores_db)
    total_doacoes = len(doacoes_db)
    total_itens = sum(d.get('quantidade', 0) for d in doacoes_db.values())
    
    return jsonify({
        'total_ongs': total_ongs,
        'total_doadores': total_doadores,
        'total_doacoes': total_doacoes,
        'total_itens': total_itens
    }), 200

# ==================== AUTENTICAÇÃO ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login de usuários (doador, ONG, admin)"""
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    tipo = data.get('tipo')
    
    if not email or not senha or not tipo:
        return jsonify({'error': 'Email, senha e tipo são obrigatórios'}), 400
    
    usuario = None
    user_id = None
    
    if tipo == 'ong':
        for uid, ong in ongs_db.items():
            if ong.get('email') == email:
                usuario = ong
                user_id = uid
                break
    elif tipo == 'doador':
        for uid, doador in doadores_db.items():
            if doador.get('email') == email:
                usuario = doador
                user_id = uid
                break
    elif tipo == 'admin':
        if email == 'admin@doamais.org' and senha == 'admin123':
            usuario = {'id': 999, 'nome': 'Administrador', 'email': email, 'senha': hash_senha('admin123')}
            user_id = 999
    
    if not usuario or hash_senha(senha) != usuario.get('senha'):
        registrar_log(f'Tentativa de login falhou: {email}', ip=request.remote_addr, gravidade='media')
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    
    if tipo == 'ong' and usuario.get('status') == 'bloqueada':
        return jsonify({'error': 'ONG bloqueada. Contate o administrador.'}), 403
    
    token = gerar_token(user_id, email, tipo)
    registrar_log(f'Login realizado: {email}', usuario=email, ip=request.remote_addr)
    
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
def cadastro_ong():
    """Cadastro de nova ONG"""
    global next_ong_id
    
    data = request.json
    nome = data.get('nome')
    cnpj = data.get('cnpj')
    email = data.get('email')
    senha = data.get('senha')
    telefone = data.get('telefone')
    endereco = data.get('endereco')
    cidade = data.get('cidade')
    uf = data.get('uf')
    descricao = data.get('descricao')
    
    if not nome or not cnpj or not email or not senha:
        return jsonify({'error': 'Nome, CNPJ, email e senha são obrigatórios'}), 400
    
    if not validar_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    if not validar_cnpj(cnpj):
        return jsonify({'error': 'CNPJ inválido'}), 400
    
    if len(senha) < 12:
        return jsonify({'error': 'Senha deve ter no mínimo 12 caracteres'}), 400
    
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
        'status': 'ativa',
        'data_cadastro': datetime.now(),
        'total_advertencias': 0
    }
    
    next_ong_id += 1
    registrar_log(f'Nova ONG cadastrada: {nome}', usuario=email)
    
    return jsonify({'message': 'ONG cadastrada com sucesso!', 'ong_id': ong_id}), 201

@app.route('/api/auth/cadastro/doador', methods=['POST'])
def cadastro_doador():
    """Cadastro de novo doador"""
    global next_doador_id
    
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    telefone = data.get('telefone')
    
    if not nome or not email or not senha:
        return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
    
    if not validar_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    if len(senha) < 6:
        return jsonify({'error': 'Senha deve ter no mínimo 6 caracteres'}), 400
    
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
        'status': 'ativo',
        'data_cadastro': datetime.now(),
        'total_doacoes': 0
    }
    
    next_doador_id += 1
    registrar_log(f'Novo doador cadastrado: {nome}', usuario=email)
    
    return jsonify({'message': 'Doador cadastrado com sucesso!', 'doador_id': doador_id}), 201

# ==================== ROTAS DE NECESSIDADES ====================

@app.route('/api/necessidades', methods=['GET'])
def listar_necessidades():
    """Lista necessidades disponíveis para doação"""
    params = request.args
    cidade = params.get('cidade', '').lower()
    categoria = params.get('categoria', '')
    urgente = params.get('urgente', 'false').lower() == 'true'
    page = int(params.get('page', 1))
    limit = int(params.get('limit', 10))
    
    necessidades_lista = []
    for nec_id, nec in necessidades_db.items():
        if nec.get('status') != 'ativa':
            continue
        
        ong = ongs_db.get(nec.get('ong_id'))
        if not ong or ong.get('status') != 'ativa':
            continue
        
        if cidade and cidade not in ong.get('cidade', '').lower():
            continue
        if categoria and nec.get('categoria') != categoria:
            continue
        if urgente and nec.get('urgencia') != 'alta':
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
            'data_criacao': nec.get('data_criacao')
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

# ==================== ROTAS DE DOAÇÕES ====================

@app.route('/api/doacoes', methods=['POST'])
@token_required
def registrar_doacao():
    """Registra uma nova doação"""
    global next_doacao_id
    
    data = request.json
    necessidade_id = data.get('necessidade_id')
    quantidade = data.get('quantidade')
    mensagem = data.get('mensagem')
    
    user_type = request.user_payload.get('tipo')
    if user_type != 'doador':
        return jsonify({'error': 'Apenas doadores podem registrar doações'}), 403
    
    doador_id = request.user_payload.get('user_id')
    doador = doadores_db.get(doador_id)
    
    if not doador:
        return jsonify({'error': 'Doador não encontrado'}), 404
    
    necessidade = necessidades_db.get(necessidade_id)
    if not necessidade or necessidade.get('status') != 'ativa':
        return jsonify({'error': 'Necessidade não encontrada ou inativa'}), 404
    
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
    
    next_doacao_id += 1
    registrar_log(f'Nova doação registrada: {quantidade} itens', usuario=doador.get('email'))
    
    return jsonify({'message': 'Doação registrada com sucesso!', 'doacao_id': doacao_id}), 201

# ==================== ROTAS ESPECÍFICAS PARA ONG ====================

@app.route('/api/ongs/dashboard', methods=['GET'])
@token_required
def ong_dashboard():
    """Dashboard da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    necessidades_ong = [n for n in necessidades_db.values() if n.get('ong_id') == ong_id]
    doacoes_ong = [d for d in doacoes_db.values() if d.get('ong_id') == ong_id]
    
    total_necessidades = len(necessidades_ong)
    total_doacoes = len(doacoes_ong)
    total_itens = sum(d.get('quantidade', 0) for d in doacoes_ong)
    total_doadores = len(set(d.get('doador_id') for d in doacoes_ong))
    
    return jsonify({
        'total_necessidades': total_necessidades,
        'total_doacoes': total_doacoes,
        'total_itens': total_itens,
        'total_doadores': total_doadores
    }), 200

@app.route('/api/ongs/necessidades', methods=['GET', 'POST'])
@token_required
def ong_necessidades():
    """Gerencia necessidades da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    if request.method == 'GET':
        necessidades_ong = []
        for nec_id, nec in necessidades_db.items():
            if nec.get('ong_id') == ong_id:
                necessidades_ong.append({
                    'id': nec_id,
                    'titulo': nec.get('titulo'),
                    'descricao': nec.get('descricao'),
                    'categoria': nec.get('categoria'),
                    'quantidade_necessaria': nec.get('quantidade_necessaria'),
                    'quantidade_recebida': nec.get('quantidade_recebida', 0),
                    'urgencia': nec.get('urgencia'),
                    'status': nec.get('status'),
                    'data_criacao': nec.get('data_criacao')
                })
        return jsonify({'necessidades': necessidades_ong}), 200
    
    elif request.method == 'POST':
        global next_necessidade_id, next_anuncio_id
        data = request.json
        
        titulo = data.get('titulo')
        categoria = data.get('categoria')
        descricao = data.get('descricao')
        quantidade_necessaria = data.get('quantidade_necessaria')
        urgencia = data.get('urgencia', 'media')
        
        if not all([titulo, categoria, descricao, quantidade_necessaria]):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
        
        necessidade_id = next_necessidade_id
        necessidades_db[necessidade_id] = {
            'id': necessidade_id,
            'ong_id': ong_id,
            'titulo': titulo,
            'descricao': descricao,
            'categoria': categoria,
            'quantidade_necessaria': quantidade_necessaria,
            'quantidade_recebida': 0,
            'urgencia': urgencia,
            'status': 'ativa',
            'data_criacao': datetime.now()
        }
        
        anuncios_db[next_anuncio_id] = {
            'id': next_anuncio_id,
            'ong_id': ong_id,
            'ong_nome': ongs_db[ong_id].get('nome'),
            'necessidade_id': necessidade_id,
            'titulo': titulo,
            'descricao': descricao,
            'categoria': categoria,
            'urgencia': urgencia,
            'quantidade_necessaria': quantidade_necessaria,
            'quantidade_recebida': 0,
            'status': 'ativo',
            'excluido': False,
            'total_advertencias': 0,
            'data_criacao': datetime.now()
        }
        next_anuncio_id += 1
        next_necessidade_id += 1
        
        registrar_log(f'Nova necessidade criada: {titulo}', usuario=ongs_db[ong_id].get('email'))
        
        return jsonify({'message': 'Necessidade criada com sucesso!', 'necessidade_id': necessidade_id}), 201

@app.route('/api/ongs/necessidades/<int:necessidade_id>', methods=['GET', 'PUT'])
@token_required
def atualizar_necessidade(necessidade_id):
    """Obtém ou atualiza uma necessidade"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    necessidade = necessidades_db.get(necessidade_id)
    
    if not necessidade or necessidade.get('ong_id') != ong_id:
        return jsonify({'error': 'Necessidade não encontrada'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': necessidade_id,
            'titulo': necessidade.get('titulo'),
            'descricao': necessidade.get('descricao'),
            'categoria': necessidade.get('categoria'),
            'quantidade_necessaria': necessidade.get('quantidade_necessaria'),
            'urgencia': necessidade.get('urgencia')
        }), 200
    
    elif request.method == 'PUT':
        data = request.json
        necessidade.update({
            'titulo': data.get('titulo', necessidade.get('titulo')),
            'descricao': data.get('descricao', necessidade.get('descricao')),
            'categoria': data.get('categoria', necessidade.get('categoria')),
            'quantidade_necessaria': data.get('quantidade_necessaria', necessidade.get('quantidade_necessaria')),
            'urgencia': data.get('urgencia', necessidade.get('urgencia'))
        })
        
        return jsonify({'message': 'Necessidade atualizada com sucesso!'}), 200

@app.route('/api/ongs/necessidades/<int:necessidade_id>/encerrar', methods=['PUT'])
@token_required
def encerrar_necessidade(necessidade_id):
    """Encerra uma necessidade"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    necessidade = necessidades_db.get(necessidade_id)
    
    if not necessidade or necessidade.get('ong_id') != ong_id:
        return jsonify({'error': 'Necessidade não encontrada'}), 404
    
    necessidade['status'] = 'encerrada'
    
    return jsonify({'message': 'Necessidade encerrada com sucesso!'}), 200

@app.route('/api/ongs/doacoes', methods=['GET'])
@token_required
def listar_doacoes_ong():
    """Lista doações recebidas pela ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    doacoes_ong = []
    for doc_id, doc in doacoes_db.items():
        if doc.get('ong_id') == ong_id:
            doacoes_ong.append({
                'id': doc_id,
                'doador_nome': doc.get('doador_nome'),
                'necessidade_titulo': doc.get('item'),
                'quantidade': doc.get('quantidade'),
                'mensagem': doc.get('mensagem'),
                'status': doc.get('status'),
                'data': doc.get('data')
            })
    
    return jsonify({'doacoes': doacoes_ong}), 200

@app.route('/api/ongs/doacoes/<int:doacao_id>/confirmar', methods=['PUT'])
@token_required
def confirmar_doacao(doacao_id):
    """Confirma uma doação recebida"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    doacao = doacoes_db.get(doacao_id)
    
    if not doacao or doacao.get('ong_id') != ong_id:
        return jsonify({'error': 'Doação não encontrada'}), 404
    
    doacao['status'] = 'confirmada'
    
    return jsonify({'message': 'Doação confirmada com sucesso!'}), 200

@app.route('/api/ongs/perfil', methods=['GET', 'PUT'])
@token_required
def ong_perfil():
    """Gerencia perfil da ONG"""
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    ong = ongs_db.get(ong_id)
    
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'nome': ong.get('nome'),
            'email': ong.get('email'),
            'telefone': ong.get('telefone'),
            'endereco': ong.get('endereco'),
            'cidade': ong.get('cidade'),
            'descricao': ong.get('descricao')
        }), 200
    
    elif request.method == 'PUT':
        data = request.json
        ong.update({
            'nome': data.get('nome', ong.get('nome')),
            'telefone': data.get('telefone', ong.get('telefone')),
            'endereco': data.get('endereco', ong.get('endereco')),
            'cidade': data.get('cidade', ong.get('cidade')),
            'descricao': data.get('descricao', ong.get('descricao'))
        })
        
        if data.get('email'):
            ong['email'] = data.get('email')
        
        return jsonify({'message': 'Perfil atualizado com sucesso!'}), 200

# ==================== ROTAS ADMIN ====================

@app.route('/api/admin/dashboard', methods=['GET'])
@token_required
def admin_dashboard():
    """Dashboard do administrador"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    total_ongs = len([o for o in ongs_db.values() if o.get('status') == 'ativa'])
    total_doadores = len(doadores_db)
    total_anuncios = len([a for a in anuncios_db.values() if not a.get('excluido')])
    total_advertencias = len(advertencias_db)
    total_doacoes = len(doacoes_db)
    ongs_bloqueadas = len([o for o in ongs_db.values() if o.get('status') == 'bloqueada'])
    
    logs_recentes = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:10]
    
    for log in logs_recentes:
        if isinstance(log.get('data'), datetime):
            log['data'] = log['data'].isoformat()
    
    return jsonify({
        'total_ongs': total_ongs,
        'total_doadores': total_doadores,
        'total_anuncios': total_anuncios,
        'total_advertencias': total_advertencias,
        'total_doacoes': total_doacoes,
        'ongs_bloqueadas': ongs_bloqueadas,
        'logs_recentes': [{
            'data': l.get('data'),
            'evento': l.get('evento'),
            'usuario': l.get('usuario'),
            'ip': l.get('ip')
        } for l in logs_recentes]
    }), 200

@app.route('/api/admin/anuncios', methods=['GET'])
@token_required
def admin_anuncios():
    """Lista todos os anúncios (necessidades)"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    anuncios_lista = []
    for an_id, an in anuncios_db.items():
        ong = ongs_db.get(an.get('ong_id'))
        anuncios_lista.append({
            'id': an_id,
            'ong_id': an.get('ong_id'),
            'ong_nome': ong.get('nome') if ong else 'Desconhecida',
            'titulo': an.get('titulo'),
            'descricao': an.get('descricao'),
            'categoria': an.get('categoria'),
            'urgencia': an.get('urgencia'),
            'quantidade_necessaria': an.get('quantidade_necessaria'),
            'quantidade_recebida': an.get('quantidade_recebida', 0),
            'status': an.get('status'),
            'excluido': an.get('excluido', False),
            'total_advertencias': an.get('total_advertencias', 0),
            'data_criacao': an.get('data_criacao'),
            'advertencias': [a for a in advertencias_db.values() if a.get('anuncio_id') == an_id]
        })
    
    return jsonify({'anuncios': anuncios_lista}), 200

@app.route('/api/admin/anuncios/<int:anuncio_id>/excluir', methods=['DELETE'])
@token_required
def admin_excluir_anuncio(anuncio_id):
    """Exclui um anúncio"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    anuncio = anuncios_db.get(anuncio_id)
    if not anuncio:
        return jsonify({'error': 'Anúncio não encontrado'}), 404
    
    anuncio['excluido'] = True
    
    necessidade_id = anuncio.get('necessidade_id')
    if necessidade_id in necessidades_db:
        necessidades_db[necessidade_id]['status'] = 'encerrada'
    
    registrar_log(f'Anúncio #{anuncio_id} excluído por admin', gravidade='media')
    
    return jsonify({'message': 'Anúncio excluído com sucesso!'}), 200

@app.route('/api/admin/ongs', methods=['GET'])
@token_required
def admin_ongs():
    """Lista todas as ONGs"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    ongs_lista = []
    for ong_id, ong in ongs_db.items():
        ongs_lista.append({
            'id': ong_id,
            'nome': ong.get('nome'),
            'cnpj': ong.get('cnpj'),
            'email': ong.get('email'),
            'telefone': ong.get('telefone'),
            'endereco': ong.get('endereco'),
            'cidade': ong.get('cidade'),
            'status': ong.get('status', 'ativa'),
            'total_advertencias': ong.get('total_advertencias', 0),
            'data_cadastro': ong.get('data_cadastro'),
            'advertencias': [a for a in advertencias_db.values() if a.get('ong_id') == ong_id]
        })
    
    return jsonify({'ongs': ongs_lista}), 200

@app.route('/api/admin/ongs/<int:ong_id>/bloquear', methods=['PUT'])
@token_required
def admin_bloquear_ong(ong_id):
    """Bloqueia uma ONG"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    ong = ongs_db.get(ong_id)
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    ong['status'] = 'bloqueada'
    registrar_log(f'ONG #{ong_id} ({ong.get("nome")}) bloqueada por admin', gravidade='alta')
    
    return jsonify({'message': 'ONG bloqueada com sucesso!'}), 200

@app.route('/api/admin/ongs/<int:ong_id>/desbloquear', methods=['PUT'])
@token_required
def admin_desbloquear_ong(ong_id):
    """Desbloqueia uma ONG"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    ong = ongs_db.get(ong_id)
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    ong['status'] = 'ativa'
    registrar_log(f'ONG #{ong_id} ({ong.get("nome")}) desbloqueada por admin', gravidade='media')
    
    return jsonify({'message': 'ONG desbloqueada com sucesso!'}), 200

@app.route('/api/admin/doadores', methods=['GET'])
@token_required
def admin_doadores():
    """Lista todos os doadores"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doadores_lista = []
    for doador_id, doador in doadores_db.items():
        doadores_lista.append({
            'id': doador_id,
            'nome': doador.get('nome'),
            'email': doador.get('email'),
            'telefone': doador.get('telefone'),
            'status': doador.get('status', 'ativo'),
            'total_doacoes': doador.get('total_doacoes', 0),
            'data_cadastro': doador.get('data_cadastro')
        })
    
    return jsonify({'doadores': doadores_lista}), 200

@app.route('/api/admin/doadores/<int:doador_id>/bloquear', methods=['PUT'])
@token_required
def admin_bloquear_doador(doador_id):
    """Bloqueia um doador"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doador = doadores_db.get(doador_id)
    if not doador:
        return jsonify({'error': 'Doador não encontrado'}), 404
    
    doador['status'] = 'bloqueado'
    registrar_log(f'Doador #{doador_id} ({doador.get("nome")}) bloqueado por admin', gravidade='media')
    
    return jsonify({'message': 'Doador bloqueado com sucesso!'}), 200

@app.route('/api/admin/doacoes', methods=['GET'])
@token_required
def admin_doacoes():
    """Lista todas as doações"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    doacoes_lista = []
    for doc_id, doc in doacoes_db.items():
        ong = ongs_db.get(doc.get('ong_id'))
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

@app.route('/api/admin/logs', methods=['GET'])
@token_required
def admin_logs():
    """Lista logs de segurança"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    limit = int(request.args.get('limite', 50))
    logs_ordenados = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:limit]
    
    for log in logs_ordenados:
        if isinstance(log.get('data'), datetime):
            log['data'] = log['data'].isoformat()
    
    return jsonify({'logs': logs_ordenados}), 200

@app.route('/api/admin/advertencias', methods=['POST'])
@token_required
def admin_adicionar_advertencia():
    """Adiciona advertência a um anúncio ou ONG"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    data = request.json
    anuncio_id = data.get('anuncio_id')
    ong_id = data.get('ong_id')
    motivo = data.get('motivo')
    descricao = data.get('descricao')
    acao = data.get('acao')
    
    if not anuncio_id or not ong_id or not motivo:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    global next_advertencia_id
    advertencia = {
        'id': next_advertencia_id,
        'anuncio_id': anuncio_id,
        'ong_id': ong_id,
        'motivo': motivo,
        'descricao': descricao,
        'data': datetime.now(),
        'acao_tomada': acao
    }
    advertencias_db[next_advertencia_id] = advertencia
    next_advertencia_id += 1
    
    anuncio = anuncios_db.get(anuncio_id)
    if anuncio:
        anuncio['total_advertencias'] = anuncio.get('total_advertencias', 0) + 1
        
        if acao == 'remover_anuncio':
            anuncio['excluido'] = True
        
        ong = ongs_db.get(ong_id)
        if ong:
            ong['total_advertencias'] = ong.get('total_advertencias', 0) + 1
            
            if ong['total_advertencias'] >= 3 or acao == 'bloquear_ong':
                ong['status'] = 'bloqueada'
    
    registrar_log(f'Advertência aplicada ao anúncio #{anuncio_id}', gravidade='alta')
    
    return jsonify({'message': 'Advertência aplicada com sucesso!'}), 201

# ==================== ROTAS DE SEGURANÇA ====================

@app.route('/api/security/logs', methods=['GET'])
@token_required
def security_logs():
    """Retorna logs de segurança (para admin)"""
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    limit = int(request.args.get('limite', 20))
    logs_ordenados = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:limit]
    
    for log in logs_ordenados:
        if isinstance(log.get('data'), datetime):
            log['data'] = log['data'].isoformat()
    
    return jsonify({'logs': logs_ordenados}), 200

# ==================== TRATAMENTO DE ERROS ====================

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Recurso não encontrado'}), 404
    try:
        return send_from_directory(TEMPLETES_DIR, 'index.html')
    except:
        return jsonify({'error': 'Página não encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Erro interno: {error}')
    return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== INICIALIZAR DADOS DE TESTE ====================

def init_test_data():
    """Inicializa dados de teste"""
    global next_ong_id, next_doador_id, next_necessidade_id, next_anuncio_id
    
    if not ongs_db:
        ong_id = next_ong_id
        ongs_db[ong_id] = {
            'id': ong_id,
            'nome': 'ONG Solidária Brasil',
            'cnpj': '12345678000199',
            'email': 'ong@solidaria.org',
            'senha': hash_senha('ong123456'),
            'telefone': '(11) 99999-9999',
            'endereco': 'Rua da Solidariedade, 100',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'descricao': 'ONG dedicada a ajudar pessoas em situação de vulnerabilidade',
            'status': 'ativa',
            'data_cadastro': datetime.now(),
            'total_advertencias': 0
        }
        next_ong_id += 1
        
        necessidade_id = next_necessidade_id
        necessidades_db[necessidade_id] = {
            'id': necessidade_id,
            'ong_id': ong_id,
            'titulo': 'Arrecadação de Alimentos',
            'descricao': 'Precisamos de alimentos não perecíveis para distribuir para famílias carentes',
            'categoria': 'alimentos',
            'quantidade_necessaria': 500,
            'quantidade_recebida': 150,
            'urgencia': 'alta',
            'status': 'ativa',
            'data_criacao': datetime.now()
        }
        
        anuncios_db[next_anuncio_id] = {
            'id': next_anuncio_id,
            'ong_id': ong_id,
            'ong_nome': 'ONG Solidária Brasil',
            'necessidade_id': necessidade_id,
            'titulo': 'Arrecadação de Alimentos',
            'descricao': 'Precisamos de alimentos não perecíveis',
            'categoria': 'alimentos',
            'urgencia': 'alta',
            'quantidade_necessaria': 500,
            'quantidade_recebida': 150,
            'status': 'ativo',
            'excluido': False,
            'total_advertencias': 0,
            'data_criacao': datetime.now()
        }
        next_anuncio_id += 1
        next_necessidade_id += 1
    
    if not doadores_db:
        doador_id = next_doador_id
        doadores_db[doador_id] = {
            'id': doador_id,
            'nome': 'João Silva',
            'email': 'joao@email.com',
            'senha': hash_senha('doador123'),
            'telefone': '(11) 98888-7777',
            'status': 'ativo',
            'data_cadastro': datetime.now(),
            'total_doacoes': 0
        }
        next_doador_id += 1

init_test_data()

# ==================== EXECUTAR APP ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Servidor Doa+ iniciado!")
    print("="*60)
    print(f"📁 Servindo arquivos da pasta: {TEMPLETES_DIR}")
    print(f"🌍 Ambiente: {app.config['ENV']}")
    print(f"📍 Acesse: http://localhost:{app.config['PORT']}")
    print("\n📝 Credenciais de teste:")
    print("  🏢 ONG: ong@solidaria.org / ong123456")
    print("  👤 Doador: joao@email.com / doador123")
    print("  👑 Admin: admin@doamais.org / admin123")
    print("="*60)
    print("\n⚠️  IMPORTANTE: Use http://localhost:5000 (não https)")
    print("="*60 + "\n")
    
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
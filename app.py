from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
import jwt
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import re

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# Inicializar app
app = Flask(__name__, static_folder=TEMPLATES_DIR, static_url_path='')

# ==================== CONFIGURAÇÕES ====================
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui-mude-em-producao'
app.config['JWT_SECRET_KEY'] = 'jwt-chave-secreta-mude'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)
app.config['DEBUG'] = True
app.config['PORT'] = 5000
app.config['HOST'] = '0.0.0.0'

# Configurar CORS
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# ==================== BANCO DE DADOS SIMULADO ====================
ongs_db = {}
doadores_db = {}
necessidades_db = {}
doacoes_db = {}
logs_db = []
ong_fotos_db = {}
ong_eventos_db = {}
ong_parcerias_db = {}
advertencias_db = {}
feedback_db = {}
suporte_db = {}

# IDs auto-incremento
next_ong_id = 1
next_doador_id = 1
next_necessidade_id = 1
next_doacao_id = 1
next_log_id = 1
next_evento_id = 1
next_parceria_id = 1
next_foto_id = 1
next_advertencia_id = 1
next_feedback_id = 1
next_suporte_id = 1

# ==================== UTILS ====================

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
    log = {
        'id': next_log_id,
        'data': datetime.now(),
        'evento': evento,
        'usuario': usuario,
        'ip': ip or request.remote_addr if request else 'unknown',
        'gravidade': gravidade
    }
    logs_db.append(log)
    next_log_id += 1
    return log

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def validar_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_cnpj(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    return len(cnpj) == 14

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

@app.route('/necessidades')
def necessidades_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/ongs')
def ongs_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/sobre')
def sobre_page():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

# ==================== ROTAS DE API ====================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    total_ongs = len([o for o in ongs_db.values() if o.get('status') == 'ativo'])
    total_doadores = len(doadores_db)
    total_doacoes = len(doacoes_db)
    total_itens = sum(d.get('quantidade', 0) for d in doacoes_db.values())
    
    return jsonify({
        'total_ongs': total_ongs,
        'total_doadores': total_doadores,
        'total_doacoes': total_doacoes,
        'total_itens': total_itens
    }), 200

@app.route('/api/eventos', methods=['GET'])
def listar_eventos():
    eventos_futuros = []
    for evento_id, evento in ong_eventos_db.items():
        if evento.get('status') != 'ativo':
            continue
        
        data_evento = evento.get('data_evento')
        if isinstance(data_evento, str):
            data_evento = datetime.fromisoformat(data_evento)
        
        if data_evento > datetime.now():
            ong = ongs_db.get(evento.get('ong_id'))
            if ong and ong.get('status') == 'ativo':
                eventos_futuros.append({
                    'id': evento_id,
                    'ong_id': evento.get('ong_id'),
                    'ong_nome': ong.get('nome'),
                    'titulo': evento.get('titulo'),
                    'descricao': evento.get('descricao'),
                    'data_evento': evento.get('data_evento').isoformat() if hasattr(evento.get('data_evento'), 'isoformat') else evento.get('data_evento'),
                    'local_evento': evento.get('local_evento'),
                    'cidade': evento.get('cidade'),
                    'imagem_url': evento.get('imagem_url')
                })
    
    eventos_futuros.sort(key=lambda x: x.get('data_evento', ''))
    return jsonify({'eventos': eventos_futuros[:6]}), 200

# ==================== ROTA DE LOGIN ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    tipo = data.get('tipo')
    
    print(f"🔐 Tentativa de login: email={email}, tipo={tipo}")
    
    if not email or not senha or not tipo:
        return jsonify({'error': 'Email, senha e tipo são obrigatórios'}), 400
    
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
            print("✅ Admin autenticado com sucesso!")
    
    elif tipo == 'ong':
        for uid, ong in ongs_db.items():
            if ong.get('email') == email:
                if hash_senha(senha) == ong.get('senha'):
                    usuario = ong
                    user_id = uid
                    print(f"✅ ONG autenticada: {ong.get('nome')}")
                break
    
    elif tipo == 'doador':
        for uid, doador in doadores_db.items():
            if doador.get('email') == email:
                if hash_senha(senha) == doador.get('senha'):
                    usuario = doador
                    user_id = uid
                    print(f"✅ Doador autenticado: {doador.get('nome')}")
                break
    
    if not usuario:
        registrar_log(f'Tentativa de login falhou: {email}', ip=request.remote_addr, gravidade='media')
        print(f"❌ Login falhou: {email}")
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    
    if tipo == 'ong' and usuario.get('status') == 'bloqueado':
        return jsonify({'error': 'ONG bloqueada. Contate o administrador.'}), 403
    
    token = gerar_token(user_id, email, tipo)
    registrar_log(f'Login realizado: {email} ({tipo})', usuario=email, ip=request.remote_addr)
    print(f"✅ Login realizado com sucesso: {email} ({tipo})")
    
    return jsonify({
        'token': token,
        'usuario': {
            'id': user_id,
            'nome': usuario.get('nome'),
            'email': usuario.get('email')
        },
        'tipo': tipo
    }), 200

# ==================== ROTA DE CADASTRO ====================

@app.route('/api/auth/cadastro/ong', methods=['POST'])
def cadastro_ong():
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
        'logo_url': None,
        'status': 'ativo',
        'data_cadastro': datetime.now(),
        'total_advertencias': 0,
        'latitude': None,
        'longitude': None,
        'endereco_completo': None
    }
    
    next_ong_id += 1
    registrar_log(f'Nova ONG cadastrada: {nome}', usuario=email)
    
    return jsonify({'message': 'ONG cadastrada com sucesso!', 'ong_id': ong_id}), 201

@app.route('/api/auth/cadastro/doador', methods=['POST'])
def cadastro_doador():
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
    params = request.args
    cidade = params.get('cidade', '').lower()
    categoria = params.get('categoria', '')
    page = int(params.get('page', 1))
    limit = int(params.get('limit', 10))
    urgent = params.get('urgente', 'false').lower() == 'true'
    
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

@app.route('/api/necessidades/<int:necessidade_id>', methods=['GET'])
def buscar_necessidade(necessidade_id):
    nec = necessidades_db.get(necessidade_id)
    if not nec:
        return jsonify({'error': 'Necessidade não encontrada'}), 404
    
    ong = ongs_db.get(nec.get('ong_id'))
    
    return jsonify({
        'id': necessidade_id,
        'ong_id': nec.get('ong_id'),
        'ong_nome': ong.get('nome') if ong else 'Desconhecida',
        'titulo': nec.get('titulo'),
        'descricao': nec.get('descricao'),
        'categoria': nec.get('categoria'),
        'quantidade_necessaria': nec.get('quantidade_necessaria'),
        'quantidade_recebida': nec.get('quantidade_recebida', 0),
        'urgencia': nec.get('urgencia')
    }), 200

# ==================== ROTAS DE DOAÇÕES ====================

@app.route('/api/doacoes', methods=['POST'])
@token_required
def registrar_doacao():
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
    if not necessidade or necessidade.get('status') != 'aberta':
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
    
    if necessidade['quantidade_recebida'] >= necessidade['quantidade_necessaria']:
        necessidade['status'] = 'encerrada'
    
    next_doacao_id += 1
    registrar_log(f'Nova doação registrada: {quantidade} itens', usuario=doador.get('email'))
    
    return jsonify({'message': 'Doação registrada com sucesso!', 'doacao_id': doacao_id}), 201

@app.route('/api/doacoes/minhas', methods=['GET'])
@token_required
def listar_minhas_doacoes():
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Acesso restrito a doadores'}), 403
    
    doador_id = request.user_payload.get('user_id')
    
    minhas_doacoes = []
    for doc_id, doc in doacoes_db.items():
        if doc.get('doador_id') == doador_id:
            minhas_doacoes.append({
                'id': doc_id,
                'ong_nome': ongs_db.get(doc.get('ong_id'), {}).get('nome', 'Desconhecida'),
                'item': doc.get('item'),
                'quantidade': doc.get('quantidade'),
                'status': doc.get('status'),
                'data': doc.get('data')
            })
    
    return jsonify({'doacoes': minhas_doacoes}), 200

@app.route('/api/doacoes/<int:doacao_id>/confirmar', methods=['PUT'])
@token_required
def confirmar_doacao_doador(doacao_id):
    if request.user_payload.get('tipo') != 'doador':
        return jsonify({'error': 'Acesso restrito a doadores'}), 403
    
    doacao = doacoes_db.get(doacao_id)
    if not doacao or doacao.get('doador_id') != request.user_payload.get('user_id'):
        return jsonify({'error': 'Doação não encontrada'}), 404
    
    doacao['status'] = 'confirmada'
    doacao['data_confirmacao'] = datetime.now()
    
    return jsonify({'message': 'Doação confirmada com sucesso!'}), 200

# ==================== ROTAS DE ONGs ====================

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
            'longitude': ong.get('longitude')
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
        'necessidades': necessidades_ativas
    }), 200

@app.route('/api/ongs/dashboard', methods=['GET'])
@token_required
def ong_dashboard():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    necessidades_ong = [n for n in necessidades_db.values() if n.get('ong_id') == ong_id]
    doacoes_ong = [d for d in doacoes_db.values() if d.get('ong_id') == ong_id]
    eventos_ong = [e for e in ong_eventos_db.values() if e.get('ong_id') == ong_id and e.get('status') == 'ativo']
    
    total_necessidades = len(necessidades_ong)
    total_doacoes = len(doacoes_ong)
    total_itens = sum(d.get('quantidade', 0) for d in doacoes_ong)
    total_doadores = len(set(d.get('doador_id') for d in doacoes_ong))
    
    return jsonify({
        'total_necessidades': total_necessidades,
        'total_doacoes': total_doacoes,
        'total_itens': total_itens,
        'total_doadores': total_doadores,
        'total_eventos': len(eventos_ong)
    }), 200

@app.route('/api/ongs/necessidades', methods=['GET', 'POST'])
@token_required
def ong_necessidades():
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
        global next_necessidade_id
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
            'status': 'aberta',
            'data_criacao': datetime.now()
        }
        
        next_necessidade_id += 1
        registrar_log(f'Nova necessidade criada: {titulo}', usuario=ongs_db[ong_id].get('email'))
        
        return jsonify({'message': 'Necessidade criada com sucesso!', 'necessidade_id': necessidade_id}), 201

@app.route('/api/ongs/necessidades/<int:necessidade_id>', methods=['GET', 'PUT'])
@token_required
def gerenciar_necessidade(necessidade_id):
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
            'quantidade_recebida': necessidade.get('quantidade_recebida', 0),
            'urgencia': necessidade.get('urgencia'),
            'status': necessidade.get('status')
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
def confirmar_doacao_ong(doacao_id):
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    doacao = doacoes_db.get(doacao_id)
    
    if not doacao or doacao.get('ong_id') != ong_id:
        return jsonify({'error': 'Doação não encontrada'}), 404
    
    doacao['status'] = 'confirmada'
    doacao['data_confirmacao'] = datetime.now()
    
    return jsonify({'message': 'Doação confirmada com sucesso!'}), 200

@app.route('/api/ongs/perfil', methods=['GET', 'PUT'])
@token_required
def ong_perfil():
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
            'uf': ong.get('uf'),
            'descricao': ong.get('descricao'),
            'logo_url': ong.get('logo_url')
        }), 200
    
    elif request.method == 'PUT':
        data = request.json
        if data.get('nome'):
            ong['nome'] = data.get('nome')
        if data.get('telefone'):
            ong['telefone'] = data.get('telefone')
        if data.get('endereco'):
            ong['endereco'] = data.get('endereco')
        if data.get('cidade'):
            ong['cidade'] = data.get('cidade')
        if data.get('uf'):
            ong['uf'] = data.get('uf')
        if data.get('descricao'):
            ong['descricao'] = data.get('descricao')
        if data.get('email'):
            ong['email'] = data.get('email')
        if data.get('logo_url'):
            ong['logo_url'] = data.get('logo_url')
        
        return jsonify({'message': 'Perfil atualizado com sucesso!'}), 200

@app.route('/api/ongs/eventos', methods=['GET', 'POST'])
@token_required
def ong_eventos():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    if request.method == 'GET':
        eventos = []
        for ev_id, ev in ong_eventos_db.items():
            if ev.get('ong_id') == ong_id and ev.get('status') == 'ativo':
                eventos.append({
                    'id': ev_id,
                    'titulo': ev.get('titulo'),
                    'descricao': ev.get('descricao'),
                    'data_evento': ev.get('data_evento').isoformat() if hasattr(ev.get('data_evento'), 'isoformat') else ev.get('data_evento'),
                    'local_evento': ev.get('local_evento'),
                    'endereco': ev.get('endereco'),
                    'cidade': ev.get('cidade'),
                    'uf': ev.get('uf'),
                    'imagem_url': ev.get('imagem_url'),
                    'status': ev.get('status')
                })
        return jsonify({'eventos': eventos}), 200
    
    elif request.method == 'POST':
        global next_evento_id
        data = request.json
        
        titulo = data.get('titulo')
        descricao = data.get('descricao')
        data_evento = data.get('data_evento')
        local_evento = data.get('local_evento')
        endereco = data.get('endereco')
        cidade = data.get('cidade')
        uf = data.get('uf')
        imagem_url = data.get('imagem_url')
        
        if not titulo or not data_evento:
            return jsonify({'error': 'Título e data do evento são obrigatórios'}), 400
        
        evento = {
            'id': next_evento_id,
            'ong_id': ong_id,
            'titulo': titulo,
            'descricao': descricao,
            'data_evento': datetime.fromisoformat(data_evento) if isinstance(data_evento, str) else data_evento,
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
        
        registrar_log(f'Novo evento criado: {titulo}', usuario=ongs_db[ong_id].get('email'))
        
        return jsonify({'message': 'Evento criado com sucesso!', 'evento_id': evento['id']}), 201

@app.route('/api/ongs/eventos/<int:evento_id>', methods=['PUT', 'DELETE'])
@token_required
def gerenciar_evento(evento_id):
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    evento = ong_eventos_db.get(evento_id)
    
    if not evento or evento.get('ong_id') != ong_id:
        return jsonify({'error': 'Evento não encontrado'}), 404
    
    if request.method == 'PUT':
        data = request.json
        
        if data.get('titulo'):
            evento['titulo'] = data.get('titulo')
        if data.get('descricao'):
            evento['descricao'] = data.get('descricao')
        if data.get('data_evento'):
            evento['data_evento'] = datetime.fromisoformat(data.get('data_evento')) if isinstance(data.get('data_evento'), str) else data.get('data_evento')
        if data.get('local_evento'):
            evento['local_evento'] = data.get('local_evento')
        if data.get('endereco'):
            evento['endereco'] = data.get('endereco')
        if data.get('cidade'):
            evento['cidade'] = data.get('cidade')
        if data.get('uf'):
            evento['uf'] = data.get('uf')
        if data.get('imagem_url'):
            evento['imagem_url'] = data.get('imagem_url')
        
        return jsonify({'message': 'Evento atualizado com sucesso!'}), 200
    
    elif request.method == 'DELETE':
        evento['status'] = 'cancelado'
        return jsonify({'message': 'Evento cancelado com sucesso!'}), 200

@app.route('/api/ongs/parcerias', methods=['GET', 'POST'])
@token_required
def ong_parcerias():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    if request.method == 'GET':
        parcerias = []
        for par_id, par in ong_parcerias_db.items():
            if par.get('ong_id') == ong_id and par.get('status') == 'ativa':
                parcerias.append({
                    'id': par_id,
                    'parceiro_nome': par.get('parceiro_nome'),
                    'tipo_parceria': par.get('tipo_parceria'),
                    'descricao': par.get('descricao'),
                    'logo_url': par.get('logo_url'),
                    'website_url': par.get('website_url'),
                    'data_inicio': par.get('data_inicio'),
                    'status': par.get('status')
                })
        return jsonify({'parcerias': parcerias}), 200
    
    elif request.method == 'POST':
        global next_parceria_id
        data = request.json
        
        parceiro_nome = data.get('parceiro_nome')
        tipo_parceria = data.get('tipo_parceria')
        descricao = data.get('descricao')
        logo_url = data.get('logo_url')
        website_url = data.get('website_url')
        
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
            'data_inicio': datetime.now().date(),
            'status': 'ativa',
            'data_cadastro': datetime.now()
        }
        ong_parcerias_db[next_parceria_id] = parceria
        next_parceria_id += 1
        
        registrar_log(f'Nova parceria adicionada: {parceiro_nome}', usuario=ongs_db[ong_id].get('email'))
        
        return jsonify({'message': 'Parceria adicionada com sucesso!', 'parceria_id': parceria['id']}), 201

@app.route('/api/ongs/parcerias/<int:parceria_id>', methods=['PUT', 'DELETE'])
@token_required
def gerenciar_parceria(parceria_id):
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    parceria = ong_parcerias_db.get(parceria_id)
    
    if not parceria or parceria.get('ong_id') != ong_id:
        return jsonify({'error': 'Parceria não encontrada'}), 404
    
    if request.method == 'PUT':
        data = request.json
        
        if data.get('parceiro_nome'):
            parceria['parceiro_nome'] = data.get('parceiro_nome')
        if data.get('tipo_parceria'):
            parceria['tipo_parceria'] = data.get('tipo_parceria')
        if data.get('descricao'):
            parceria['descricao'] = data.get('descricao')
        if data.get('logo_url'):
            parceria['logo_url'] = data.get('logo_url')
        if data.get('website_url'):
            parceria['website_url'] = data.get('website_url')
        
        return jsonify({'message': 'Parceria atualizada com sucesso!'}), 200
    
    elif request.method == 'DELETE':
        parceria['status'] = 'encerrada'
        return jsonify({'message': 'Parceria encerrada com sucesso!'}), 200

# ==================== ROTAS DE FOTOS DA ONG ====================

@app.route('/api/ongs/fotos', methods=['GET', 'POST'])
@token_required
def ong_fotos():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    
    if request.method == 'GET':
        fotos = [f for f in ong_fotos_db.values() if f.get('ong_id') == ong_id]
        return jsonify({'fotos': fotos}), 200
    
    elif request.method == 'POST':
        global next_foto_id
        
        data = request.json
        foto_url = data.get('foto_url')
        descricao = data.get('descricao', '')
        
        if not foto_url:
            return jsonify({'error': 'URL da foto é obrigatória'}), 400
        
        fotos_atuais = [f for f in ong_fotos_db.values() if f.get('ong_id') == ong_id]
        if len(fotos_atuais) >= 3:
            return jsonify({'error': 'Limite máximo de 3 fotos atingido'}), 400
        
        foto = {
            'id': next_foto_id,
            'ong_id': ong_id,
            'foto_url': foto_url,
            'descricao': descricao,
            'data_upload': datetime.now()
        }
        ong_fotos_db[next_foto_id] = foto
        next_foto_id += 1
        
        registrar_log(f'Nova foto adicionada pela ONG #{ong_id}', usuario=ongs_db[ong_id].get('email'))
        
        return jsonify({'message': 'Foto adicionada com sucesso!', 'foto_id': foto['id']}), 201

@app.route('/api/ongs/fotos/<int:foto_id>', methods=['DELETE'])
@token_required
def remover_foto_ong(foto_id):
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    foto = ong_fotos_db.get(foto_id)
    
    if not foto or foto.get('ong_id') != ong_id:
        return jsonify({'error': 'Foto não encontrada'}), 404
    
    del ong_fotos_db[foto_id]
    registrar_log(f'Foto removida pela ONG #{ong_id}', usuario=ongs_db[ong_id].get('email'))
    
    return jsonify({'message': 'Foto removida com sucesso!'}), 200

# ==================== ROTA DE LOCALIZAÇÃO DA ONG ====================

@app.route('/api/ongs/localizacao', methods=['GET', 'PUT'])
@token_required
def ong_localizacao():
    if request.user_payload.get('tipo') != 'ong':
        return jsonify({'error': 'Acesso restrito a ONGs'}), 403
    
    ong_id = request.user_payload.get('user_id')
    ong = ongs_db.get(ong_id)
    
    if not ong:
        return jsonify({'error': 'ONG não encontrada'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'latitude': ong.get('latitude'),
            'longitude': ong.get('longitude'),
            'endereco_completo': ong.get('endereco_completo'),
            'endereco': ong.get('endereco'),
            'cidade': ong.get('cidade'),
            'uf': ong.get('uf')
        }), 200
    
    elif request.method == 'PUT':
        data = request.json
        
        if data.get('latitude') is not None:
            ong['latitude'] = data.get('latitude')
        if data.get('longitude') is not None:
            ong['longitude'] = data.get('longitude')
        if data.get('endereco_completo'):
            ong['endereco_completo'] = data.get('endereco_completo')
        if data.get('endereco'):
            ong['endereco'] = data.get('endereco')
        if data.get('cidade'):
            ong['cidade'] = data.get('cidade')
        if data.get('uf'):
            ong['uf'] = data.get('uf')
        
        registrar_log(f'Localização atualizada pela ONG #{ong_id}', usuario=ong.get('email'))
        
        return jsonify({'message': 'Localização atualizada com sucesso!'}), 200

# ==================== ROTAS DE FEEDBACK ====================

@app.route('/api/feedback', methods=['POST'])
@token_required
def enviar_feedback():
    global next_feedback_id
    
    data = request.json
    mensagem = data.get('mensagem')
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
                'data': fb.get('data').isoformat() if hasattr(fb.get('data'), 'isoformat') else fb.get('data'),
                'resposta': fb.get('resposta'),
                'data_resposta': fb.get('data_resposta').isoformat() if hasattr(fb.get('data_resposta'), 'isoformat') else fb.get('data_resposta')
            })
    
    return jsonify({'feedbacks': meus_feedbacks}), 200

# ==================== ROTAS DE SUPORTE ====================

@app.route('/api/suporte', methods=['POST'])
@token_required
def enviar_suporte():
    global next_suporte_id
    
    data = request.json
    assunto = data.get('assunto')
    mensagem = data.get('mensagem')
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
                'data': sp.get('data').isoformat() if hasattr(sp.get('data'), 'isoformat') else sp.get('data'),
                'resposta': sp.get('resposta'),
                'data_resposta': sp.get('data_resposta').isoformat() if hasattr(sp.get('data_resposta'), 'isoformat') else sp.get('data_resposta')
            })
    
    return jsonify({'suportes': meus_suportes}), 200

# ==================== ROTAS ADMIN ====================

@app.route('/api/admin/dashboard', methods=['GET'])
@token_required
def admin_dashboard():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    total_ongs = len([o for o in ongs_db.values() if o.get('status') == 'ativo'])
    total_doadores = len(doadores_db)
    total_anuncios = len(necessidades_db)
    total_advertencias = len(advertencias_db)
    total_doacoes = len(doacoes_db)
    total_feedback = len(feedback_db)
    total_suporte = len(suporte_db)
    ongs_bloqueadas = len([o for o in ongs_db.values() if o.get('status') == 'bloqueado'])
    
    logs_recentes = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:10]
    
    logs_formatados = []
    for l in logs_recentes:
        log_data = l.get('data')
        if hasattr(log_data, 'isoformat'):
            log_data = log_data.isoformat()
        logs_formatados.append({
            'data': log_data,
            'evento': l.get('evento'),
            'usuario': l.get('usuario'),
            'ip': l.get('ip')
        })
    
    return jsonify({
        'total_ongs': total_ongs,
        'total_doadores': total_doadores,
        'total_anuncios': total_anuncios,
        'total_advertencias': total_advertencias,
        'total_doacoes': total_doacoes,
        'total_feedback': total_feedback,
        'total_suporte': total_suporte,
        'ongs_bloqueadas': ongs_bloqueadas,
        'logs_recentes': logs_formatados
    }), 200

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

@app.route('/api/admin/ongs', methods=['GET'])
@token_required
def admin_ongs():
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
            'status': ong.get('status'),
            'total_advertencias': len([a for a in advertencias_db.values() if a.get('ong_id') == ong_id]),
            'data_cadastro': ong.get('data_cadastro')
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

@app.route('/api/admin/logs', methods=['GET'])
@token_required
def admin_logs():
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

@app.route('/api/admin/feedback', methods=['GET'])
@token_required
def admin_listar_feedback():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    status_filtro = request.args.get('status')
    
    lista = []
    for fid, fb in feedback_db.items():
        if status_filtro and fb.get('status') != status_filtro:
            continue
        lista.append({
            'id': fid,
            'user_nome': fb.get('user_nome'),
            'user_email': fb.get('user_email'),
            'user_type': fb.get('user_type'),
            'mensagem': fb.get('mensagem'),
            'tipo': fb.get('tipo'),
            'status': fb.get('status'),
            'data': fb.get('data').isoformat() if hasattr(fb.get('data'), 'isoformat') else fb.get('data'),
            'resposta': fb.get('resposta'),
            'data_resposta': fb.get('data_resposta').isoformat() if hasattr(fb.get('data_resposta'), 'isoformat') else fb.get('data_resposta')
        })
    
    return jsonify({'feedbacks': lista}), 200

@app.route('/api/admin/feedback/<int:feedback_id>', methods=['PUT'])
@token_required
def admin_responder_feedback(feedback_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    feedback = feedback_db.get(feedback_id)
    if not feedback:
        return jsonify({'error': 'Feedback não encontrado'}), 404
    
    data = request.json
    resposta = data.get('resposta')
    status = data.get('status', 'respondido')
    
    if not resposta:
        return jsonify({'error': 'Resposta é obrigatória'}), 400
    
    feedback['resposta'] = resposta.strip()
    feedback['status'] = status
    feedback['data_resposta'] = datetime.now()
    
    registrar_log(f'Feedback #{feedback_id} respondido pelo admin', gravidade='baixa')
    
    return jsonify({'message': 'Feedback respondido com sucesso!'}), 200

@app.route('/api/admin/suporte', methods=['GET'])
@token_required
def admin_listar_suporte():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    status_filtro = request.args.get('status')
    
    lista = []
    for sid, sp in suporte_db.items():
        if status_filtro and sp.get('status') != status_filtro:
            continue
        lista.append({
            'id': sid,
            'user_nome': sp.get('user_nome'),
            'user_email': sp.get('user_email'),
            'user_type': sp.get('user_type'),
            'assunto': sp.get('assunto'),
            'mensagem': sp.get('mensagem'),
            'categoria': sp.get('categoria'),
            'status': sp.get('status'),
            'data': sp.get('data').isoformat() if hasattr(sp.get('data'), 'isoformat') else sp.get('data'),
            'resposta': sp.get('resposta'),
            'data_resposta': sp.get('data_resposta').isoformat() if hasattr(sp.get('data_resposta'), 'isoformat') else sp.get('data_resposta'),
            'responsavel': sp.get('responsavel')
        })
    
    return jsonify({'suportes': lista}), 200

@app.route('/api/admin/suporte/<int:suporte_id>', methods=['PUT'])
@token_required
def admin_responder_suporte(suporte_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    suporte = suporte_db.get(suporte_id)
    if not suporte:
        return jsonify({'error': 'Solicitação não encontrada'}), 404
    
    data = request.json
    resposta = data.get('resposta')
    status = data.get('status', 'resolvido')
    
    if not resposta:
        return jsonify({'error': 'Resposta é obrigatória'}), 400
    
    suporte['resposta'] = resposta.strip()
    suporte['status'] = status
    suporte['data_resposta'] = datetime.now()
    suporte['responsavel'] = request.user_payload.get('email')
    
    registrar_log(f'Solicitação de suporte #{suporte_id} respondida pelo admin', gravidade='baixa')
    
    return jsonify({'message': 'Solicitação de suporte respondida com sucesso!'}), 200

@app.route('/api/admin/suporte/<int:suporte_id>/status', methods=['PUT'])
@token_required
def admin_atualizar_status_suporte(suporte_id):
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    suporte = suporte_db.get(suporte_id)
    if not suporte:
        return jsonify({'error': 'Solicitação não encontrada'}), 404
    
    data = request.json
    novo_status = data.get('status')
    
    status_validos = ['aberto', 'em_andamento', 'resolvido', 'fechado']
    if novo_status not in status_validos:
        return jsonify({'error': 'Status inválido'}), 400
    
    suporte['status'] = novo_status
    
    return jsonify({'message': 'Status atualizado com sucesso!'}), 200

# ==================== ROTA DE AJUDA ====================

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
            'titulo': 'O que fazer se tiver um problema?',
            'categoria': 'suporte',
            'conteudo': 'Utilize a opção "Suporte" no menu para reportar problemas. Nossa equipe responderá o mais rápido possível.'
        },
        {
            'id': 5,
            'titulo': 'Como funciona o sistema de feedback?',
            'categoria': 'feedback',
            'conteudo': 'O feedback permite que você envie sugestões, elogios ou críticas sobre a plataforma. Sua opinião é muito importante para nós!'
        },
        {
            'id': 6,
            'titulo': 'Dicas para uma boa doação',
            'categoria': 'doador',
            'conteudo': '• Verifique as necessidades da ONG\n• Doe itens em bom estado\n• Respeite a quantidade solicitada\n• Deixe uma mensagem de apoio'
        }
    ]
    
    categoria = request.args.get('categoria')
    if categoria:
        artigos = [a for a in artigos if a['categoria'] == categoria]
    
    return jsonify({'artigos': artigos}), 200

@app.route('/api/security/logs', methods=['GET'])
@token_required
def security_logs():
    if request.user_payload.get('tipo') != 'admin':
        return jsonify({'error': 'Acesso restrito a administradores'}), 403
    
    limit = int(request.args.get('limite', 20))
    logs_ordenados = sorted(logs_db, key=lambda x: x.get('data'), reverse=True)[:limit]
    
    for log in logs_ordenados:
        if isinstance(log.get('data'), datetime):
            log['data'] = log['data'].isoformat()
    
    return jsonify({'logs': logs_ordenados}), 200

# ==================== INICIALIZAR DADOS DE TESTE ====================

def init_test_data():
    global next_ong_id, next_doador_id, next_necessidade_id, next_evento_id, next_parceria_id, next_feedback_id, next_suporte_id
    
    if not ongs_db:
        ong_id = next_ong_id
        ongs_db[ong_id] = {
            'id': ong_id,
            'nome': 'ONG Solidária Brasil',
            'cnpj': '12.345.678/0001-90',
            'email': 'ong@solidaria.org',
            'senha': hash_senha('ong123456'),
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
            'endereco_completo': 'Rua da Solidariedade, 100 - São Paulo, SP'
        }
        next_ong_id += 1
        
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
        
        ong_eventos_db[next_evento_id] = {
            'id': next_evento_id,
            'ong_id': ong_id,
            'titulo': 'Dia da Solidariedade',
            'descricao': 'Evento de arrecadação com música e food trucks!',
            'data_evento': datetime.now() + timedelta(days=30),
            'local_evento': 'Parque da Cidade',
            'endereco': 'Av. Principal, 500',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'imagem_url': None,
            'status': 'ativo',
            'data_criacao': datetime.now()
        }
        next_evento_id += 1
        
        ong_parcerias_db[next_parceria_id] = {
            'id': next_parceria_id,
            'ong_id': ong_id,
            'parceiro_nome': 'Mercado Popular',
            'tipo_parceria': 'empresa',
            'descricao': 'Doação mensal de alimentos',
            'logo_url': None,
            'website_url': None,
            'data_inicio': datetime.now().date(),
            'status': 'ativa'
        }
        next_parceria_id += 1
        
        # Feedback de exemplo
        feedback_db[next_feedback_id] = {
            'id': next_feedback_id,
            'user_id': ong_id,
            'user_type': 'ong',
            'user_email': 'ong@solidaria.org',
            'user_nome': 'ONG Solidária Brasil',
            'mensagem': 'A plataforma é excelente! Já recebemos várias doações graças a vocês. Parabéns!',
            'tipo': 'elogio',
            'anonimo': False,
            'data': datetime.now() - timedelta(days=2),
            'status': 'pendente',
            'resposta': None,
            'data_resposta': None
        }
        next_feedback_id += 1
        
        feedback_db[next_feedback_id] = {
            'id': next_feedback_id,
            'user_id': 1,
            'user_type': 'doador',
            'user_email': 'joao@email.com',
            'user_nome': 'João Silva',
            'mensagem': 'Seria bom ter mais categorias de filtro para encontrar ONGs mais facilmente.',
            'tipo': 'sugestao',
            'anonimo': False,
            'data': datetime.now() - timedelta(days=1),
            'status': 'pendente',
            'resposta': None,
            'data_resposta': None
        }
        next_feedback_id += 1
        
        # Suporte de exemplo
        suporte_db[next_suporte_id] = {
            'id': next_suporte_id,
            'user_id': ong_id,
            'user_type': 'ong',
            'user_email': 'ong@solidaria.org',
            'user_nome': 'ONG Solidária Brasil',
            'assunto': 'Dúvida sobre confirmação de doações',
            'mensagem': 'Como faço para confirmar as doações recebidas? Não encontrei a opção no painel.',
            'categoria': 'duvida',
            'data': datetime.now() - timedelta(days=3),
            'status': 'aberto',
            'resposta': None,
            'data_resposta': None,
            'responsavel': None
        }
        next_suporte_id += 1
    
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
    print(f"📁 Servindo arquivos da pasta: {TEMPLATES_DIR}")
    print(f"📍 Acesse: http://localhost:{app.config['PORT']}")
    print("\n📝 Credenciais de teste:")
    print("  🏢 ONG: ong@solidaria.org / ong123456")
    print("  👤 Doador: joao@email.com / doador123")
    print("  👑 Admin: admin@doamais.org / admin123")
    print("\n📋 Novas funcionalidades:")
    print("  📝 Feedback: Envie comentários/sugestões")
    print("  🆘 Suporte: Reporte problemas e tire dúvidas")
    print("  📚 Central de Ajuda: Artigos informativos")
    print("="*60)
    print("\n⚠️  Use http://localhost:5000 (não https)")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
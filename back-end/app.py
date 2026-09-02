# app.py - COMPLETO COM CONTROLE DE AMBIENTE
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
load_dotenv()

# Importar configurações
from config import get_config

# Importar segurança
from security import add_security_headers, configurar_sessao_segura, is_development, gerar_csrf_token

# Importar TODOS os blueprints
from blueprints import (
    auth_bp,
    admin_bp,
    doacoes_bp,
    doacoes_financeiras_bp,
    ong_bp,
    doador_bp,
    public_bp,
    comunicacoes_bp,
    chat_bp,
    suporte_bp,
    feedback_bp,
    carteira_bp
)

# Importar rate limiter
from middleware.rate_limiter import RateLimiterMiddleware

# ==================== CONFIGURAÇÃO ====================
config = get_config()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, '..', 'templates')

app = Flask(__name__, static_folder=TEMPLATES_DIR, static_url_path='')
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
CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'https://doa-b988.onrender.com'])

# ==================== REGISTRAR BLUEPRINTS ====================
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(doacoes_bp, url_prefix='/api/doacoes')
app.register_blueprint(doacoes_financeiras_bp, url_prefix='/api/doacoes/financeiras')
app.register_blueprint(ong_bp, url_prefix='/api/ongs')
app.register_blueprint(doador_bp, url_prefix='/api/doador')
app.register_blueprint(public_bp, url_prefix='/api')
app.register_blueprint(comunicacoes_bp, url_prefix='/api/comunicacoes')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(suporte_bp, url_prefix='/api/suporte')
app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
app.register_blueprint(carteira_bp, url_prefix='/api/carteira')

print("✅ Blueprints registrados:")
print(f"   /api/auth - {auth_bp.name}")
print(f"   /api/admin - {admin_bp.name}")
print(f"   /api/doacoes - {doacoes_bp.name}")
print(f"   /api/doacoes/financeiras - {doacoes_financeiras_bp.name}")
print(f"   /api/ongs - {ong_bp.name}")
print(f"   /api/doador - {doador_bp.name}")
print(f"   /api/ - {public_bp.name}")
print(f"   /api/comunicacoes - {comunicacoes_bp.name}")
print(f"   /api/chat - {chat_bp.name}")
print(f"   /api/suporte - {suporte_bp.name}")
print(f"   /api/feedback - {feedback_bp.name}")
print(f"   /api/carteira - {carteira_bp.name}")

# ==================== INICIALIZAR RATE LIMITER ====================
RateLimiterMiddleware(app)

# ==================== ROTAS DE PÁGINAS HTML ====================
@app.route('/')
def index():
    return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Se for uma requisição para API, não interferir
    if filename.startswith('api/'):
        return jsonify({'error': 'Rota não encontrada'}), 404
    
    # Mapear caminhos corretos para JS e CSS
    if filename.startswith('javascript.js/'):
        filepath = filename.replace('javascript.js/', '')
        return send_from_directory(os.path.join(TEMPLATES_DIR, 'javascript.js'), filepath)
    
    if filename.startswith('estilos.css/'):
        filepath = filename.replace('estilos.css/', '')
        return send_from_directory(os.path.join(TEMPLATES_DIR, 'estilos.css'), filepath)
    
    # Verificar se o arquivo existe
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return send_from_directory(TEMPLATES_DIR, filename)
    
    # Para arquivos .html, retornar o arquivo específico
    if filename.endswith('.html'):
        return send_from_directory(TEMPLATES_DIR, filename)
    
    # Qualquer outra coisa, tentar servir como arquivo estático
    try:
        return send_from_directory(TEMPLATES_DIR, filename)
    except:
        return send_from_directory(TEMPLATES_DIR, 'index.html')

@app.route('/estilos.css/<path:filename>')
def serve_css(filename):
    css_dir = os.path.join(TEMPLATES_DIR, 'estilos.css')
    if os.path.exists(os.path.join(css_dir, filename)):
        return send_from_directory(css_dir, filename)
    return '', 404

@app.route('/javascript.js/<path:filename>')
def serve_js(filename):
    js_dir = os.path.join(TEMPLATES_DIR, 'javascript.js')
    if os.path.exists(os.path.join(js_dir, filename)):
        return send_from_directory(js_dir, filename)
    return '', 404

# ==================== ROTA CSRF TOKEN ====================
@app.route('/api/config/csrf-token', methods=['GET'])
def get_csrf_token():
    token = gerar_csrf_token()
    return jsonify({'csrf_token': token}), 200

# ==================== ROTA DE HEALTH CHECK ====================
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Servidor Doa+ está rodando'}), 200

# ==================== WEBHOOK MERCADO PAGO ====================
@app.route('/webhook/mercadopago', methods=['POST', 'GET'])
def webhook_mercadopago():
    from blueprints.doacoes_financeiras import processar_webhook
    return processar_webhook()

# ==================== MIDDLEWARE DE SEGURANÇA ====================
@app.after_request
def add_security_headers_to_response(response):
    return add_security_headers(response)

# ==================== INICIALIZAÇÃO ====================
if __name__ == '__main__':
    from database.repositories import init_test_data
    
    # SÓ CARREGA DADOS DE TESTE EM DESENVOLVIMENTO
    if is_development():
        init_test_data()
        
        # Verificar se os dados foram carregados
        from database.repositories import ongs_db, doadores_db, necessidades_db
        print(f"\n📊 Dados carregados:")
        print(f"   ONGs: {len(ongs_db)}")
        print(f"   Doadores: {len(doadores_db)}")
        print(f"   Necessidades: {len(necessidades_db)}")
    else:
        print("🚀 Ambiente PRODUÇÃO - Sem dados de teste")
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = is_development()
    
    print("\n" + "="*70)
    print("🚀 Servidor Doa+ iniciado!")
    print("="*70)
    print(f"📍 Acesse: http://127.0.0.1:{port}")
    print(f"🔧 Modo: {'DESENVOLVIMENTO' if debug_mode else 'PRODUÇÃO'}")
    
    print("\n" + "="*70)
    print("🔑 CREDENCIAIS DE TESTE (apenas desenvolvimento)")
    print("="*70)
    print("\n👑 ADMIN (Painel Administrativo)")
    print("   Email: admin@doamais.org")
    print("   Senha: admin123")
    print("   Tipo: admin")
    print("   Acesso: /admin_plataform.html")
    
    print("\n🏢 ONG (Organização)")
    print("   Email: ong@solidaria.org")
    print("   Senha: Ong@123456")
    print("   Tipo: ong")
    print("   Acesso: /dashboard_ong.html")
    
    print("\n👤 DOADOR (Usuário Comum)")
    print("   Email: joao@email.com")
    print("   Senha: Doador@123456")
    print("   Tipo: doador")
    print("   Acesso: /")
    
    print("\n" + "="*70)
    print("📋 ROTAS DISPONÍVEIS")
    print("="*70)
    print("\n   🌐 PÁGINAS:")
    print("   /                 - Página inicial")
    print("   /login.html       - Login")
    print("   /cadastro.html    - Cadastro")
    print("   /dashboard_ong.html - Dashboard ONG")
    print("   /admin_plataform.html - Painel Admin")
    print("   /feedback.html    - Feedback")
    print("   /suporte.html     - Suporte")
    
    print("\n   📡 API:")
    print("   /api/ongs          - Listar ONGs")
    print("   /api/necessidades  - Listar necessidades")
    print("   /api/eventos       - Listar eventos")
    print("   /api/dashboard/stats - Estatísticas")
    print("   /api/auth/login    - Login")
    print("   /api/carteira/saldo - Saldo da carteira")
    
    print("\n" + "="*70)
    print("💡 DICA: Use as credenciais acima para testar o sistema")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
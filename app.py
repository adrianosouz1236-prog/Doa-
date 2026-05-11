from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Importando configurações e blueprints
from config import Config
from api.routes.auth import auth_bp
from api.routes.ongs import ongs_bp
from api.routes.doacoes import doacoes_bp
from api.routes.security import security_bp
from api.middleware.security_headers import add_security_headers
from api.middleware.rate_limiter import limiter

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar app
app = Flask(__name__)
app.config.from_object(Config)

# Configurar CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# Configurar rate limiter
limiter.init_app(app)

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(ongs_bp, url_prefix='/api/ongs')
app.register_blueprint(doacoes_bp, url_prefix='/api/doacoes')
app.register_blueprint(security_bp, url_prefix='/api/security')

# Aplicar headers de segurança
add_security_headers(app)

# Rota de health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'environment': app.config['ENVIRONMENT']
    }), 200

# Tratamento de erros globais
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
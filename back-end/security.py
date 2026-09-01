# security.py 
import os
import re
import logging
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
import bleach
import pyotp
import qrcode
import io
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import bcrypt

load_dotenv()

# ==================== CONFIGURAÇÕES ====================

def obter_chave_fernet():
    """Obtém ou gera uma chave Fernet válida"""
    key = os.getenv('FERNET_KEY', '')
    
    if not key:
        key = Fernet.generate_key().decode()
        print(f"⚠️ GERANDO NOVA CHAVE FERNET: {key}")
        try:
            with open('.env', 'a') as f:
                f.write(f"\nFERNET_KEY={key}\n")
            print("✅ Chave Fernet salva no .env")
        except Exception as e:
            print(f"⚠️ Não foi possível salvar a chave no .env: {e}")
        return key
    
    try:
        Fernet(key.encode())
        return key
    except Exception:
        print(f"⚠️ Chave Fernet inválida: {key[:10]}...")
        new_key = Fernet.generate_key().decode()
        print(f"⚠️ GERANDO NOVA CHAVE FERNET: {new_key}")
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
            with open('.env', 'w') as f:
                key_updated = False
                for line in lines:
                    if line.startswith('FERNET_KEY='):
                        f.write(f'FERNET_KEY={new_key}\n')
                        key_updated = True
                    else:
                        f.write(line)
                if not key_updated:
                    f.write(f'\nFERNET_KEY={new_key}\n')
            print("✅ Chave Fernet atualizada no .env")
        except Exception as e:
            print(f"⚠️ Não foi possível atualizar a chave no .env: {e}")
        return new_key

FERNET_KEY = obter_chave_fernet()
cipher = Fernet(FERNET_KEY.encode())

# ==================== LOGGING ====================

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('security')

# ==================== UTILS ====================

def is_development():
    """Verifica se está em modo desenvolvimento"""
    return os.getenv('FLASK_ENV', 'development') == 'development'

def is_production():
    """Verifica se está em modo produção"""
    return os.getenv('FLASK_ENV', 'production') == 'production'

# ==================== HASH DE SENHA ====================

def hash_senha(senha):
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha, hash_armazenado):
    """Verifica se a senha corresponde ao hash"""
    if not hash_armazenado:
        return False
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))

# ==================== SANITIZAÇÃO ====================

def sanitizar_html(texto):
    """Remove tags HTML e scripts maliciosos"""
    if not texto:
        return texto
    return bleach.clean(
        texto,
        tags=[],
        strip=True,
        strip_comments=True,
        strip_eol_comments=True
    )

def sanitizar_string(texto):
    """Remove caracteres perigosos de strings"""
    if not texto:
        return ''
    texto = re.sub(r'[<>]', '', texto)
    texto = re.sub(r'[;\'"()]', '', texto)
    return texto.strip()

# ==================== VALIDAÇÃO DE SENHA ====================

def validar_senha_forte(senha):
    """
    Valida se a senha atende aos requisitos de segurança
    Retorna (bool, mensagem)
    """
    erros = []
    
    if len(senha) < 12:
        erros.append("Mínimo 12 caracteres")
    if not re.search(r'[A-Z]', senha):
        erros.append("Pelo menos 1 letra maiúscula")
    if not re.search(r'[a-z]', senha):
        erros.append("Pelo menos 1 letra minúscula")
    if not re.search(r'\d', senha):
        erros.append("Pelo menos 1 número")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        erros.append("Pelo menos 1 caractere especial")
    if re.search(r'(.)\1\1\1', senha):
        erros.append("Evite caracteres repetidos")
    
    palavras_comuns = ['senha', '123456', 'qwerty', 'password', 'admin', 'abc123']
    if any(palavra in senha.lower() for palavra in palavras_comuns):
        erros.append("Evite palavras comuns")
    
    return len(erros) == 0, ", ".join(erros) if erros else "Senha válida"

# ==================== CRIPTOGRAFIA ====================

def criptografar(dados):
    """Criptografa dados sensíveis usando Fernet"""
    if not dados:
        return None
    try:
        return cipher.encrypt(dados.encode()).decode()
    except Exception as e:
        logger.error(f"Erro ao criptografar: {e}")
        return None

def descriptografar(dados_criptografados):
    """Descriptografa dados usando Fernet"""
    if not dados_criptografados:
        return None
    try:
        return cipher.decrypt(dados_criptografados.encode()).decode()
    except Exception as e:
        logger.error(f"Erro ao descriptografar: {e}")
        return None

# ==================== 2FA ====================

def gerar_2fa_secret():
    """Gera segredo para autenticação de dois fatores"""
    return pyotp.random_base32()

def gerar_qr_code(usuario_email, secret):
    """Gera QR Code para 2FA"""
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(usuario_email, issuer_name="Doa+")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def verificar_2fa(secret, codigo):
    """Verifica código de autenticação de dois fatores"""
    if not secret or not codigo:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(codigo)
    except:
        return False

# ==================== BRUTE FORCE PROTECTION ====================

tentativas_login = {}
ips_bloqueados = {}

def verificar_tentativas_login(ip):
    """
    Verifica se o IP está bloqueado ou excedeu tentativas
    Retorna (pode_continuar, mensagem)
    """
    if ip in ips_bloqueados:
        if datetime.now() < ips_bloqueados[ip]:
            return False, f"IP bloqueado até {ips_bloqueados[ip].strftime('%H:%M:%S')}"
        else:
            del ips_bloqueados[ip]
    
    if ip in tentativas_login:
        tentativas, ultima_tentativa = tentativas_login[ip]
        if datetime.now() - ultima_tentativa > timedelta(minutes=30):
            tentativas_login[ip] = (0, datetime.now())
            return True, None
        if tentativas >= 5:
            ips_bloqueados[ip] = datetime.now() + timedelta(minutes=30)
            return False, "Muitas tentativas. Tente novamente em 30 minutos"
    
    return True, None

def registrar_tentativa_login(ip, sucesso=False):
    """Registra tentativa de login para proteção contra brute force"""
    if sucesso:
        tentativas_login[ip] = (0, datetime.now())
        if ip in ips_bloqueados:
            del ips_bloqueados[ip]
        return
    
    if ip in tentativas_login:
        tentativas, _ = tentativas_login[ip]
        tentativas_login[ip] = (tentativas + 1, datetime.now())
    else:
        tentativas_login[ip] = (1, datetime.now())

# ==================== CSRF ====================

def gerar_csrf_token():
    """Gera token CSRF para proteção contra ataques CSRF"""
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token

def verificar_csrf_token(token):
    """Verifica se o token CSRF é válido"""
    if not token:
        return False
    return token == session.get('csrf_token')

# ==================== DECORATORS ====================

def security_required(f):
    """Decorator para aplicar verificações de segurança em rotas"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            ip = request.remote_addr
            pode, mensagem = verificar_tentativas_login(ip)
            if not pode:
                return jsonify({'error': mensagem}), 429
            
            token = request.headers.get('X-CSRF-Token')
            if not token:
                token = request.json.get('csrf_token') if request.is_json else None
            if not verificar_csrf_token(token):
                return jsonify({'error': 'CSRF token inválido'}), 403
        
        return f(*args, **kwargs)
    return decorated

# ==================== SECURITY HEADERS ====================

def add_security_headers(response):
    """Adiciona headers de segurança à resposta"""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://maps.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https://via.placeholder.com; "
        "connect-src 'self' https://maps.googleapis.com; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "frame-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"
    )
    
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(self), microphone=(), camera=()'
    
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    return response

# ==================== EVENTOS DE SEGURANÇA ====================

def registrar_evento_seguranca(evento, usuario=None, ip=None, detalhes=None, gravidade='info'):
    """Registra evento de segurança no log"""
    try:
        ip = ip or request.remote_addr if request else 'unknown'
        logger.info(f"{evento} | Usuário: {usuario} | IP: {ip} | Detalhes: {detalhes}")
        return {
            'data': datetime.now().isoformat(),
            'evento': evento,
            'usuario': usuario,
            'ip': ip,
            'detalhes': detalhes,
            'gravidade': gravidade
        }
    except:
        return None

# ==================== SESSÃO SEGURA ====================

def configurar_sessao_segura(app):
    """Configura a sessão do Flask com opções de segurança"""
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    app.config['SESSION_COOKIE_NAME'] = 'doaplus_session'
    
    @app.before_request
    def generate_csrf():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)

# ==================== EXPORTAÇÕES ====================

__all__ = [
    'hash_senha',
    'verificar_senha',
    'sanitizar_html',
    'sanitizar_string',
    'validar_senha_forte',
    'criptografar',
    'descriptografar',
    'gerar_2fa_secret',
    'gerar_qr_code',
    'verificar_2fa',
    'verificar_tentativas_login',
    'registrar_tentativa_login',
    'gerar_csrf_token',
    'verificar_csrf_token',
    'security_required',
    'add_security_headers',
    'registrar_evento_seguranca',
    'configurar_sessao_segura',
    'is_development',
    'is_production',
    'logger'
]

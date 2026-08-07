# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuração principal do sistema"""
    
    # APP
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-chave-secreta-mude')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', 2)))
    
    # BANCO DE DADOS
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'postgres'),
        'charset': 'utf8mb4',
        'autocommit': False,
        'use_unicode': True
    }
    
    # SEGURANÇA
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day, 50 per hour')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # FINANCEIRO
    TAXA_PROCESSAMENTO = float(os.getenv('TAXA_PROCESSAMENTO', 3.99))
    TAXA_FIXA = float(os.getenv('TAXA_FIXA', 0.60))
    SAQUE_MINIMO = float(os.getenv('SAQUE_MINIMO', 10.00))
    PRAZO_SAQUE_DIAS = int(os.getenv('PRAZO_SAQUE_DIAS', 3))
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # LOGS
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # GOOGLE MAPS
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # SECURITY
    FERNET_KEY = os.getenv('FERNET_KEY', '')
    
    # EMAIL
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '')
    
    # PLATAFORMA
    PLATAFORMA_BANCO = os.getenv('PLATAFORMA_BANCO', 'Banco do Brasil')
    PLATAFORMA_AGENCIA = os.getenv('PLATAFORMA_AGENCIA', '1234')
    PLATAFORMA_CONTA = os.getenv('PLATAFORMA_CONTA', '12345-6')
    PLATAFORMA_TITULAR = os.getenv('PLATAFORMA_TITULAR', 'Doa+ Plataforma')
    PLATAFORMA_CNPJ = os.getenv('PLATAFORMA_CNPJ', '00.000.000/0001-00')
    
    # Sessão
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # =====================================================================
    # MERCADO PAGO - CONFIGURAÇÕES
    # =====================================================================
    MP_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN', '')
    MP_PUBLIC_KEY = os.getenv('MP_PUBLIC_KEY', '')
    MP_STATEMENT_DESCRIPTOR = os.getenv('MP_STATEMENT_DESCRIPTOR', 'Doa+ Doações')
    MP_BINARY_MODE = os.getenv('MP_BINARY_MODE', 'True').lower() == 'true'
    MP_AUTO_RETURN = os.getenv('MP_AUTO_RETURN', 'approved')
    MP_INSTALLMENTS = int(os.getenv('MP_INSTALLMENTS', 12))

    # =====================================================================
    # TAXAS DA PLATAFORMA
    # =====================================================================
    TAXA_SERVICO = float(os.getenv('TAXA_SERVICO', 3.99))
    TAXA_FIXA = float(os.getenv('TAXA_FIXA', 0.60))

    # =====================================================================
    # WEBHOOK
    # =====================================================================
    MP_WEBHOOK_URL = os.getenv('MP_WEBHOOK_URL', '')

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DB_CONFIG = {**Config.DB_CONFIG, 'database': 'doacoes_test'}

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    return configs.get(env, DevelopmentConfig)()
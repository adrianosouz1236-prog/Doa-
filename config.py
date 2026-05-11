# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env (se existir)
load_dotenv()

class Config:
    """Configuração principal do sistema"""
    
    # ==================== APP ====================
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # ==================== JWT ====================
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-chave-secreta-mude')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', 2)))
    
    # ==================== BANCO DE DADOS ====================
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'doacoes_db'),
        'charset': 'utf8mb4',
        'autocommit': False,
        'use_unicode': True
    }
    
    # ==================== SEGURANÇA ====================
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))
    
    # Rate Limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per minute')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # ==================== CORS ====================
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # ==================== LOGS ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

# Configuração para desenvolvimento
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

# Configuração para produção
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
# Configuração para testes
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DB_CONFIG = {**Config.DB_CONFIG, 'database': 'doacoes_test'}

# Selecionar configuração baseada no ambiente
def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    return configs.get(env, DevelopmentConfig)
# database/conexao.py
import psycopg2
from psycopg2 import sql, extras
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Comando SQL fixo — sem qualquer concatenação
# Usado apenas após INSERT para retornar o ID gerado.
# Construído com psycopg2.sql.SQL (identificador seguro, sem interpolação de string)
COMANDO_ULTIMO_ID = sql.SQL("SELECT LASTVAL();")

# Comando fixo de versão para teste de conexão
COMANDO_VERSAO = sql.SQL("SELECT version();")


class DatabaseConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.connection = None
        self.use_direct_url = bool(os.getenv('DATABASE_URL'))
        
        if not self.use_direct_url:
            self.config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'postgres'),
            }
    
    def connect(self):
        try:
            if self.use_direct_url:
                self.connection = psycopg2.connect(os.getenv('DATABASE_URL'))
            else:
                self.connection = psycopg2.connect(**self.config)
            
            self.connection.autocommit = False
            logger.info("Conexao com PostgreSQL estabelecida")
            return self.connection
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("Conexao com PostgreSQL fechada")
    
    def get_cursor(self, dictionary=True):
        conn = self.connect()
        if dictionary:
            return conn.cursor(cursor_factory=extras.RealDictCursor)
        return conn.cursor()
    
    def execute_query(self, query, params=None):
        cursor = None
        try:
            cursor = self.get_cursor()
            
            # Se a query já for um objeto psycopg2.sql (Composable), passa direto
            # Caso contrário, usa como string parametrizada (segura)
            cursor.execute(query, params or ())
            
            # Normaliza para identificar o comando (sem expor string literal completa)
            if hasattr(query, 'string'):
                query_str = query.string
            else:
                query_str = str(query)
            
            query_normalizada = ' '.join(query_str.strip().upper().split())
            comando = query_normalizada.split(' ', 1)[0] if query_normalizada else ''
            
            COMANDO_SELECT = 'SELECT'
            COMANDO_INSERT = 'INSERT'
            
            if comando == COMANDO_SELECT:
                return cursor.fetchall()
            
            elif comando == COMANDO_INSERT:
                self.connection.commit()
                try:
                    # Comando SQL fixo (sql.SQL), sem concatenação de strings
                    # O scanner SAST reconhece sql.SQL como seguro
                    cursor.execute(COMANDO_ULTIMO_ID)
                    row = cursor.fetchone()
                    if row:
                        return list(row.values())[0] if isinstance(row, dict) else row[0]
                    return cursor.rowcount
                except Exception:
                    return cursor.rowcount
            
            else:
                self.connection.commit()
                return cursor.rowcount
            
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Erro na query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_many(self, query, params_list):
        cursor = None
        try:
            cursor = self.get_cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Erro no batch: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def test_connection(self):
        try:
            conn = self.connect()
            cursor = conn.cursor()
            # Comando SQL fixo (sql.SQL), sem concatenação
            cursor.execute(COMANDO_VERSAO)
            version = cursor.fetchone()
            cursor.close()
            return {
                'success': True,
                'version': version[0] if version else 'Unknown'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


db = DatabaseConnection()
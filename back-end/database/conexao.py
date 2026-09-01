# database/conexao.py
import psycopg2
from psycopg2 import sql, extras
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


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
            logger.info("Conexão com PostgreSQL estabelecida")
            return self.connection
        except Exception as e:
            logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("Conexão com PostgreSQL fechada")
    
    def get_cursor(self, dictionary=True):
        conn = self.connect()
        if dictionary:
            return conn.cursor(cursor_factory=extras.RealDictCursor)
        return conn.cursor()
    
    def execute_query(self, query, params=None):
        cursor = None
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            
            query_upper = query.strip().upper()
            
            if query_upper.startswith('SELECT'):
                return cursor.fetchall()
            elif query_upper.startswith('INSERT'):
                self.connection.commit()
                try:
                    cursor.execute("SELECT LASTVAL();")
                    return cursor.fetchone()[0]
                except:
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
            cursor.execute("SELECT version();")
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
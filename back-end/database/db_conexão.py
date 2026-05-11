import mysql.connector
from mysql.connector import Error
import logging
from config import Config

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Gerenciador de conexões com MySQL"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa a conexão com o banco"""
        self.connection = None
        self.config = Config.DB_CONFIG
    
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
                logger.info("Conexão com MySQL estabelecida")
            return self.connection
        except Error as e:
            logger.error(f"Erro ao conectar ao MySQL: {e}")
            raise
    
    def disconnect(self):
        """Fecha a conexão com o banco"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexão com MySQL fechada")
    
    def get_cursor(self, dictionary=True):
        """Retorna um cursor para executar queries"""
        conn = self.connect()
        return conn.cursor(dictionary=dictionary)
    
    def execute_query(self, query, params=None):
        """Executa uma query e retorna o resultado"""
        cursor = None
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            
            self.connection.commit()
            return cursor.lastrowid
            
        except Error as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Erro na query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def execute_many(self, query, params_list):
        """Executa múltiplas queries com batch"""
        cursor = None
        try:
            cursor = self.get_cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
            return cursor.rowcount
        except Error as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Erro no batch: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

# Singleton para uso global
db = DatabaseConnection()
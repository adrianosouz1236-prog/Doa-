from database.connection import db
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditService:
    """Serviço para registro de logs de auditoria"""
    
    @classmethod
    def registrar_evento(cls, evento, usuario_id, usuario_tipo, ip, user_agent, 
                         detalhes=None, gravidade='info'):
        """
        Registra um evento no log de auditoria
        
        Args:
            evento: Nome do evento (ex: 'login_sucesso', 'doacao_realizada')
            usuario_id: ID do usuário ou None
            usuario_tipo: 'ong', 'doador' ou None
            ip: Endereço IP do usuário
            user_agent: User-Agent do navegador
            detalhes: Dict com detalhes adicionais
            gravidade: 'info', 'alerta', 'critico'
        """
        try:
            query = """
                INSERT INTO logs_seguranca 
                (evento, usuario_id, usuario_tipo, ip, user_agent, detalhes, gravidade, data_evento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            detalhes_json = json.dumps(detalhes, ensure_ascii=False) if detalhes else None
            
            db.execute_query(query, (
                evento,
                usuario_id,
                usuario_tipo,
                ip,
                user_agent[:500] if user_agent else None,  # Limitar tamanho
                detalhes_json,
                gravidade,
                datetime.now()
            ))
            
        except Exception as e:
            # Não deixar erro de log quebrar a aplicação
            logger.error(f"Erro ao registrar evento de auditoria: {e}")
    
    @classmethod
    def registrar_tentativa_login(cls, email, ip, sucesso, motivo=None):
        """Registra tentativa de login específica"""
        query = """
            INSERT INTO tentativas_login (email, ip, sucesso, data_tentativa)
            VALUES (%s, %s, %s, %s)
        """
        
        db.execute_query(query, (email, ip, sucesso, datetime.now()))
        
        if not sucesso:
            # Verificar bloqueio por múltiplas tentativas
            cls._verificar_bloqueio_ip(ip)
    
    @classmethod
    def _verificar_bloqueio_ip(cls, ip):
        """Verifica se IP deve ser bloqueado por muitas tentativas falhas"""
        query = """
            SELECT COUNT(*) as tentativas
            FROM tentativas_login
            WHERE ip = %s 
            AND sucesso = 0
            AND data_tentativa > DATE_SUB(NOW(), INTERVAL 15 MINUTE)
        """
        
        resultado = db.execute_query(query, (ip,))
        
        if resultado and resultado[0]['tentativas'] >= 10:
            # Registrar bloqueio
            cls.registrar_evento(
                evento='ip_bloqueado',
                usuario_id=None,
                usuario_tipo=None,
                ip=ip,
                user_agent=None,
                detalhes={'motivo': 'múltiplas tentativas de login falhas'},
                gravidade='critico'
            )
            logger.warning(f"IP bloqueado por múltiplas tentativas: {ip}")
    
    @classmethod
    def obter_logs_seguranca(cls, limite=100, gravidade=None):
        """Recupera logs de segurança para dashboard"""
        query = """
            SELECT id, evento, usuario_id, usuario_tipo, ip, 
                   detalhes, gravidade, data_evento
            FROM logs_seguranca
            WHERE 1=1
        """
        params = []
        
        if gravidade:
            query += " AND gravidade = %s"
            params.append(gravidade)
        
        query += " ORDER BY data_evento DESC LIMIT %s"
        params.append(limite)
        
        return db.execute_query(query, params)
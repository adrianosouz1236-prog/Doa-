# services/audit_service.py
from database.repositories import AuditRepository
from datetime import datetime

class AuditService:
    @staticmethod
    def registrar_evento(evento, usuario_id, usuario_tipo, ip, user_agent, 
                         detalhes=None, gravidade='info'):
        return AuditRepository.registrar_evento(
            evento=evento,
            usuario_id=usuario_id,
            usuario_tipo=usuario_tipo,
            ip=ip,
            user_agent=user_agent,
            detalhes=detalhes,
            gravidade=gravidade
        )
    
    @staticmethod
    def registrar_tentativa_login(email, ip, sucesso):
        return AuditRepository.registrar_tentativa_login(email, ip, sucesso)
    
    @staticmethod
    def contar_tentativas_falhas(ip, minutos=15):
        return AuditRepository.contar_tentativas_falhas(ip, minutos)
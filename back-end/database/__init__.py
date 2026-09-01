# database/__init__.py
from .conexao import db, DatabaseConnection
from .repositories import (
    OngRepository, DoadorRepository, DoacaoRepository, 
    NecessidadeRepository, CarteiraRepository, AuditRepository
)

__all__ = [
    'db', 'DatabaseConnection',
    'OngRepository', 'DoadorRepository', 'DoacaoRepository',
    'NecessidadeRepository', 'CarteiraRepository', 'AuditRepository'
]
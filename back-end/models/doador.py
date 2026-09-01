# models/doador.py
from datetime import datetime
import bcrypt
import re


class Doador:
    def __init__(self, id=None, nome=None, email=None, senha=None,
                 telefone=None, cpf=None, data_nascimento=None,
                 endereco=None, cidade=None, uf=None,
                 status='ativo', data_cadastro=None, data_atualizacao=None,
                 total_doacoes=0, pontuacao=0, conquistas=None,
                 email_confirmado=False, consentimento_lgpd=False,
                 data_consentimento=None, total_itens=0,
                 twofa_secret=None, twofa_ativado=False):
        
        self.id = id
        self.nome = nome
        self.email = email
        self._senha = senha
        self.telefone = telefone
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.endereco = endereco
        self.cidade = cidade
        self.uf = uf
        self.status = status
        self.data_cadastro = data_cadastro or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()
        self.total_doacoes = total_doacoes or 0
        self.pontuacao = pontuacao or 0
        self.conquistas = conquistas or []
        self.email_confirmado = email_confirmado or False
        self.consentimento_lgpd = consentimento_lgpd or False
        self.data_consentimento = data_consentimento
        self.total_itens = total_itens or 0
        self.twofa_secret = twofa_secret
        self.twofa_ativado = twofa_ativado or False
    
    @property
    def senha(self):
        return None
    
    @senha.setter
    def senha(self, senha_plain):
        self._senha = self._hash_senha(senha_plain)
    
    def _hash_senha(self, senha_plain):
        salt = bcrypt.gensalt(rounds=10)
        return bcrypt.hashpw(senha_plain.encode('utf-8'), salt).decode('utf-8')
    
    def verificar_senha(self, senha_plain):
        if not self._senha:
            return False
        return bcrypt.checkpw(senha_plain.encode('utf-8'), self._senha.encode('utf-8'))
    
    def to_dict(self, include_sensitive=False):
        dados = {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cpf': self._mascarar_cpf() if not include_sensitive else self.cpf,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'uf': self.uf,
            'status': self.status,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'total_doacoes': self.total_doacoes,
            'pontuacao': self.pontuacao,
            'conquistas': self.conquistas,
            'email_confirmado': self.email_confirmado,
            'consentimento_lgpd': self.consentimento_lgpd,
            'data_consentimento': self.data_consentimento.isoformat() if self.data_consentimento else None,
            'total_itens': self.total_itens,
            'twofa_ativado': self.twofa_ativado
        }
        
        if include_sensitive:
            dados['senha_hash'] = self._senha
            dados['cpf'] = self.cpf
            dados['twofa_secret'] = self.twofa_secret
        
        return dados
    
    def _mascarar_cpf(self):
        if not self.cpf or len(self.cpf) < 11:
            return None
        cpf_clean = re.sub(r'[^0-9]', '', self.cpf)
        return f"***.{cpf_clean[-4:]}"
    
    @classmethod
    def from_dict(cls, dados):
        return cls(
            id=dados.get('id'),
            nome=dados.get('nome'),
            email=dados.get('email'),
            telefone=dados.get('telefone'),
            cpf=dados.get('cpf'),
            data_nascimento=dados.get('data_nascimento'),
            endereco=dados.get('endereco'),
            cidade=dados.get('cidade'),
            uf=dados.get('uf'),
            status=dados.get('status', 'ativo'),
            data_cadastro=dados.get('data_cadastro'),
            data_atualizacao=dados.get('data_atualizacao'),
            total_doacoes=dados.get('total_doacoes', 0),
            pontuacao=dados.get('pontuacao', 0),
            conquistas=dados.get('conquistas', []),
            email_confirmado=dados.get('email_confirmado', False),
            consentimento_lgpd=dados.get('consentimento_lgpd', False),
            data_consentimento=dados.get('data_consentimento'),
            total_itens=dados.get('total_itens', 0),
            twofa_secret=dados.get('twofa_secret'),
            twofa_ativado=dados.get('twofa_ativado', False)
        )
    
    @staticmethod
    def validar_cpf(cpf):
        if not cpf:
            return True
        cpf = re.sub(r'[^0-9]', '', cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        if digito1 != int(cpf[9]):
            return False
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        if digito2 != int(cpf[10]):
            return False
        return True
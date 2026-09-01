# models/ong.py
from datetime import datetime
import bcrypt
import re


class Ong:
    def __init__(self, id=None, nome=None, cnpj=None, email=None, senha=None,
                 telefone=None, endereco=None, cidade=None, uf=None,
                 descricao=None, logo_url=None, status='pendente_verificacao',
                 banco=None, agencia=None, conta=None, tipo_conta='corrente',
                 data_cadastro=None, data_atualizacao=None,
                 data_verificacao=None, verificado_por=None,
                 documento_verificacao=None, codigo_verificacao=None,
                 dias_para_verificacao=7, motivo_rejeicao=None):
        
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.email = email
        self._senha = senha
        self.telefone = telefone
        self.endereco = endereco
        self.cidade = cidade
        self.uf = uf
        self.descricao = descricao
        self.logo_url = logo_url
        self.status = status
        self.banco = banco
        self.agencia = agencia
        self.conta = conta
        self.tipo_conta = tipo_conta
        self.data_cadastro = data_cadastro or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()
        self.data_verificacao = data_verificacao
        self.verificado_por = verificado_por
        self.documento_verificacao = documento_verificacao
        self.codigo_verificacao = codigo_verificacao
        self.dias_para_verificacao = dias_para_verificacao
        self.motivo_rejeicao = motivo_rejeicao
        self.total_advertencias = 0
        self.media_avaliacao = 0
        self.total_avaliacoes = 0
    
    @property
    def senha(self):
        return None
    
    @senha.setter
    def senha(self, senha_plain):
        self._senha = self._hash_senha(senha_plain)
    
    def _hash_senha(self, senha_plain):
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(senha_plain.encode('utf-8'), salt).decode('utf-8')
    
    def verificar_senha(self, senha_plain):
        if not self._senha:
            return False
        return bcrypt.checkpw(senha_plain.encode('utf-8'), self._senha.encode('utf-8'))
    
    def is_verificado(self):
        return self.status == 'verificado'
    
    def is_pendente(self):
        return self.status == 'pendente_verificacao'
    
    def is_rejeitado(self):
        return self.status == 'rejeitado'
    
    def is_bloqueado(self):
        return self.status == 'bloqueado'
    
    def to_dict(self, include_sensitive=False):
        dados = {
            'id': self.id,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'email': self.email,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'uf': self.uf,
            'descricao': self.descricao,
            'logo_url': self.logo_url,
            'status': self.status,
            'banco': self.banco,
            'agencia': self.agencia,
            'conta': self.conta,
            'tipo_conta': self.tipo_conta,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'data_verificacao': self.data_verificacao,
            'verificado_por': self.verificado_por,
            'codigo_verificacao': self.codigo_verificacao,
            'dias_para_verificacao': self.dias_para_verificacao,
            'motivo_rejeicao': self.motivo_rejeicao,
            'total_advertencias': self.total_advertencias,
            'media_avaliacao': self.media_avaliacao,
            'total_avaliacoes': self.total_avaliacoes
        }
        
        if include_sensitive:
            dados['senha_hash'] = self._senha
        
        return dados
    
    @classmethod
    def from_dict(cls, dados):
        return cls(
            id=dados.get('id'),
            nome=dados.get('nome'),
            cnpj=dados.get('cnpj'),
            email=dados.get('email'),
            telefone=dados.get('telefone'),
            endereco=dados.get('endereco'),
            cidade=dados.get('cidade'),
            uf=dados.get('uf'),
            descricao=dados.get('descricao'),
            logo_url=dados.get('logo_url'),
            status=dados.get('status', 'pendente_verificacao'),
            banco=dados.get('banco'),
            agencia=dados.get('agencia'),
            conta=dados.get('conta'),
            tipo_conta=dados.get('tipo_conta', 'corrente'),
            data_cadastro=dados.get('data_cadastro'),
            data_atualizacao=dados.get('data_atualizacao'),
            data_verificacao=dados.get('data_verificacao'),
            verificado_por=dados.get('verificado_por'),
            documento_verificacao=dados.get('documento_verificacao'),
            codigo_verificacao=dados.get('codigo_verificacao'),
            dias_para_verificacao=dados.get('dias_para_verificacao', 7),
            motivo_rejeicao=dados.get('motivo_rejeicao')
        )
    
    @staticmethod
    def validar_cnpj(cnpj):
        if not cnpj:
            return False
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        soma = 0
        peso = 5
        for i in range(12):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        digito1 = 11 - (soma % 11)
        if digito1 >= 10:
            digito1 = 0
        if digito1 != int(cnpj[12]):
            return False
        
        soma = 0
        peso = 6
        for i in range(13):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        digito2 = 11 - (soma % 11)
        if digito2 >= 10:
            digito2 = 0
        if digito2 != int(cnpj[13]):
            return False
        
        return True
    
    def validar(self):
        erros = []
        if not self.nome or len(self.nome) < 3:
            erros.append("Nome deve ter no mínimo 3 caracteres")
        if not self.cnpj or not self.validar_cnpj(self.cnpj):
            erros.append("CNPJ inválido")
        if not self.email:
            erros.append("E-mail é obrigatório")
        if not self._senha:
            erros.append("Senha é obrigatória")
        return {'valido': len(erros) == 0, 'erros': erros}
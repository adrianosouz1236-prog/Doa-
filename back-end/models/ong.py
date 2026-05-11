"""
models/ong.py
Modelo da tabela ONG para a plataforma Doa+
"""

from datetime import datetime
import bcrypt


class Ong:
    """Classe modelo para representar uma Organização Não Governamental (ONG)"""
    
    def __init__(self, id=None, nome=None, cnpj=None, email=None, senha=None,
                 telefone=None, endereco=None, cidade=None, uf=None,
                 descricao=None, logo_url=None, status='ativo',
                 data_cadastro=None, data_atualizacao=None):
        
        self.id = id
        self.nome = nome
        self.cnpj = cnpj
        self.email = email
        self._senha = senha  # Atributo privado para senha
        self.telefone = telefone
        self.endereco = endereco
        self.cidade = cidade
        self.uf = uf
        self.descricao = descricao
        self.logo_url = logo_url
        self.status = status
        self.data_cadastro = data_cadastro or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()
    
    @property
    def senha(self):
        """Getter da senha (retorna None por segurança)"""
        return None
    
    @senha.setter
    def senha(self, senha_plain):
        """Setter para definir a senha (já com hash)"""
        self._senha = self._hash_senha(senha_plain)
    
    def _hash_senha(self, senha_plain):
        """Gera hash bcrypt da senha"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(senha_plain.encode('utf-8'), salt).decode('utf-8')
    
    def verificar_senha(self, senha_plain):
        """Verifica se a senha fornecida corresponde ao hash"""
        if not self._senha:
            return False
        return bcrypt.checkpw(senha_plain.encode('utf-8'), self._senha.encode('utf-8'))
    
    def to_dict(self, include_sensitive=False):
        """Converte o objeto para dicionário"""
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
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
        
        # Incluir campos sensíveis apenas se solicitado
        if include_sensitive:
            dados['senha_hash'] = self._senha
        
        return dados
    
    @classmethod
    def from_dict(cls, dados):
        """Cria uma instância de Ong a partir de um dicionário"""
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
            status=dados.get('status', 'ativo'),
            data_cadastro=dados.get('data_cadastro'),
            data_atualizacao=dados.get('data_atualizacao')
        )
    
    @staticmethod
    def validar_cnpj(cnpj):
        """Valida o formato do CNPJ"""
        import re
        if not cnpj:
            return False
        # Remove caracteres não numéricos
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj) != 14:
            return False
        return True
    
    @staticmethod
    def validar_email(email):
        """Valida o formato do e-mail"""
        import re
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(padrao, email))
    
    def validar(self):
        """Valida todos os campos obrigatórios da ONG"""
        erros = []
        
        if not self.nome or len(self.nome) < 3:
            erros.append("Nome deve ter no mínimo 3 caracteres")
        
        if not self.cnpj:
            erros.append("CNPJ é obrigatório")
        elif not self.validar_cnpj(self.cnpj):
            erros.append("CNPJ inválido")
        
        if not self.email:
            erros.append("E-mail é obrigatório")
        elif not self.validar_email(self.email):
            erros.append("E-mail inválido")
        
        if not self._senha:
            erros.append("Senha é obrigatória")
        
        return {'valido': len(erros) == 0, 'erros': erros}
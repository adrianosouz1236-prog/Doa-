"""
models/doador.py
Modelo da tabela Doador para a plataforma Doa+
"""

from datetime import datetime
import bcrypt
import re


class Doador:
    """Classe modelo para representar um Doador"""
    
    def __init__(self, id=None, nome=None, email=None, senha=None,
                 telefone=None, cpf=None, data_nascimento=None,
                 endereco=None, cidade=None, uf=None,
                 status='ativo', data_cadastro=None, data_atualizacao=None):
        
        self.id = id
        self.nome = nome
        self.email = email
        self._senha = senha  # Atributo privado para senha
        self.telefone = telefone
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.endereco = endereco
        self.cidade = cidade
        self.uf = uf
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
        """Gera hash bcrypt da senha (mínimo 8 rounds para doador)"""
        salt = bcrypt.gensalt(rounds=10)  # 10 rounds para doador (mais rápido)
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
            'email': self.email,
            'telefone': self.telefone,
            'cpf': self._mascarar_cpf() if not include_sensitive else self.cpf,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'uf': self.uf,
            'status': self.status,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }
        
        # Incluir campos sensíveis apenas se solicitado
        if include_sensitive:
            dados['senha_hash'] = self._senha
            dados['cpf'] = self.cpf
        
        return dados
    
    def _mascarar_cpf(self):
        """Mascara o CPF para exibição (apenas últimos 4 dígitos)"""
        if not self.cpf or len(self.cpf) < 11:
            return None
        cpf_clean = re.sub(r'[^0-9]', '', self.cpf)
        return f"***.{cpf_clean[-4:]}"
    
    @classmethod
    def from_dict(cls, dados):
        """Cria uma instância de Doador a partir de um dicionário"""
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
            data_atualizacao=dados.get('data_atualizacao')
        )
    
    @staticmethod
    def validar_cpf(cpf):
        """Valida o formato do CPF"""
        if not cpf:
            return True  # CPF é opcional
        
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
        if cpf == cpf[0] * 11:
            return False
        
        # Validação do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        if digito1 != int(cpf[9]):
            return False
        
        # Validação do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        if digito2 != int(cpf[10]):
            return False
        
        return True
    
    @staticmethod
    def validar_email(email):
        """Valida o formato do e-mail"""
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(padrao, email))
    
    @staticmethod
    def validar_senha(senha):
        """Valida força da senha para doador (mínimo 8 caracteres, 1 letra e 1 número)"""
        if len(senha) < 8:
            return False, "Senha deve ter no mínimo 8 caracteres"
        
        if not re.search(r'[A-Za-z]', senha):
            return False, "Senha deve conter pelo menos uma letra"
        
        if not re.search(r'\d', senha):
            return False, "Senha deve conter pelo menos um número"
        
        return True, "Senha válida"
    
    def validar(self):
        """Valida todos os campos obrigatórios do doador"""
        erros = []
        
        if not self.nome or len(self.nome) < 3:
            erros.append("Nome deve ter no mínimo 3 caracteres")
        
        if not self.email:
            erros.append("E-mail é obrigatório")
        elif not self.validar_email(self.email):
            erros.append("E-mail inválido")
        
        if self.cpf and not self.validar_cpf(self.cpf):
            erros.append("CPF inválido")
        
        if self._senha:
            valido, msg = self.validar_senha(self._senha)
            if not valido:
                erros.append(msg)
        
        return {'valido': len(erros) == 0, 'erros': erros}
    
    def calcular_idade(self):
        """Calcula a idade do doador com base na data de nascimento"""
        if not self.data_nascimento:
            return None
        
        hoje = datetime.now()
        idade = hoje.year - self.data_nascimento.year
        
        # Ajusta se ainda não fez aniversário este ano
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1
        
        return idade
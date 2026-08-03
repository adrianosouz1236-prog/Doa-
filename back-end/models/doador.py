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
        """Getter da senha (retorna None por segurança)"""
        return None
    
    @senha.setter
    def senha(self, senha_plain):
        """Setter para definir a senha (já com hash)"""
        self._senha = self._hash_senha(senha_plain)
    
    def _hash_senha(self, senha_plain):
        """Gera hash bcrypt da senha (mínimo 10 rounds)"""
        salt = bcrypt.gensalt(rounds=10)
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
        """Valida o formato do CPF com dígitos verificadores"""
        if not cpf:
            return True
        
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf) != 11:
            return False
        
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
        """Valida força da senha (mínimo 12 caracteres, 1 letra e 1 número)"""
        if len(senha) < 12:
            return False, "Senha deve ter no mínimo 12 caracteres"
        
        if not re.search(r'[A-Z]', senha):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        
        if not re.search(r'[a-z]', senha):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        
        if not re.search(r'\d', senha):
            return False, "Senha deve conter pelo menos um número"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
            return False, "Senha deve conter pelo menos um caractere especial"
        
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
        
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1
        
        return idade
    
    def adicionar_conquista(self, conquista_id):
        """Adiciona uma conquista se ela não existir"""
        if conquista_id not in self.conquistas:
            self.conquistas.append(conquista_id)
            self.data_atualizacao = datetime.now()
            return True
        return False
    
    def remover_conquista(self, conquista_id):
        """Remove uma conquista se ela existir"""
        if conquista_id in self.conquistas:
            self.conquistas.remove(conquista_id)
            self.data_atualizacao = datetime.now()
            return True
        return False
    
    def atualizar_pontuacao(self, pontos):
        """Atualiza a pontuação do doador"""
        self.pontuacao += pontos
        self.data_atualizacao = datetime.now()
    
    def registrar_doacao(self, quantidade=1):
        """Registra uma nova doação do doador"""
        self.total_doacoes += 1
        self.total_itens += quantidade
        self.pontuacao += (quantidade * 10)
        self.data_atualizacao = datetime.now()
        
        # Verificar conquistas automaticamente
        self._verificar_conquistas_auto()
    
    def _verificar_conquistas_auto(self):
        """Verifica e desbloqueia conquistas automaticamente"""
        conquistas = {
            'primeira_doacao': self.total_doacoes >= 1,
            'doador_frequente': self.total_doacoes >= 5,
            'doador_master': self.total_doacoes >= 20,
            '100_pontos': self.pontuacao >= 100,
            '500_pontos': self.pontuacao >= 500,
            '1000_pontos': self.pontuacao >= 1000
        }
        
        for conquista_id, desbloqueada in conquistas.items():
            if desbloqueada and conquista_id not in self.conquistas:
                self.conquistas.append(conquista_id)
    
    def to_json(self):
        """Converte para JSON com formatação amigável"""
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cidade': self.cidade,
            'uf': self.uf,
            'status': self.status,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'total_doacoes': self.total_doacoes,
            'pontuacao': self.pontuacao,
            'conquistas': self.conquistas,
            'total_itens': self.total_itens,
            'twofa_ativado': self.twofa_ativado
        }
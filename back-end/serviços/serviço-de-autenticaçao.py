import bcrypt
import jwt
from datetime import datetime, timedelta
import re
from database.connection import db
from config import Config

class AuthService:
    """Serviço de autenticação e gerenciamento de usuários"""
    
    def __init__(self):
        self.secret_key = Config.JWT_SECRET_KEY
        self.bcrypt_rounds = Config.BCRYPT_ROUNDS
    
    def validar_senha_forte(self, senha):
        """
        Valida se a senha atende aos requisitos de segurança
        Retorna (bool, mensagem)
        """
        if len(senha) < 12:
            return False, "Senha deve ter no mínimo 12 caracteres"
        
        if not re.search(r"[A-Z]", senha):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        
        if not re.search(r"[a-z]", senha):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        
        if not re.search(r"\d", senha):
            return False, "Senha deve conter pelo menos um número"
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
            return False, "Senha deve conter pelo menos um caractere especial"
        
        return True, "Senha válida"
    
    def hash_senha(self, senha):
        """Gera hash seguro da senha"""
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')
    
    def verificar_senha(self, senha, hash_armazenado):
        """Verifica a senha de forma segura"""
        return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))
    
    def gerar_token_jwt(self, usuario_id, usuario_tipo):
        """Gera token JWT com expiração"""
        payload = {
            'user_id': usuario_id,
            'user_type': usuario_tipo,
            'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES,
            'iat': datetime.utcnow(),
            'jti': self._gerar_token_id()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def _gerar_token_id(self):
        """Gera ID único para o token"""
        import secrets
        return secrets.token_hex(16)
    
    def autenticar(self, email, senha, tipo):
        """
        Autentica usuário (ONG ou Doador)
        Retorna dict com success, token, usuario, usuario_id
        """
        try:
            if tipo == 'ong':
                query = """
                    SELECT id, nome, email, senha, cnpj, status
                    FROM ongs 
                    WHERE email = %s AND status = 'ativo'
                """
            else:
                query = """
                    SELECT id, nome, email, senha, status
                    FROM doadores 
                    WHERE email = %s AND status = 'ativo'
                """
            
            resultado = db.execute_query(query, (email,))
            
            if not resultado:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario = resultado[0]
            
            if not self.verificar_senha(senha, usuario['senha']):
                return {'success': False, 'error': 'Senha incorreta'}
            
            # Gerar token
            token = self.gerar_token_jwt(usuario['id'], tipo)
            
            # Remover senha do retorno
            del usuario['senha']
            
            return {
                'success': True,
                'token': token,
                'usuario': usuario,
                'usuario_id': usuario['id']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cadastrar_ong(self, dados):
        """Cadastra uma nova ONG"""
        try:
            # Validar email único
            query_check = "SELECT id FROM ongs WHERE email = %s"
            existe = db.execute_query(query_check, (dados['email'],))
            if existe:
                return {'success': False, 'error': 'Email já cadastrado'}
            
            # Validar CNPJ único
            query_check_cnpj = "SELECT id FROM ongs WHERE cnpj = %s"
            existe_cnpj = db.execute_query(query_check_cnpj, (dados['cnpj'],))
            if existe_cnpj:
                return {'success': False, 'error': 'CNPJ já cadastrado'}
            
            # Validar senha forte
            senha_valida, msg = self.validar_senha_forte(dados['senha'])
            if not senha_valida:
                return {'success': False, 'error': msg}
            
            # Hash da senha
            senha_hash = self.hash_senha(dados['senha'])
            
            # Inserir no banco
            query = """
                INSERT INTO ongs 
                (nome, cnpj, email, senha, telefone, endereco, cidade, uf, descricao, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ativo')
            """
            
            ong_id = db.execute_query(query, (
                dados['nome'],
                dados['cnpj'],
                dados['email'],
                senha_hash,
                dados.get('telefone'),
                dados.get('endereco'),
                dados.get('cidade'),
                dados.get('uf'),
                dados.get('descricao')
            ))
            
            return {'success': True, 'ong_id': ong_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cadastrar_doador(self, dados):
        """Cadastra um novo doador"""
        try:
            # Validar email único
            query_check = "SELECT id FROM doadores WHERE email = %s"
            existe = db.execute_query(query_check, (dados['email'],))
            if existe:
                return {'success': False, 'error': 'Email já cadastrado'}
            
            # Validar senha forte
            senha_valida, msg = self.validar_senha_forte(dados['senha'])
            if not senha_valida:
                return {'success': False, 'error': msg}
            
            # Hash da senha
            senha_hash = self.hash_senha(dados['senha'])
            
            # Inserir no banco
            query = """
                INSERT INTO doadores 
                (nome, email, senha, telefone, status)
                VALUES (%s, %s, %s, %s, 'ativo')
            """
            
            doador_id = db.execute_query(query, (
                dados['nome'],
                dados['email'],
                senha_hash,
                dados.get('telefone')
            ))
            
            return {'success': True, 'doador_id': doador_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
# services/auth_service.py - CORRIGIDO COM ADMIN
import jwt
from datetime import datetime, timedelta
from config import Config
from database.repositories import OngRepository, DoadorRepository, AdminRepository
from security import hash_senha, verificar_senha
import secrets

class AuthService:
    @staticmethod
    def autenticar(email, senha, tipo):
        usuario = None
        usuario_id = None
        
        if tipo == 'admin':
            usuario = AdminRepository.buscar_por_email(email)
            if usuario:
                usuario_id = usuario.get('id')
        elif tipo == 'ong':
            usuario = OngRepository.buscar_por_email(email)
            if usuario:
                usuario_id = usuario.get('id')
        else:
            usuario = DoadorRepository.buscar_por_email(email)
            if usuario:
                usuario_id = usuario.get('id')
        
        if not usuario:
            return {'success': False, 'error': 'Usuário não encontrado'}
        
        if not verificar_senha(senha, usuario.get('senha')):
            return {'success': False, 'error': 'Senha incorreta'}
        
        token = jwt.encode({
            'user_id': usuario_id,
            'user_type': tipo,
            'email': usuario.get('email'),
            'nome': usuario.get('nome'),
            'exp': datetime.utcnow() + timedelta(hours=2)
        }, Config.JWT_SECRET_KEY, algorithm='HS256')
        
        return {
            'success': True,
            'token': token,
            'usuario_id': usuario_id,
            'usuario': usuario
        }
    
    @staticmethod
    def cadastrar_ong(dados):
        if OngRepository.buscar_por_email(dados['email']):
            return {'success': False, 'error': 'Email já cadastrado'}
        
        if OngRepository.buscar_por_cnpj(dados['cnpj']):
            return {'success': False, 'error': 'CNPJ já cadastrado'}
        
        dados['senha'] = hash_senha(dados['senha'])
        dados['status'] = 'pendente_verificacao'
        dados['codigo_verificacao'] = secrets.token_hex(4).upper()
        
        ong_id = OngRepository.criar(dados)
        
        return {
            'success': True,
            'ong_id': ong_id,
            'codigo_verificacao': dados['codigo_verificacao'],
            'dias_para_verificacao': 7
        }
    
    @staticmethod
    def cadastrar_doador(dados):
        if DoadorRepository.buscar_por_email(dados['email']):
            return {'success': False, 'error': 'Email já cadastrado'}
        
        dados['senha'] = hash_senha(dados['senha'])
        doador_id = DoadorRepository.criar(dados)
        
        return {'success': True, 'doador_id': doador_id}

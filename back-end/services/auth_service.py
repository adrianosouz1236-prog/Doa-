# services/auth_service.py - COMPLETO COM HASHES DAS VARIÁVEIS DE AMBIENTE
import os
import jwt
from datetime import datetime, timedelta
from config import Config
from database.repositories import OngRepository, DoadorRepository, AdminRepository
from security import hash_senha, verificar_senha
import secrets

class AuthService:
    @staticmethod
    def autenticar(email, senha, tipo):
        """
        Autentica um usuário no sistema
        - Admin: usa hash das variáveis de ambiente
        - ONG e Doador: usa hash do banco de dados
        """
        usuario = None
        usuario_id = None
        
        # ============================================================
        # ADMIN - USA HASH DAS VARIÁVEIS DE AMBIENTE
        # ============================================================
        if tipo == 'admin':
            # Busca o admin no banco
            usuario = AdminRepository.buscar_por_email(email)
            if not usuario:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            
            # Pega o hash das variáveis de ambiente
            hash_admin = os.getenv('ADMIN_PASSWORD_HASH')
            
            if hash_admin:
                # Verifica a senha com o hash do .env
                if not verificar_senha(senha, hash_admin):
                    return {'success': False, 'error': 'Senha incorreta'}
            else:
                # Fallback: usa a senha do banco de dados
                if not verificar_senha(senha, usuario.get('senha')):
                    return {'success': False, 'error': 'Senha incorreta'}
            
            # Senha correta - gera token
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
                'usuario': usuario,
                'status': usuario.get('status', 'ativo')
            }
        
        # ============================================================
        # ONG - USA HASH DO BANCO DE DADOS
        # ============================================================
        elif tipo == 'ong':
            usuario = OngRepository.buscar_por_email(email)
            if not usuario:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            
            # Verifica a senha com o hash do banco
            if not verificar_senha(senha, usuario.get('senha')):
                return {'success': False, 'error': 'Senha incorreta'}
            
            # Verifica se a ONG está bloqueada
            if usuario.get('status') == 'bloqueado':
                return {'success': False, 'error': 'ONG bloqueada. Contate o administrador.'}
        
        # ============================================================
        # DOADOR - USA HASH DO BANCO DE DADOS
        # ============================================================
        else:
            usuario = DoadorRepository.buscar_por_email(email)
            if not usuario:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            
            # Verifica a senha com o hash do banco
            if not verificar_senha(senha, usuario.get('senha')):
                return {'success': False, 'error': 'Senha incorreta'}
            
            # Verifica se o doador está bloqueado
            if usuario.get('status') == 'bloqueado':
                return {'success': False, 'error': 'Doador bloqueado. Contate o administrador.'}
        
        # ============================================================
        # GERAR TOKEN PARA ONG E DOADOR
        # ============================================================
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
            'usuario': usuario,
            'status': usuario.get('status', 'ativo')
        }
    
    @staticmethod
    def cadastrar_ong(dados):
        """
        Cadastra uma nova ONG
        - A senha é HASH antes de salvar
        - Gera código de verificação
        """
        # Verifica se o email já existe
        if OngRepository.buscar_por_email(dados['email']):
            return {'success': False, 'error': 'Email já cadastrado'}
        
        # Verifica se o CNPJ já existe
        if OngRepository.buscar_por_cnpj(dados['cnpj']):
            return {'success': False, 'error': 'CNPJ já cadastrado'}
        
        # Gera hash da senha
        dados['senha'] = hash_senha(dados['senha'])
        dados['status'] = 'pendente_verificacao'
        dados['codigo_verificacao'] = secrets.token_hex(4).upper()
        
        # Salva no banco
        ong_id = OngRepository.criar(dados)
        
        # Cria carteira para a ONG
        from database.repositories import CarteiraRepository
        CarteiraRepository.criar(ong_id)
        
        return {
            'success': True,
            'ong_id': ong_id,
            'codigo_verificacao': dados['codigo_verificacao'],
            'dias_para_verificacao': 7
        }
    
    @staticmethod
    def cadastrar_doador(dados):
        """
        Cadastra um novo doador
        - A senha é HASH antes de salvar
        """
        # Verifica se o email já existe
        if DoadorRepository.buscar_por_email(dados['email']):
            return {'success': False, 'error': 'Email já cadastrado'}
        
        # Gera hash da senha
        dados['senha'] = hash_senha(dados['senha'])
        
        # Salva no banco
        doador_id = DoadorRepository.criar(dados)
        
        return {'success': True, 'doador_id': doador_id}
    
    @staticmethod
    def verificar_codigo_verificacao(ong_id, codigo):
        """
        Verifica se o código de verificação da ONG é válido
        """
        from database.repositories import OngRepository
        
        ong = OngRepository.buscar_por_id(ong_id)
        if not ong:
            return {'success': False, 'error': 'ONG não encontrada'}
        
        if ong.get('status') == 'verificado':
            return {'success': False, 'error': 'ONG já está verificada'}
        
        if ong.get('codigo_verificacao') != codigo:
            return {'success': False, 'error': 'Código de verificação inválido'}
        
        # Atualiza status
        OngRepository.atualizar_status(ong_id, 'verificado')
        
        return {'success': True, 'message': 'ONG verificada com sucesso!'}
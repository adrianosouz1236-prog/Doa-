# services/auth_service.py - CORRIGIDO
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
        usuario = None
        usuario_id = None
        
        # ============================================================
        # ADMIN - USA HASH DAS VARIÁVEIS DE AMBIENTE
        # ============================================================
        if tipo == 'admin':
            print(f"🔑 Tentativa de login ADMIN: {email}")
            
            # Busca o admin no banco
            usuario = AdminRepository.buscar_por_email(email)
            if not usuario:
                print(f"❌ Admin não encontrado: {email}")
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            
            # Pega o hash das variáveis de ambiente
            hash_admin = os.getenv('ADMIN_PASSWORD_HASH')
            print(f"🔑 Hash do ADMIN no .env: {hash_admin[:20]}..." if hash_admin else "❌ Hash ADMIN não encontrado no .env")
            
            if hash_admin:
                # Verifica a senha com o hash do .env
                if verificar_senha(senha, hash_admin):
                    print("✅ Senha ADMIN correta (hash do .env)")
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
                else:
                    print("❌ Senha ADMIN incorreta")
                    return {'success': False, 'error': 'Senha incorreta'}
            else:
                # Fallback: usa a senha do banco de dados
                print("⚠️ Usando hash do banco de dados (fallback)")
                if not verificar_senha(senha, usuario.get('senha')):
                    return {'success': False, 'error': 'Senha incorreta'}
        
        # ============================================================
        # ONG - USA HASH DO BANCO DE DADOS
        # ============================================================
        elif tipo == 'ong':
            print(f"🔑 Tentativa de login ONG: {email}")
            usuario = OngRepository.buscar_por_email(email)
            if not usuario:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            
            if not verificar_senha(senha, usuario.get('senha')):
                return {'success': False, 'error': 'Senha incorreta'}
            
            if usuario.get('status') == 'bloqueado':
                return {'success': False, 'error': 'ONG bloqueada. Contate o administrador.'}
        
        # ============================================================
        # DOADOR - USA HASH DO BANCO DE DADOS
        # ============================================================
        else:
            print(f"🔑 Tentativa de login DOADOR: {email}")
            usuario = DoadorRepository.buscar_por_email(email)
            if not usuario:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            
            if not verificar_senha(senha, usuario.get('senha')):
                return {'success': False, 'error': 'Senha incorreta'}
            
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
        if OngRepository.buscar_por_email(dados['email']):
            return {'success': False, 'error': 'Email já cadastrado'}
        
        if OngRepository.buscar_por_cnpj(dados['cnpj']):
            return {'success': False, 'error': 'CNPJ já cadastrado'}
        
        dados['senha'] = hash_senha(dados['senha'])
        dados['status'] = 'pendente_verificacao'
        dados['codigo_verificacao'] = secrets.token_hex(4).upper()
        
        ong_id = OngRepository.criar(dados)
        
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
        if DoadorRepository.buscar_por_email(dados['email']):
            return {'success': False, 'error': 'Email já cadastrado'}
        
        dados['senha'] = hash_senha(dados['senha'])
        doador_id = DoadorRepository.criar(dados)
        
        return {'success': True, 'doador_id': doador_id}
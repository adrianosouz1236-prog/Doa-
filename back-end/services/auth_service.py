# services/auth_service.py - COMPLETO COM LOGS DE DEBUG
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
        print("="*60)
        print(f"🔑 TENTATIVA DE LOGIN")
        print(f"   Email: {email}")
        print(f"   Tipo: {tipo}")
        print("="*60)
        
        usuario = None
        usuario_id = None
        
        # ============================================================
        # ADMIN - USA HASH DAS VARIÁVEIS DE AMBIENTE
        # ============================================================
        if tipo == 'admin':
            print("👑 Verificando ADMIN...")
            
            # Busca o admin no banco
            usuario = AdminRepository.buscar_por_email(email)
            if not usuario:
                print(f"❌ Admin não encontrado: {email}")
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            print(f"✅ Admin encontrado: {usuario.get('nome')} (ID: {usuario_id})")
            
            # Pega o hash das variáveis de ambiente
            hash_admin = os.getenv('ADMIN_PASSWORD_HASH')
            print(f"🔑 ADMIN_PASSWORD_HASH do .env: {hash_admin[:20] if hash_admin else 'NÃO ENCONTRADO'}...")
            
            if hash_admin:
                # Verifica a senha com o hash do .env
                senha_correta = verificar_senha(senha, hash_admin)
                print(f"🔐 Senha correta? {senha_correta}")
                
                if senha_correta:
                    print("✅ Login ADMIN autorizado!")
                    
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
                    print("❌ Senha incorreta")
                    return {'success': False, 'error': 'Senha incorreta'}
            else:
                print("⚠️ Hash ADMIN não encontrado no .env")
                print("🔍 Verificando senha no banco de dados (fallback)...")
                
                # Fallback: usa a senha do banco de dados
                if not verificar_senha(senha, usuario.get('senha')):
                    print("❌ Senha incorreta (fallback)")
                    return {'success': False, 'error': 'Senha incorreta'}
                
                print("✅ Login ADMIN autorizado (fallback)!")
                
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
            print("🏢 Verificando ONG...")
            
            usuario = OngRepository.buscar_por_email(email)
            if not usuario:
                print(f"❌ ONG não encontrada: {email}")
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            print(f"✅ ONG encontrada: {usuario.get('nome')} (ID: {usuario_id})")
            
            # Verifica a senha com o hash do banco
            if not verificar_senha(senha, usuario.get('senha')):
                print("❌ Senha incorreta")
                return {'success': False, 'error': 'Senha incorreta'}
            
            print("✅ Senha correta!")
            
            # Verifica se a ONG está bloqueada
            if usuario.get('status') == 'bloqueado':
                print("❌ ONG está bloqueada")
                return {'success': False, 'error': 'ONG bloqueada. Contate o administrador.'}
            
            print("✅ Login ONG autorizado!")
        
        # ============================================================
        # DOADOR - USA HASH DO BANCO DE DADOS
        # ============================================================
        else:
            print("👤 Verificando DOADOR...")
            
            usuario = DoadorRepository.buscar_por_email(email)
            if not usuario:
                print(f"❌ Doador não encontrado: {email}")
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            usuario_id = usuario.get('id')
            print(f"✅ Doador encontrado: {usuario.get('nome')} (ID: {usuario_id})")
            
            # Verifica a senha com o hash do banco
            if not verificar_senha(senha, usuario.get('senha')):
                print("❌ Senha incorreta")
                return {'success': False, 'error': 'Senha incorreta'}
            
            print("✅ Senha correta!")
            
            # Verifica se o doador está bloqueado
            if usuario.get('status') == 'bloqueado':
                print("❌ Doador está bloqueado")
                return {'success': False, 'error': 'Doador bloqueado. Contate o administrador.'}
            
            print("✅ Login DOADOR autorizado!")
        
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
        
        print("="*60)
        print("✅ LOGIN REALIZADO COM SUCESSO!")
        print("="*60)
        
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
        print(f"📝 Cadastrando ONG: {dados.get('email')}")
        
        # Verifica se o email já existe
        if OngRepository.buscar_por_email(dados['email']):
            print(f"❌ Email já cadastrado: {dados['email']}")
            return {'success': False, 'error': 'Email já cadastrado'}
        
        # Verifica se o CNPJ já existe
        if OngRepository.buscar_por_cnpj(dados['cnpj']):
            print(f"❌ CNPJ já cadastrado: {dados['cnpj']}")
            return {'success': False, 'error': 'CNPJ já cadastrado'}
        
        # Gera hash da senha
        dados['senha'] = hash_senha(dados['senha'])
        dados['status'] = 'pendente_verificacao'
        dados['codigo_verificacao'] = secrets.token_hex(4).upper()
        
        # Salva no banco
        ong_id = OngRepository.criar(dados)
        print(f"✅ ONG criada com ID: {ong_id}")
        
        # Cria carteira para a ONG
        from database.repositories import CarteiraRepository
        CarteiraRepository.criar(ong_id)
        print(f"✅ Carteira criada para ONG ID: {ong_id}")
        
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
        print(f"📝 Cadastrando DOADOR: {dados.get('email')}")
        
        # Verifica se o email já existe
        if DoadorRepository.buscar_por_email(dados['email']):
            print(f"❌ Email já cadastrado: {dados['email']}")
            return {'success': False, 'error': 'Email já cadastrado'}
        
        # Gera hash da senha
        dados['senha'] = hash_senha(dados['senha'])
        
        # Salva no banco
        doador_id = DoadorRepository.criar(dados)
        print(f"✅ Doador criado com ID: {doador_id}")
        
        return {'success': True, 'doador_id': doador_id}
    
    @staticmethod
    def verificar_codigo_verificacao(ong_id, codigo):
        """
        Verifica se o código de verificação da ONG é válido
        """
        from database.repositories import OngRepository
        
        print(f"🔍 Verificando código para ONG ID: {ong_id}")
        
        ong = OngRepository.buscar_por_id(ong_id)
        if not ong:
            print(f"❌ ONG não encontrada: {ong_id}")
            return {'success': False, 'error': 'ONG não encontrada'}
        
        if ong.get('status') == 'verificado':
            print(f"⚠️ ONG já está verificada")
            return {'success': False, 'error': 'ONG já está verificada'}
        
        if ong.get('codigo_verificacao') != codigo:
            print(f"❌ Código inválido: {codigo}")
            return {'success': False, 'error': 'Código de verificação inválido'}
        
        # Atualiza status
        OngRepository.atualizar_status(ong_id, 'verificado')
        print(f"✅ ONG verificada com sucesso!")
        
        return {'success': True, 'message': 'ONG verificada com sucesso!'}
"""
Script para gerar senha aleatória do administrador
Execute: python generate_admin.py
"""
import bcrypt
import secrets
import string
from datetime import datetime

def gerar_senha_aleatoria(tamanho=20):
    """Gera uma senha aleatória forte"""
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return ''.join(secrets.choice(caracteres) for _ in range(tamanho))

def gerar_hash_senha(senha, rounds=12):
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt(rounds=rounds)
    hash_senha = bcrypt.hashpw(senha.encode('utf-8'), salt)
    return hash_senha.decode('utf-8'), salt.decode('utf-8')

def main():
    print("="*70)
    print("🔐 GERADOR DE SENHA ADMINISTRADOR - Doa+")
    print("="*70)
    
    senha_admin = gerar_senha_aleatoria(20)
    print(f"\n📝 SENHA GERADA: {senha_admin}")
    print("⚠️  GUARDE ESTA SENHA EM LOCAL SEGURO!")
    
    hash_senha, salt = gerar_hash_senha(senha_admin)
    
    print("\n" + "="*70)
    print("📋 ADICIONE NO ARQUIVO .env:")
    print("="*70)
    print(f"ADMIN_EMAIL=admin@doamais.org")
    print(f"ADMIN_PASSWORD_HASH={hash_senha}")
    print(f"ADMIN_PASSWORD_SALT={salt}")
    print("="*70)
    
    with open('admin_credentials.txt', 'w') as f:
        f.write(f"""
========================================
🔐 CREDENCIAIS DO ADMINISTRADOR - Doa+
========================================
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Email: admin@doamais.org
SENHA: {senha_admin}
HASH: {hash_senha}
SALT: {salt}

⚠️  GUARDE ESTE ARQUIVO EM LOCAL SEGURO!
========================================
""")
    
    print("\n✅ Credenciais salvas em 'admin_credentials.txt'")
    print("⚠️  NUNCA COMMITE este arquivo no repositório!")
    print("="*70)

if __name__ == "__main__":
    main()

# gerar_hashes.py
import bcrypt
import os
import sys

def gerar_hash(senha):
    """
    Gera um hash bcrypt para a senha fornecida
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha, hash_armazenado):
    """
    Verifica se a senha corresponde ao hash
    """
    return bcrypt.checkpw(senha.encode('utf-8'), hash_armazenado.encode('utf-8'))

def main():
    print("=" * 70)
    print("🔑 GERADOR DE HASHES PARA VARIÁVEIS DE AMBIENTE")
    print("   Doa+ Plataforma - Autenticação de Teste")
    print("=" * 70)
    print()
    
    # ============================================================
    # ADMIN
    # ============================================================
    print("👑 ADMIN")
    print("-" * 40)
    admin_senha = input("Digite a senha do ADMIN (padrão: admin123): ").strip()
    if not admin_senha:
        admin_senha = "admin123"
        print(f"   Usando senha padrão: {admin_senha}")
    
    # ============================================================
    # ONG
    # ============================================================
    print("\n🏢 ONG DE TESTE")
    print("-" * 40)
    ong_senha = input("Digite a senha da ONG de teste (padrão: Ong@123456): ").strip()
    if not ong_senha:
        ong_senha = "Ong@123456"
        print(f"   Usando senha padrão: {ong_senha}")
    
    # ============================================================
    # DOADOR
    # ============================================================
    print("\n👤 DOADOR DE TESTE")
    print("-" * 40)
    doador_senha = input("Digite a senha do DOADOR de teste (padrão: Doador@123456): ").strip()
    if not doador_senha:
        doador_senha = "Doador@123456"
        print(f"   Usando senha padrão: {doador_senha}")
    
    # ============================================================
    # GERAR HASHES
    # ============================================================
    print("\n" + "=" * 70)
    print("📋 COPIAR E COLAR NO .env E NO RENDER:")
    print("=" * 70)
    print()
    
    admin_hash = gerar_hash(admin_senha)
    ong_hash = gerar_hash(ong_senha)
    doador_hash = gerar_hash(doador_senha)
    
    print("# =====================================================================")
    print("# CREDENCIAIS DE TESTE (HASHES)")
    print("# =====================================================================")
    print()
    print(f"ADMIN_EMAIL=admin@doamais.org")
    print(f"ADMIN_PASSWORD_HASH={admin_hash}")
    print()
    print(f"ONG_EMAIL=ong@solidaria.org")
    print(f"ONG_PASSWORD_HASH={ong_hash}")
    print()
    print(f"DOADOR_EMAIL=joao@email.com")
    print(f"DOADOR_PASSWORD_HASH={doador_hash}")
    
    # ============================================================
    # VERIFICAR HASHES (TESTE)
    # ============================================================
    print("\n" + "=" * 70)
    print("🔍 VERIFICANDO HASHES (Teste de validação)")
    print("=" * 70)
    
    admin_valido = verificar_senha(admin_senha, admin_hash)
    ong_valido = verificar_senha(ong_senha, ong_hash)
    doador_valido = verificar_senha(doador_senha, doador_hash)
    
    print(f"\n   👑 Admin: {'✅ Válido' if admin_valido else '❌ Inválido'}")
    print(f"   🏢 ONG: {'✅ Válido' if ong_valido else '❌ Inválido'}")
    print(f"   👤 Doador: {'✅ Válido' if doador_valido else '❌ Inválido'}")
    
    # ============================================================
    # RESUMO FINAL
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 RESUMO DAS CREDENCIAIS (guarde com segurança!)")
    print("=" * 70)
    print(f"\n   👑 Admin:   {admin_senha}")
    print(f"   🏢 ONG:     {ong_senha}")
    print(f"   👤 Doador:  {doador_senha}")
    print()
    print("   📌 Emails:")
    print(f"      Admin:  admin@doamais.org")
    print(f"      ONG:    ong@solidaria.org")
    print(f"      Doador: joao@email.com")
    
    print("\n" + "=" * 70)
    print("✅ Script finalizado com sucesso!")
    print("=" * 70)
    
    # ============================================================
    # SALVAR EM ARQUIVO (OPCIONAL)
    # ============================================================
    salvar = input("\n💾 Deseja salvar as credenciais em um arquivo? (s/N): ").strip().lower()
    if salvar == 's':
        arquivo = "credenciais_hashes.txt"
        with open(arquivo, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("CREDENCIAIS DE TESTE - Doa+ Plataforma\n")
            f.write("=" * 70 + "\n\n")
            f.write("VARIÁVEIS DE AMBIENTE (.env / Render):\n")
            f.write("-" * 40 + "\n")
            f.write(f"ADMIN_EMAIL=admin@doamais.org\n")
            f.write(f"ADMIN_PASSWORD_HASH={admin_hash}\n\n")
            f.write(f"ONG_EMAIL=ong@solidaria.org\n")
            f.write(f"ONG_PASSWORD_HASH={ong_hash}\n\n")
            f.write(f"DOADOR_EMAIL=joao@email.com\n")
            f.write(f"DOADOR_PASSWORD_HASH={doador_hash}\n\n")
            f.write("-" * 40 + "\n")
            f.write("SENHAS ORIGINAIS:\n")
            f.write(f"Admin:  {admin_senha}\n")
            f.write(f"ONG:    {ong_senha}\n")
            f.write(f"Doador: {doador_senha}\n")
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"✅ Arquivo salvo como: {arquivo}")
        print(f"   ⚠️  Mantenha este arquivo em local seguro!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Script interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
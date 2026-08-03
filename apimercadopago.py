"""
apimercadopago.py - Integração com Mercado Pago para Doa+
Plataforma de doações - Doa+
"""

import mercadopago
import json
import time
import os
import secrets
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# =====================================================================
# CONFIGURAÇÕES
# =====================================================================

MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', '')
MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY', '')
MP_STATEMENT_DESCRIPTOR = os.environ.get('MP_STATEMENT_DESCRIPTOR', 'Doa+ Doações')
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
TAXA_SERVICO = float(os.environ.get('TAXA_SERVICO', 3.99))
TAXA_FIXA = float(os.environ.get('TAXA_FIXA', 0.60))

# =====================================================================
# INICIALIZAÇÃO DO SDK
# =====================================================================

if MP_ACCESS_TOKEN:
    try:
        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
        print("✅ Mercado Pago SDK inicializado com sucesso!")
    except Exception as e:
        sdk = None
        print(f"⚠️ Erro ao inicializar Mercado Pago SDK: {e}")
else:
    sdk = None
    print("⚠️ ATENÇÃO: Token do Mercado Pago não configurado!")

# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================

def get_base_url():
    """Obtém a URL base da aplicação"""
    url = (
        os.environ.get('RENDER_EXTERNAL_URL') or
        os.environ.get('BASE_URL') or
        'http://localhost:5000'
    )
    
    if FLASK_ENV == 'production':
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
    
    return url.rstrip('/')

def verificar_ambiente_mercado_pago():
    """Verifica o ambiente baseado no token"""
    if not MP_ACCESS_TOKEN:
        return False, "NÃO CONFIGURADO"
    
    if MP_ACCESS_TOKEN.startswith('APP_USR-'):
        return True, "PRODUÇÃO"
    elif MP_ACCESS_TOKEN.startswith('TEST-'):
        return False, "SANDBOX"
    else:
        return False, "DESCONHECIDO"

def testar_conexao_direta():
    """Testa a conexão com o Mercado Pago"""
    resultado = {
        "token_configurado": False,
        "token_tipo": "NÃO CONFIGURADO",
        "conexao_sdk": False,
        "conexao_api": False,
        "erro": None,
        "ambiente": "NÃO CONFIGURADO"
    }
    
    if not MP_ACCESS_TOKEN:
        resultado["erro"] = "Token do Mercado Pago não configurado"
        return resultado
    
    resultado["token_configurado"] = True
    
    if MP_ACCESS_TOKEN.startswith('APP_USR-'):
        resultado["token_tipo"] = "PRODUÇÃO"
        resultado["ambiente"] = "PRODUÇÃO"
    elif MP_ACCESS_TOKEN.startswith('TEST-'):
        resultado["token_tipo"] = "SANDBOX"
        resultado["ambiente"] = "SANDBOX"
    
    try:
        sdk_test = mercadopago.SDK(MP_ACCESS_TOKEN)
        resultado["conexao_sdk"] = True
        
        result = sdk_test.payment_methods().list_all()
        
        if result and "status" in result:
            resultado["status_code"] = result.get("status")
            if result["status"] == 200:
                resultado["conexao_api"] = True
            else:
                resultado["erro"] = f"Status: {result['status']}"
        else:
            resultado["erro"] = "Resposta inválida da API"
            
    except Exception as e:
        resultado["erro"] = str(e)
    
    return resultado

def calcular_taxas(valor):
    """
    Calcula as taxas de serviço para doações
    Retorna: (taxa, valor_liquido)
    """
    taxa = (valor * TAXA_SERVICO / 100) + TAXA_FIXA
    valor_liquido = valor - taxa
    return round(taxa, 2), round(valor_liquido, 2)

# =====================================================================
# FUNÇÃO PRINCIPAL - CRIAÇÃO DE PREFERÊNCIA PARA DOAÇÃO
# =====================================================================

def criar_preferencia_doacao(
    doador_nome,
    doador_email,
    doador_cpf,
    ong_id,
    ong_nome,
    valor,
    mensagem=None,
    external_reference=None,
    recorrente=False
):
    """
    Cria uma preferência de pagamento para doação no Mercado Pago
    
    Parâmetros:
    - doador_nome: Nome do doador
    - doador_email: Email do doador
    - doador_cpf: CPF do doador
    - ong_id: ID da ONG
    - ong_nome: Nome da ONG
    - valor: Valor da doação
    - mensagem: Mensagem opcional
    - external_reference: Referência externa
    - recorrente: Se é doação recorrente
    
    Retorna:
    - dict com sucesso, url_doacao, id_preferencia, external_reference
    """
    
    is_production, ambiente = verificar_ambiente_mercado_pago()
    
    if not MP_ACCESS_TOKEN:
        return {
            'sucesso': False,
            'error': 'Token do Mercado Pago não configurado',
            'error_code': 'NO_TOKEN'
        }
    
    if not sdk:
        return {
            'sucesso': False,
            'error': 'SDK do Mercado Pago não inicializado',
            'error_code': 'SDK_ERROR'
        }
    
    if valor <= 0:
        return {
            'sucesso': False,
            'error': 'Valor deve ser maior que zero',
            'error_code': 'INVALID_VALUE'
        }
    
    # Calcular taxas
    taxa, valor_liquido = calcular_taxas(valor)
    
    # Gerar external reference
    if not external_reference:
        timestamp = int(time.time())
        random_suffix = secrets.token_hex(4)
        external_reference = f"DOA_{ong_id}_{timestamp}_{random_suffix}"
    
    # Preparar dados do pagador
    nome_completo = doador_nome.strip()
    partes_nome = nome_completo.split(' ')
    primeiro_nome = partes_nome[0] if partes_nome else 'Doador'
    ultimo_nome = partes_nome[-1] if len(partes_nome) > 1 else 'Anônimo'
    
    if not doador_email or '@' not in doador_email:
        doador_email = 'doador@email.com'
    
    cpf_limpo = str(doador_cpf).replace('.', '').replace('-', '').replace(' ', '')
    if len(cpf_limpo) != 11:
        cpf_limpo = '12345678909'
    
    payer = {
        "name": primeiro_nome[:50],
        "surname": ultimo_nome[:50],
        "email": doador_email,
        "identification": {
            "type": "CPF",
            "number": cpf_limpo
        }
    }
    
    # URL base
    url_base = get_base_url()
    
    # Descrição do item
    descricao = f"Doação para {ong_nome}"
    if mensagem:
        descricao += f" - {mensagem[:100]}"
    
    # Itens (apenas 1 item para doação)
    items = [{
        "id": f"doacao_{ong_id}",
        "title": f"Doação para {ong_nome[:50]}",
        "description": descricao[:255],
        "quantity": 1,
        "unit_price": valor,
        "currency_id": "BRL"
    }]
    
    # URLs de retorno
    back_urls = {
        "success": f"{url_base}/doacao/success",
        "failure": f"{url_base}/doacao/failure",
        "pending": f"{url_base}/doacao/pending"
    }
    
    # Montagem do payload
    payment_data = {
        "items": items,
        "payer": payer,
        "back_urls": back_urls,
        "auto_return": "approved",
        "external_reference": external_reference,
        "payment_methods": {
            "excluded_payment_types": [{"id": "atm"}],
            "installments": 12
        },
        "statement_descriptor": MP_STATEMENT_DESCRIPTOR[:22],
        "binary_mode": False,
        "notification_url": f"{url_base}/webhook/mercadopago",
        "metadata": {
            "tipo": "doacao",
            "ong_id": ong_id,
            "ong_nome": ong_nome[:100],
            "doador": doador_nome[:100],
            "doador_email": doador_email,
            "valor_original": valor,
            "taxa_servico": taxa,
            "valor_liquido": valor_liquido,
            "recorrente": recorrente,
            "mensagem": (mensagem or '')[:255],
            "ambiente": ambiente,
            "timestamp": int(time.time())
        }
    }
    
    # Log de debug
    print(f"\n{'='*60}")
    print(f"💰 CRIANDO DOAÇÃO NO MERCADO PAGO")
    print(f"   Ambiente: {ambiente}")
    print(f"   ONG: {ong_nome} (ID: {ong_id})")
    print(f"   Doador: {doador_nome}")
    print(f"   Valor: R$ {valor:.2f}")
    print(f"   Taxa: R$ {taxa:.2f}")
    print(f"   Líquido: R$ {valor_liquido:.2f}")
    print(f"   Recorrente: {'Sim' if recorrente else 'Não'}")
    print(f"   External Reference: {external_reference}")
    print(f"{'='*60}\n")
    
    try:
        result = sdk.preference().create(payment_data)
        
        if result.get('status') == 201:
            response = result.get('response', {})
            preference_id = response.get('id')
            url_doacao = response.get('init_point') or response.get('sandbox_init_point')
            
            print(f"✅ Preferência criada com sucesso!")
            print(f"   ID: {preference_id}")
            print(f"   URL: {url_doacao}")
            
            return {
                'sucesso': True,
                'url_doacao': url_doacao,
                'id_preferencia': preference_id,
                'external_reference': external_reference,
                'valor': valor,
                'taxa_servico': taxa,
                'valor_liquido': valor_liquido,
                'ambiente': ambiente,
                'is_production': is_production
            }
        else:
            error_msg = result.get('response', {}).get('message', 'Erro desconhecido')
            print(f"❌ Erro ao criar preferência: {error_msg}")
            
            return {
                'sucesso': False,
                'error': f"Erro {result.get('status')}: {error_msg}",
                'error_code': f"STATUS_{result.get('status')}",
                'error_details': result.get('response', {})
            }
            
    except Exception as e:
        print(f"❌ Exceção ao criar preferência: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'sucesso': False,
            'error': f"Exceção: {str(e)}",
            'error_code': 'EXCEPTION'
        }


def criar_preferencia_teste(valor=10.00):
    """Função simplificada para teste rápido"""
    return criar_preferencia_doacao(
        doador_nome="Doador Teste",
        doador_email="teste@email.com",
        doador_cpf="12345678909",
        ong_id=1,
        ong_nome="ONG Teste",
        valor=valor
    )


def obter_status_doacao(payment_id):
    """
    Obtém o status de uma doação no Mercado Pago
    """
    if not sdk:
        return {'success': False, 'error': 'SDK não inicializado'}
    
    try:
        result = sdk.payment().get(payment_id)
        
        if result.get('status') == 200:
            payment_data = result.get('response', {})
            return {
                'success': True,
                'status': payment_data.get('status'),
                'status_detail': payment_data.get('status_detail'),
                'external_reference': payment_data.get('external_reference'),
                'payer': payment_data.get('payer', {}),
                'transaction_amount': payment_data.get('transaction_amount'),
                'payment_method_id': payment_data.get('payment_method_id'),
                'date_created': payment_data.get('date_created'),
                'date_approved': payment_data.get('date_approved')
            }
        else:
            return {
                'success': False,
                'error': f"Erro {result.get('status')}: {result.get('response', {}).get('message', 'Erro desconhecido')}"
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def cancelar_doacao(payment_id):
    """
    Cancela uma doação no Mercado Pago
    """
    if not sdk:
        return {'success': False, 'error': 'SDK não inicializado'}
    
    try:
        result = sdk.payment().update(payment_id, {"status": "cancelled"})
        
        if result.get('status') == 200:
            return {'success': True, 'message': 'Doação cancelada com sucesso'}
        else:
            return {
                'success': False,
                'error': f"Erro {result.get('status')}: {result.get('response', {}).get('message', 'Erro desconhecido')}"
            }
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


# =====================================================================
# TESTE RÁPIDO
# =====================================================================

if __name__ == "__main__":
    if not MP_ACCESS_TOKEN:
        print("❌ Token do Mercado Pago não configurado!")
        print("   Configure MP_ACCESS_TOKEN no .env")
        exit(1)
    
    print("🔍 Testando conexão com Mercado Pago...")
    resultado = testar_conexao_direta()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
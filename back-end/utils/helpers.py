# utils/helpers.py
from datetime import datetime, timedelta
import re

def calcular_dias_restantes(data_cadastro, prazo_dias=7):
    """Calcula quantos dias faltam para o prazo"""
    if not data_cadastro:
        return prazo_dias
    
    if isinstance(data_cadastro, str):
        data_cadastro = datetime.fromisoformat(data_cadastro)
    
    data_limite = data_cadastro + timedelta(days=prazo_dias)
    hoje = datetime.now()
    
    if hoje > data_limite:
        return 0
    
    dias = (data_limite - hoje).days
    return max(0, dias)

def formatar_data(data, formato='%d/%m/%Y %H:%M'):
    """Formata uma data para o formato especificado"""
    if not data:
        return ''
    
    if isinstance(data, str):
        data = datetime.fromisoformat(data)
    
    return data.strftime(formato)

def mascara_cnpj(cnpj):
    """Aplica máscara ao CNPJ"""
    if not cnpj:
        return ''
    
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) == 14:
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}'
    return cnpj

def mascara_cpf(cpf):
    """Aplica máscara ao CPF"""
    if not cpf:
        return ''
    
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}'
    return cpf

def mascara_telefone(telefone):
    """Aplica máscara ao telefone"""
    if not telefone:
        return ''
    
    telefone = re.sub(r'[^0-9]', '', telefone)
    if len(telefone) == 10:
        return f'({telefone[:2]}) {telefone[2:6]}-{telefone[6:10]}'
    elif len(telefone) == 11:
        return f'({telefone[:2]}) {telefone[2:7]}-{telefone[7:11]}'
    return telefone

# Lista de bancos brasileiros
BANCOS_BRASIL = {
    '001': 'Banco do Brasil',
    '033': 'Santander',
    '104': 'Caixa Econômica Federal',
    '237': 'Bradesco',
    '341': 'Itaú',
    '389': 'Mercantil do Brasil',
    '399': 'HSBC',
    '422': 'Banco Safra',
    '453': 'Banco Rural',
    '633': 'Banco Rendimento',
    '652': 'Itaú Unibanco',
    '745': 'Banco Citibank',
    '756': 'Banco Cooperativo do Brasil',
}

def enviar_email(destinatario, assunto, mensagem):
    """
    Função simplificada para envio de email
    Em produção, usar biblioteca de email (smtplib, sendgrid, etc.)
    """
    print(f"\n{'='*60}")
    print(f"📧 EMAIL")
    print(f"   Para: {destinatario}")
    print(f"   Assunto: {assunto}")
    print(f"   Mensagem:\n{mensagem}")
    print(f"{'='*60}\n")
    
    # Em produção, implementar envio real
    return True

def is_development():
    """Verifica se está em ambiente de desenvolvimento"""
    import os
    return os.getenv('FLASK_ENV', 'development') == 'development'

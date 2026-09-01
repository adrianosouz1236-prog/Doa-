# utils/validators.py
import re

def validar_email(email):
    """Valida se o email é válido"""
    if not email:
        return False
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

def validar_cnpj(cnpj):
    """Valida se o CNPJ é válido"""
    if not cnpj:
        return False
    
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validação do primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if digito1 != int(cnpj[12]):
        return False
    
    # Validação do segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if digito2 != int(cnpj[13]):
        return False
    
    return True

def validar_cpf(cpf):
    """Valida se o CPF é válido"""
    if not cpf:
        return False
    
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if digito1 != int(cpf[9]):
        return False
    
    # Validação do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if digito2 != int(cpf[10]):
        return False
    
    return True

def validar_telefone(telefone):
    """Valida se o telefone é válido"""
    if not telefone:
        return True  # Telefone é opcional
    
    telefone = re.sub(r'[^0-9]', '', telefone)
    
    # Aceita números com 10 ou 11 dígitos (com ou sem DDD)
    return len(telefone) in [10, 11]

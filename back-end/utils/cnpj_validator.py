# utils/cnpj_validator.py - Validador de CNPJ com API da Receita Federal
import re
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Códigos de natureza jurídica para ONGs/Associações
NATUREZA_ONG = [
    '399-9',  # Associação Privada
    '322-0',  # Organização Social (OS)
    '323-8',  # Organização da Sociedade Civil de Interesse Público (OSCIP)
    '324-6',  # Fundação Privada
    '325-4',  # Entidade Sindical
    '327-0',  # Cooperativa
]

# Códigos de natureza que indicam ONGs
NATUREZA_ONG_DESCRICOES = {
    '399-9': 'Associação Privada',
    '322-0': 'Organização Social (OS)',
    '323-8': 'OSCIP',
    '324-6': 'Fundação Privada',
    '325-4': 'Entidade Sindical',
    '327-0': 'Cooperativa'
}


def validar_cnpj_formato(cnpj):
    """
    Valida o formato e dígitos verificadores do CNPJ (validação local)
    Retorna: (bool, mensagem)
    """
    if not cnpj:
        return False, 'CNPJ é obrigatório'
    
    # Remove caracteres especiais
    cnpj_limpo = re.sub(r'[^0-9]', '', str(cnpj))
    
    if len(cnpj_limpo) != 14:
        return False, 'CNPJ deve ter 14 dígitos'
    
    # Verifica se todos os dígitos são iguais (CNPJ inválido)
    if cnpj_limpo == cnpj_limpo[0] * 14:
        return False, 'CNPJ inválido (todos os dígitos são iguais)'
    
    # Validação dos dígitos verificadores
    # Primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj_limpo[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    digito1 = 11 - (soma % 11)
    if digito1 >= 10:
        digito1 = 0
    
    if digito1 != int(cnpj_limpo[12]):
        return False, 'CNPJ inválido (dígito verificador incorreto)'
    
    # Segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj_limpo[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    digito2 = 11 - (soma % 11)
    if digito2 >= 10:
        digito2 = 0
    
    if digito2 != int(cnpj_limpo[13]):
        return False, 'CNPJ inválido (dígito verificador incorreto)'
    
    return True, 'CNPJ válido'


def consultar_cnpj_receita(cnpj):
    """
    Consulta CNPJ na API da Receita Federal (Brasil API)
    Retorna: dict com dados do CNPJ ou erro
    """
    cnpj_limpo = re.sub(r'[^0-9]', '', str(cnpj))
    
    if len(cnpj_limpo) != 14:
        return {
            'success': False,
            'error': 'CNPJ deve ter 14 dígitos'
        }
    
    try:
        # Consulta Brasil API (gratuita)
        response = requests.get(
            f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}',
            timeout=15,
            headers={
                'User-Agent': 'Doa+ Plataforma (contato@doamais.org)'
            }
        )
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verifica se o CNPJ está ativo
            situacao = dados.get('situacao_cadastral', '').upper()
            if situacao != 'ATIVA':
                return {
                    'success': False,
                    'error': f'CNPJ com situação: {situacao}. Apenas CNPJs ativos são permitidos.',
                    'situacao': situacao,
                    'dados': dados
                }
            
            # Verifica se é uma ONG
            natureza = dados.get('natureza_juridica', {}).get('codigo', '')
            natureza_descricao = dados.get('natureza_juridica', {}).get('descricao', '')
            
            if natureza not in NATUREZA_ONG:
                return {
                    'success': False,
                    'error': f'CNPJ não pertence a uma ONG/Associação. Natureza: {natureza_descricao}',
                    'natureza': natureza,
                    'natureza_descricao': natureza_descricao,
                    'dados': dados
                }
            
            # Retorna os dados completos
            return {
                'success': True,
                'dados': dados,
                'cnpj': cnpj_limpo,
                'nome': dados.get('nome', ''),
                'razao_social': dados.get('razao_social', ''),
                'cidade': dados.get('cidade', ''),
                'uf': dados.get('uf', ''),
                'cep': dados.get('cep', ''),
                'logradouro': dados.get('logradouro', ''),
                'numero': dados.get('numero', ''),
                'bairro': dados.get('bairro', ''),
                'telefone': dados.get('ddd_telefone_1', ''),
                'email': dados.get('email', ''),
                'situacao': situacao,
                'natureza_codigo': natureza,
                'natureza_descricao': natureza_descricao,
                'data_abertura': dados.get('data_inicio_atividade', '')
            }
            
        elif response.status_code == 404:
            return {
                'success': False,
                'error': 'CNPJ não encontrado na Receita Federal'
            }
        elif response.status_code == 429:
            return {
                'success': False,
                'error': 'Limite de consultas excedido. Aguarde alguns segundos e tente novamente.'
            }
        else:
            return {
                'success': False,
                'error': f'Erro na consulta: Status {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Tempo limite excedido. Tente novamente.'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Erro de conexão: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro inesperado: {str(e)}'
        }


def validar_cnpj_completo(cnpj, exigir_ong=True):
    """
    Valida CNPJ completo (formato + consulta Receita)
    Retorna: dict com resultado
    """
    # Primeiro: validação local
    formato_valido, msg = validar_cnpj_formato(cnpj)
    if not formato_valido:
        return {
            'valido': False,
            'error': msg
        }
    
    # Segundo: consulta na Receita Federal
    resultado = consultar_cnpj_receita(cnpj)
    
    if not resultado['success']:
        return {
            'valido': False,
            'error': resultado['error']
        }
    
    # Se exigir que seja uma ONG
    if exigir_ong:
        natureza = resultado.get('natureza_codigo', '')
        if natureza not in NATUREZA_ONG:
            return {
                'valido': False,
                'error': f'CNPJ não é de uma ONG/Associação. Natureza: {resultado.get("natureza_descricao", "Desconhecida")}'
            }
    
    return {
        'valido': True,
        'dados': resultado['dados'],
        'cnpj': resultado['cnpj'],
        'nome': resultado['nome'],
        'cidade': resultado['cidade'],
        'uf': resultado['uf'],
        'telefone': resultado.get('telefone', '')
    }


def formatar_cnpj(cnpj):
    """Formata CNPJ no padrão 00.000.000/0001-00"""
    cnpj_limpo = re.sub(r'[^0-9]', '', str(cnpj))
    if len(cnpj_limpo) == 14:
        return f'{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}'
    return cnpj
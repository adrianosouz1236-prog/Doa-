# blueprints/ajuda.py - Central de Ajuda
from flask import Blueprint, request, jsonify
import logging

ajuda_bp = Blueprint('ajuda', __name__)
logger = logging.getLogger(__name__)

# Artigos da central de ajuda
ARTIGOS = [
    {
        'id': 1,
        'titulo': 'Como funciona a plataforma Doa+?',
        'categoria': 'geral',
        'conteudo': 'A Doa+ é uma plataforma que conecta doadores a ONGs. Você pode doar itens, fazer doações financeiras ou se voluntariar para ajudar causas sociais.'
    },
    {
        'id': 2,
        'titulo': 'Como faço uma doação?',
        'categoria': 'doador',
        'conteudo': 'Para fazer uma doação: 1) Faça login na plataforma. 2) Encontre uma necessidade ou ONG. 3) Clique em "Quero Doar". 4) Escolha a quantidade e confirme.'
    },
    {
        'id': 3,
        'titulo': 'Como minha ONG pode se cadastrar?',
        'categoria': 'ong',
        'conteudo': 'Para cadastrar sua ONG: 1) Acesse a página de cadastro. 2) Escolha "Sou uma ONG". 3) Preencha todos os dados. 4) Aguarde a verificação do administrador.'
    },
    {
        'id': 4,
        'titulo': 'Como funciona a verificação de ONGs?',
        'categoria': 'ong',
        'conteudo': 'Após o cadastro, sua ONG passa por um processo de verificação que pode levar até 7 dias úteis. Você receberá um email quando for verificada.'
    },
    {
        'id': 5,
        'titulo': 'Esqueci minha senha, o que fazer?',
        'categoria': 'suporte',
        'conteudo': 'Clique em "Esqueceu a senha?" na tela de login. Digite seu email e você receberá um código de recuperação para criar uma nova senha.'
    },
    {
        'id': 6,
        'titulo': 'Como faço para enviar feedback?',
        'categoria': 'feedback',
        'conteudo': 'Acesse a página de Feedback e preencha o formulário com sua opinião. Você pode enviar de forma anônima se preferir.'
    },
    {
        'id': 7,
        'titulo': 'A Doa+ é segura?',
        'categoria': 'seguranca',
        'conteudo': 'Sim! A Doa+ utiliza criptografia SSL, hashing de senhas com bcrypt, proteção contra CSRF e rate limiting para garantir a segurança dos seus dados.'
    },
    {
        'id': 8,
        'titulo': 'Quais tipos de doação posso fazer?',
        'categoria': 'doador',
        'conteudo': 'Você pode fazer doações de itens (alimentos, roupas, medicamentos, etc.) e doações financeiras via Mercado Pago (cartão de crédito, PIX ou boleto).'
    },
    {
        'id': 9,
        'titulo': 'Como funciona o sistema de pontuação?',
        'categoria': 'doador',
        'conteudo': 'Você ganha pontos a cada doação realizada. Com os pontos, você desbloqueia conquistas e pode ver seu ranking entre os doadores.'
    },
    {
        'id': 10,
        'titulo': 'Posso cancelar uma doação?',
        'categoria': 'suporte',
        'conteudo': 'Doações de itens podem ser canceladas antes da confirmação pela ONG. Doações financeiras só podem ser canceladas antes da confirmação do pagamento.'
    }
]

@ajuda_bp.route('', methods=['GET'])
@ajuda_bp.route('/', methods=['GET'])
def listar_artigos():
    """Lista todos os artigos da central de ajuda"""
    try:
        categoria = request.args.get('categoria')
        
        if categoria and categoria != 'todos':
            artigos = [a for a in ARTIGOS if a.get('categoria') == categoria]
        else:
            artigos = ARTIGOS
        
        return jsonify({'artigos': artigos}), 200
    except Exception as e:
        logger.error(f"Erro ao listar artigos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ajuda_bp.route('/<int:artigo_id>', methods=['GET'])
def obter_artigo(artigo_id):
    """Obtém um artigo específico"""
    try:
        artigo = next((a for a in ARTIGOS if a.get('id') == artigo_id), None)
        if not artigo:
            return jsonify({'error': 'Artigo não encontrado'}), 404
        return jsonify(artigo), 200
    except Exception as e:
        logger.error(f"Erro ao obter artigo: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

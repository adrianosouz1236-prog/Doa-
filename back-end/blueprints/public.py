# blueprints/public.py - ROTAS PÚBLICAS (SEM DADOS FALSOS EM PRODUÇÃO)
from flask import Blueprint, request, jsonify
from database.repositories import (
    ongs_db,
    doadores_db,
    necessidades_db,
    doacoes_db,
    doacoes_financeiras_db,
    ong_eventos_db,
    voluntariado_db,
    OngRepository,
    NecessidadeRepository
)
import logging
import os

public_bp = Blueprint('public', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


@public_bp.route('/ongs', methods=['GET'])
def listar_ongs_publicas():
    """Lista ONGs - APENAS as reais (ignora ONG de teste)"""
    try:
        cidade = request.args.get('cidade', '').lower()
        ongs_lista = []
        
        for ong_id, ong in ongs_db.items():
            # IGNORA a ONG de teste (ID = 1) em produção
            if os.getenv('FLASK_ENV') == 'production' and ong_id == 1:
                continue
            
            if ong.get('status') != 'verificado':
                continue
            if cidade and cidade not in ong.get('cidade', '').lower():
                continue
            
            ongs_lista.append({
                'id': ong_id,
                'nome': ong.get('nome'),
                'cidade': ong.get('cidade'),
                'uf': ong.get('uf'),
                'descricao': ong.get('descricao'),
                'logo_url': ong.get('logo_url'),
                'latitude': ong.get('latitude'),
                'longitude': ong.get('longitude'),
                'media_avaliacao': ong.get('media_avaliacao', 0),
                'total_avaliacoes': ong.get('total_avaliacoes', 0)
            })
        
        return jsonify({'ongs': ongs_lista}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar ONGs públicas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/necessidades', methods=['GET'])
def listar_necessidades_publicas():
    """Lista necessidades - APENAS as reais (ignora dados de teste)"""
    try:
        # Em produção, retorna lista vazia se não houver dados reais
        if os.getenv('FLASK_ENV') == 'production' and len(necessidades_db) <= 1:
            return jsonify({
                'necessidades': [],
                'total': 0,
                'page': 1,
                'limit': 10,
                'has_more': False
            }), 200
        
        params = request.args
        cidade = params.get('cidade', '').lower()
        categoria = params.get('categoria', '')
        page = int(params.get('page', 1))
        limit = int(params.get('limit', 10))
        urgent = params.get('urgente', 'false').lower() == 'true'
        busca = params.get('busca', '').lower()
        
        necessidades_lista = []
        for nec_id, nec in necessidades_db.items():
            # IGNORA a necessidade de teste (ID = 1) em produção
            if os.getenv('FLASK_ENV') == 'production' and nec_id == 1:
                continue
            
            if nec.get('status') != 'aberta':
                continue
            ong = OngRepository.buscar_por_id(nec.get('ong_id'))
            if not ong or ong.get('status') != 'verificado':
                continue
            if cidade and cidade not in ong.get('cidade', '').lower():
                continue
            if categoria and nec.get('categoria') != categoria:
                continue
            if urgent and nec.get('urgencia') != 'alta':
                continue
            if busca and busca not in nec.get('titulo', '').lower() and busca not in nec.get('descricao', '').lower():
                continue
            
            necessidades_lista.append({
                'id': nec_id,
                'ong_id': nec.get('ong_id'),
                'ong_nome': ong.get('nome'),
                'cidade': ong.get('cidade'),
                'titulo': nec.get('titulo'),
                'descricao': nec.get('descricao'),
                'categoria': nec.get('categoria'),
                'quantidade_necessaria': nec.get('quantidade_necessaria'),
                'quantidade_recebida': nec.get('quantidade_recebida', 0),
                'urgencia': nec.get('urgencia'),
                'status': nec.get('status'),
                'data_criacao': nec.get('data_criacao'),
                'media_avaliacao_ong': ong.get('media_avaliacao', 0)
            })
        
        start = (page - 1) * limit
        end = start + limit
        paginated = necessidades_lista[start:end]
        
        return jsonify({
            'necessidades': paginated,
            'total': len(necessidades_lista),
            'page': page,
            'limit': limit,
            'has_more': end < len(necessidades_lista)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar necessidades públicas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/eventos', methods=['GET'])
def listar_eventos_publicos():
    """Lista eventos - APENAS os reais (ignora dados de teste)"""
    try:
        if os.getenv('FLASK_ENV') == 'production' and len(ong_eventos_db) <= 1:
            return jsonify({'eventos': []}), 200
        
        eventos = []
        for ev_id, ev in ong_eventos_db.items():
            # IGNORA o evento de teste (ID = 1) em produção
            if os.getenv('FLASK_ENV') == 'production' and ev_id == 1:
                continue
            
            if ev.get('status') == 'ativo':
                ong = OngRepository.buscar_por_id(ev.get('ong_id'))
                if ong and ong.get('status') == 'verificado':
                    eventos.append({
                        'id': ev.get('id'),
                        'ong_id': ev.get('ong_id'),
                        'ong_nome': ong.get('nome'),
                        'titulo': ev.get('titulo'),
                        'descricao': ev.get('descricao'),
                        'data_evento': ev.get('data_evento'),
                        'local_evento': ev.get('local_evento'),
                        'cidade': ev.get('cidade'),
                        'uf': ev.get('uf'),
                        'imagem_url': ev.get('imagem_url')
                    })
        eventos.sort(key=lambda x: x.get('data_evento', ''))
        return jsonify({'eventos': eventos}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar eventos públicos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/ranking/doadores', methods=['GET'])
def ranking_doadores_publico():
    """Lista ranking - APENAS doadores reais"""
    try:
        if os.getenv('FLASK_ENV') == 'production' and len(doadores_db) <= 1:
            return jsonify({'ranking': []}), 200
        
        limit = int(request.args.get('limit', 5))
        doadores_ativos = [d for d in doadores_db.values() if d.get('status') == 'ativo']
        
        # IGNORA o doador de teste (ID = 1) em produção
        if os.getenv('FLASK_ENV') == 'production':
            doadores_ativos = [d for d in doadores_ativos if d.get('id') != 1]
        
        doadores_ordenados = sorted(doadores_ativos, key=lambda x: x.get('pontuacao', 0), reverse=True)
        
        ranking = []
        for i, doador in enumerate(doadores_ordenados[:limit], 1):
            ranking.append({
                'posicao': i,
                'id': doador.get('id'),
                'nome': doador.get('nome'),
                'total_doacoes': doador.get('total_doacoes', 0),
                'pontuacao': doador.get('pontuacao', 0),
                'conquistas': doador.get('conquistas', [])
            })
        
        return jsonify({'ranking': ranking}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar ranking público: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/voluntariado/vagas', methods=['GET'])
def listar_vagas_publicas():
    """Lista vagas - APENAS as reais"""
    try:
        if os.getenv('FLASK_ENV') == 'production' and len(voluntariado_db) <= 1:
            return jsonify({'vagas': []}), 200
        
        vagas = []
        for v_id, v in voluntariado_db.items():
            # IGNORA a vaga de teste (ID = 1) em produção
            if os.getenv('FLASK_ENV') == 'production' and v_id == 1:
                continue
            
            if v.get('status') != 'aberta':
                continue
            ong = OngRepository.buscar_por_id(v.get('ong_id'))
            if not ong or ong.get('status') != 'verificado':
                continue
            vagas.append({
                'id': v.get('id'),
                'ong_id': v.get('ong_id'),
                'ong_nome': v.get('ong_nome'),
                'titulo': v.get('titulo'),
                'descricao': v.get('descricao'),
                'data_evento': v.get('data_evento'),
                'local': v.get('local'),
                'vagas_disponiveis': v.get('vagas_disponiveis'),
                'vagas_preenchidas': v.get('vagas_preenchidas', 0)
            })
        
        return jsonify({'vagas': vagas}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar vagas públicas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@public_bp.route('/dashboard/stats', methods=['GET'])
def dashboard_stats_publico():
    """Estatísticas - APENAS dados reais"""
    try:
        # Em produção, retorna zeros se não houver dados reais
        if os.getenv('FLASK_ENV') == 'production':
            total_ongs = len([o for o in ongs_db.values() if o.get('status') == 'verificado' and o.get('id') != 1])
            total_doadores = len([d for d in doadores_db.values() if d.get('status') == 'ativo' and d.get('id') != 1])
            total_doacoes = len([d for d in doacoes_db.values() if d.get('id') != 1])
            total_itens = sum(d.get('quantidade', 0) for d in doacoes_db.values() if d.get('id') != 1)
            total_voluntarios = sum(v.get('vagas_preenchidas', 0) for v in voluntariado_db.values() if v.get('id') != 1)
            total_doacoes_financeiras = len([d for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado' and d.get('id') != 1])
            total_valor_financeiro = sum(d.get('valor', 0) for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado' and d.get('id') != 1)
        else:
            total_ongs = len([o for o in ongs_db.values() if o.get('status') == 'verificado'])
            total_doadores = len([d for d in doadores_db.values() if d.get('status') == 'ativo'])
            total_doacoes = len(doacoes_db)
            total_itens = sum(d.get('quantidade', 0) for d in doacoes_db.values())
            total_voluntarios = sum(v.get('vagas_preenchidas', 0) for v in voluntariado_db.values())
            total_doacoes_financeiras = len([d for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado'])
            total_valor_financeiro = sum(d.get('valor', 0) for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado')
        
        return jsonify({
            'total_ongs': total_ongs,
            'total_doadores': total_doadores,
            'total_doacoes': total_doacoes,
            'total_itens': total_itens,
            'total_voluntarios': total_voluntarios,
            'total_doacoes_financeiras': total_doacoes_financeiras,
            'total_valor_financeiro': total_valor_financeiro
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar stats públicos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
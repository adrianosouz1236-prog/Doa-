# blueprints/ong.py - CORRIGIDO
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required, ong_required, ong_verificada_required
from services.doacao_service import DoacaoService
from services.audit_service import AuditService
from security import sanitizar_string, sanitizar_html, criptografar, descriptografar
from database.repositories import (
    OngRepository, 
    NecessidadeRepository, 
    DoacaoRepository, 
    CarteiraRepository, 
    DoacaoFinanceiraRepository,
    ong_eventos_db,
    ong_parcerias_db,
    ong_fotos_db
)
from utils.helpers import calcular_dias_restantes, enviar_email
import logging
from datetime import datetime

ong_bp = Blueprint('ong', __name__, url_prefix='/api/ongs')
logger = logging.getLogger(__name__)

# Variáveis globais para IDs
next_evento_id = 1
next_parceria_id = 1
next_foto_id = 1


@ong_bp.route('/dashboard', methods=['GET'])
@token_required
@ong_required
def dashboard():
    try:
        ong = OngRepository.buscar_por_id(g.user_id)
        
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        status = ong.get('status', 'pendente_verificacao')
        verificada = status == 'verificado'
        
        dias_restantes = None
        if status == 'pendente_verificacao':
            dias_restantes = calcular_dias_restantes(ong.get('data_cadastro'), 7)
        
        total_necessidades = 0
        total_doacoes = 0
        total_itens = 0
        total_doadores = 0
        total_eventos = 0
        total_doacoes_financeiras = 0
        saldo_carteira = 0
        
        if verificada:
            total_necessidades = len(NecessidadeRepository.buscar_por_ong(g.user_id))
            doacoes = DoacaoRepository.listar_por_ong(g.user_id)
            total_doacoes = len(doacoes)
            total_itens = sum(d.get('quantidade', 0) for d in doacoes)
            total_doadores = len(set(d.get('doador_id') for d in doacoes))
            
            # Eventos
            total_eventos = len([e for e in ong_eventos_db.values() if e.get('ong_id') == g.user_id])
            
            # Doações financeiras
            doacoes_fin = DoacaoFinanceiraRepository.listar_por_ong(g.user_id)
            total_doacoes_financeiras = len([d for d in doacoes_fin if d.get('status') == 'confirmado'])
            
            # Carteira
            carteira = CarteiraRepository.buscar_por_ong(g.user_id)
            saldo_carteira = carteira.get('saldo', 0) if carteira else 0
        
        return jsonify({
            'total_necessidades': total_necessidades,
            'total_doacoes': total_doacoes,
            'total_itens': total_itens,
            'total_doadores': total_doadores,
            'total_eventos': total_eventos,
            'total_doacoes_financeiras': total_doacoes_financeiras,
            'saldo_carteira': saldo_carteira,
            'status_verificacao': status,
            'verificada': verificada,
            'dias_restantes': dias_restantes,
            'codigo_verificacao': ong.get('codigo_verificacao') if not verificada else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no dashboard da ONG: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/perfil', methods=['GET'])
@token_required
@ong_required
def obter_perfil():
    try:
        ong = OngRepository.buscar_por_id(g.user_id)
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        # Descriptografar dados bancários
        if ong.get('conta_bancaria_criptografada'):
            dados_bancarios = descriptografar(ong.get('conta_bancaria_criptografada'))
            if dados_bancarios:
                partes = dados_bancarios.split('|')
                if len(partes) >= 3:
                    ong['banco'] = partes[0]
                    ong['agencia'] = partes[1]
                    ong['conta'] = partes[2]
                    ong['tipo_conta'] = partes[3] if len(partes) > 3 else 'corrente'
        
        return jsonify(ong), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter perfil: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/perfil', methods=['PUT'])
@token_required
@ong_required
def atualizar_perfil():
    try:
        dados = request.get_json()
        ong = OngRepository.buscar_por_id(g.user_id)
        
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        campos_permitidos = ['nome', 'email', 'telefone', 'endereco', 'cidade', 'uf', 'descricao', 'logo_url']
        dados_atualizados = {}
        
        for campo in campos_permitidos:
            if campo in dados:
                dados_atualizados[campo] = sanitizar_string(dados[campo])
        
        if dados.get('banco') and dados.get('agencia') and dados.get('conta'):
            dados_bancarios = f"{dados['banco']}|{dados['agencia']}|{dados['conta']}|{dados.get('tipo_conta', 'corrente')}"
            dados_atualizados['conta_bancaria_criptografada'] = criptografar(dados_bancarios)
        
        OngRepository.atualizar(g.user_id, dados_atualizados)
        
        return jsonify({'message': 'Perfil atualizado com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar perfil: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/necessidades', methods=['GET'])
@token_required
@ong_required
def listar_necessidades():
    try:
        necessidades = NecessidadeRepository.buscar_por_ong(g.user_id)
        return jsonify({'necessidades': necessidades}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar necessidades: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/necessidades', methods=['POST'])
@token_required
@ong_required
@ong_verificada_required
def criar_necessidade():
    try:
        dados = request.get_json()
        
        if not dados.get('titulo') or not dados.get('categoria') or not dados.get('quantidade_necessaria'):
            return jsonify({'error': 'Título, categoria e quantidade são obrigatórios'}), 400
        
        if dados['quantidade_necessaria'] <= 0:
            return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
        
        necessidade_data = {
            'ong_id': g.user_id,
            'titulo': sanitizar_string(dados['titulo']),
            'descricao': sanitizar_html(dados.get('descricao', '')),
            'categoria': sanitizar_string(dados['categoria']),
            'quantidade_necessaria': dados['quantidade_necessaria'],
            'urgencia': dados.get('urgencia', 'media')
        }
        
        necessidade_id = NecessidadeRepository.criar(necessidade_data)
        
        return jsonify({
            'message': 'Necessidade criada com sucesso!',
            'necessidade_id': necessidade_id
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar necessidade: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/necessidades/<int:necessidade_id>', methods=['PUT'])
@token_required
@ong_required
@ong_verificada_required
def atualizar_necessidade(necessidade_id):
    try:
        dados = request.get_json()
        necessidade = NecessidadeRepository.buscar_por_id(necessidade_id)
        
        if not necessidade:
            return jsonify({'error': 'Necessidade não encontrada'}), 404
        
        if necessidade.get('ong_id') != g.user_id:
            return jsonify({'error': 'Sem permissão'}), 403
        
        dados_atualizados = {}
        for campo in ['titulo', 'descricao', 'categoria', 'urgencia']:
            if campo in dados:
                dados_atualizados[campo] = sanitizar_string(dados[campo]) if campo != 'descricao' else sanitizar_html(dados[campo])
        
        if dados.get('quantidade_necessaria'):
            dados_atualizados['quantidade_necessaria'] = dados['quantidade_necessaria']
        
        NecessidadeRepository.atualizar(necessidade_id, dados_atualizados)
        
        return jsonify({'message': 'Necessidade atualizada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar necessidade: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/necessidades/<int:necessidade_id>/encerrar', methods=['PUT'])
@token_required
@ong_required
@ong_verificada_required
def encerrar_necessidade(necessidade_id):
    try:
        necessidade = NecessidadeRepository.buscar_por_id(necessidade_id)
        
        if not necessidade:
            return jsonify({'error': 'Necessidade não encontrada'}), 404
        
        if necessidade.get('ong_id') != g.user_id:
            return jsonify({'error': 'Sem permissão'}), 403
        
        NecessidadeRepository.atualizar_status(necessidade_id, 'encerrada')
        
        return jsonify({'message': 'Necessidade encerrada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao encerrar necessidade: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/doacoes', methods=['GET'])
@token_required
@ong_required
def listar_doacoes():
    try:
        doacoes = DoacaoRepository.listar_por_ong(g.user_id)
        return jsonify({'doacoes': doacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/doacoes/<int:doacao_id>/confirmar', methods=['PUT'])
@token_required
@ong_required
@ong_verificada_required
def confirmar_doacao_ong(doacao_id):
    try:
        doacao_service = DoacaoService()
        resultado = doacao_service.confirmar_doacao(doacao_id, g.user_id)
        
        if resultado['success']:
            return jsonify({'message': 'Doação confirmada com sucesso!'}), 200
        else:
            return jsonify({'error': resultado['error']}), 400
            
    except Exception as e:
        logger.error(f"Erro ao confirmar doação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/eventos', methods=['GET'])
@token_required
@ong_required
def listar_eventos():
    try:
        eventos = [e for e in ong_eventos_db.values() if e.get('ong_id') == g.user_id]
        return jsonify({'eventos': eventos}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/eventos', methods=['POST'])
@token_required
@ong_required
def criar_evento():
    global next_evento_id
    
    try:
        dados = request.get_json()
        
        if not dados.get('titulo') or not dados.get('data_evento'):
            return jsonify({'error': 'Título e data do evento são obrigatórios'}), 400
        
        evento = {
            'id': next_evento_id,
            'ong_id': g.user_id,
            'titulo': sanitizar_string(dados['titulo']),
            'descricao': sanitizar_html(dados.get('descricao', '')),
            'data_evento': dados['data_evento'],
            'local_evento': sanitizar_string(dados.get('local_evento', '')),
            'endereco': sanitizar_string(dados.get('endereco', '')),
            'cidade': sanitizar_string(dados.get('cidade', '')),
            'uf': sanitizar_string(dados.get('uf', '')),
            'imagem_url': dados.get('imagem_url', ''),
            'status': 'ativo',
            'data_criacao': datetime.now().isoformat()
        }
        ong_eventos_db[next_evento_id] = evento
        next_evento_id += 1
        
        return jsonify({'message': 'Evento criado com sucesso!', 'evento_id': evento['id']}), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/eventos/<int:evento_id>/cancelar', methods=['PUT'])
@token_required
@ong_required
def cancelar_evento(evento_id):
    try:
        evento = ong_eventos_db.get(evento_id)
        
        if not evento:
            return jsonify({'error': 'Evento não encontrado'}), 404
        
        if evento.get('ong_id') != g.user_id:
            return jsonify({'error': 'Sem permissão'}), 403
        
        evento['status'] = 'cancelado'
        
        return jsonify({'message': 'Evento cancelado com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao cancelar evento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/parcerias', methods=['GET'])
@token_required
@ong_required
def listar_parcerias():
    try:
        parcerias = [p for p in ong_parcerias_db.values() if p.get('ong_id') == g.user_id]
        return jsonify({'parcerias': parcerias}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar parcerias: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/parcerias', methods=['POST'])
@token_required
@ong_required
def criar_parceria():
    global next_parceria_id
    
    try:
        dados = request.get_json()
        
        if not dados.get('parceiro_nome'):
            return jsonify({'error': 'Nome do parceiro é obrigatório'}), 400
        
        parceria = {
            'id': next_parceria_id,
            'ong_id': g.user_id,
            'parceiro_nome': sanitizar_string(dados['parceiro_nome']),
            'tipo_parceria': sanitizar_string(dados.get('tipo_parceria', 'empresa')),
            'descricao': sanitizar_html(dados.get('descricao', '')),
            'logo_url': dados.get('logo_url', ''),
            'website_url': dados.get('website_url', ''),
            'status': 'ativa',
            'data_cadastro': datetime.now().isoformat()
        }
        ong_parcerias_db[next_parceria_id] = parceria
        next_parceria_id += 1
        
        return jsonify({'message': 'Parceria criada com sucesso!', 'parceria_id': parceria['id']}), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar parceria: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/parcerias/<int:parceria_id>/encerrar', methods=['PUT'])
@token_required
@ong_required
def encerrar_parceria(parceria_id):
    try:
        parceria = ong_parcerias_db.get(parceria_id)
        
        if not parceria:
            return jsonify({'error': 'Parceria não encontrada'}), 404
        
        if parceria.get('ong_id') != g.user_id:
            return jsonify({'error': 'Sem permissão'}), 403
        
        parceria['status'] = 'encerrada'
        
        return jsonify({'message': 'Parceria encerrada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao encerrar parceria: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/fotos', methods=['GET'])
@token_required
@ong_required
def listar_fotos():
    try:
        fotos = [f for f in ong_fotos_db.values() if f.get('ong_id') == g.user_id]
        return jsonify({'fotos': fotos}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar fotos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/fotos', methods=['POST'])
@token_required
@ong_required
def adicionar_foto():
    global next_foto_id
    
    try:
        dados = request.json
        
        if not dados.get('foto_url'):
            return jsonify({'error': 'URL da foto é obrigatória'}), 400
        
        fotos_ong = [f for f in ong_fotos_db.values() if f.get('ong_id') == g.user_id]
        if len(fotos_ong) >= 3:
            return jsonify({'error': 'Máximo de 3 fotos por ONG'}), 400
        
        foto = {
            'id': next_foto_id,
            'ong_id': g.user_id,
            'foto_url': dados['foto_url'],
            'descricao': sanitizar_string(dados.get('descricao', '')),
            'data_upload': datetime.now().isoformat()
        }
        ong_fotos_db[next_foto_id] = foto
        next_foto_id += 1
        
        return jsonify({'message': 'Foto adicionada com sucesso!', 'foto_id': foto['id']}), 201
        
    except Exception as e:
        logger.error(f"Erro ao adicionar foto: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/fotos/<int:foto_id>', methods=['DELETE'])
@token_required
@ong_required
def remover_foto(foto_id):
    try:
        foto = ong_fotos_db.get(foto_id)
        
        if not foto:
            return jsonify({'error': 'Foto não encontrada'}), 404
        
        if foto.get('ong_id') != g.user_id:
            return jsonify({'error': 'Sem permissão'}), 403
        
        del ong_fotos_db[foto_id]
        
        return jsonify({'message': 'Foto removida com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao remover foto: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@ong_bp.route('/localizacao', methods=['PUT'])
@token_required
@ong_required
def atualizar_localizacao():
    try:
        dados = request.json
        
        if not dados.get('endereco') or not dados.get('latitude') or not dados.get('longitude'):
            return jsonify({'error': 'Endereço, latitude e longitude são obrigatórios'}), 400
        
        OngRepository.atualizar(g.user_id, {
            'endereco_completo': sanitizar_string(dados['endereco']),
            'latitude': dados['latitude'],
            'longitude': dados['longitude']
        })
        
        return jsonify({'message': 'Localização atualizada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar localização: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
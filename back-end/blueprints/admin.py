# blueprints/admin.py - COMPLETO COM TODAS AS FUNCIONALIDADES
from flask import Blueprint, request, jsonify, g
from middleware.auth_middleware import token_required, admin_required
from middleware.rate_limiter import limiter
from services.auth_service import AuthService
from services.audit_service import AuditService
from database.repositories import (
    OngRepository, 
    DoadorRepository, 
    NecessidadeRepository, 
    DoacaoRepository, 
    DoacaoFinanceiraRepository, 
    CarteiraRepository,
    AuditRepository,
    ongs_db,
    doadores_db,
    necessidades_db,
    doacoes_db,
    doacoes_financeiras_db,
    carteiras_db,
    logs_db,
    advertencias_db,
    feedback_db,
    suporte_db,
    comunicacoes_db,
    solicitacoes_exclusao_db,
    ong_eventos_db,
    ong_parcerias_db,
    ong_fotos_db,
    voluntariado_db,
    avaliacoes_db
)
from security import sanitizar_string, sanitizar_html, criptografar, descriptografar
from utils.helpers import calcular_dias_restantes, enviar_email
import logging
import secrets
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

# Variáveis para IDs
next_advertencia_id = 1
next_comunicacao_id = 1

# Carteira da plataforma
carteira_plataforma = {
    'saldo': 0,
    'total_taxas': 0,
    'total_sacado': 0,
    'extrato': [],
    'data_atualizacao': datetime.now()
}


# =====================================================================
# DASHBOARD ADMIN
# =====================================================================

@admin_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def dashboard():
    try:
        total_ongs = len(OngRepository.listar_todos())
        total_doadores = len(DoadorRepository.listar_todos())
        total_anuncios = len([n for n in necessidades_db.values() if n.get('status') == 'aberta'])
        total_advertencias = len(advertencias_db)
        total_doacoes = len(doacoes_db)
        total_doacoes_financeiras = len([d for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado'])
        total_valor_financeiro = sum(d.get('valor', 0) for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado')
        total_comunicacoes = len(comunicacoes_db)
        ongs_bloqueadas = len([o for o in ongs_db.values() if o.get('status') == 'bloqueado'])
        solicitacoes_exclusao = len([s for s in solicitacoes_exclusao_db.values() if s.get('status') == 'pendente'])
        
        logs_recentes = sorted(logs_db.values(), key=lambda x: x.get('data_evento', ''), reverse=True)[:10]
        
        return jsonify({
            'total_ongs': total_ongs,
            'total_doadores': total_doadores,
            'total_anuncios': total_anuncios,
            'total_advertencias': total_advertencias,
            'total_doacoes': total_doacoes,
            'total_doacoes_financeiras': total_doacoes_financeiras,
            'total_valor_financeiro': total_valor_financeiro,
            'total_comunicacoes': total_comunicacoes,
            'ongs_bloqueadas': ongs_bloqueadas,
            'solicitacoes_exclusao_pendentes': solicitacoes_exclusao,
            'logs_recentes': [{
                'data': l.get('data_evento', ''),
                'evento': l.get('evento', ''),
                'usuario': str(l.get('usuario_id', '')),
                'ip': l.get('ip', '')
            } for l in logs_recentes]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no dashboard admin: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# CARTEIRA DA PLATAFORMA
# =====================================================================

@admin_bp.route('/carteira', methods=['GET'])
@token_required
@admin_required
def carteira_plataforma_admin():
    try:
        return jsonify({
            'saldo': carteira_plataforma['saldo'],
            'total_taxas': carteira_plataforma['total_taxas'],
            'total_sacado': carteira_plataforma['total_sacado'],
            'extrato': carteira_plataforma['extrato'][-50:],
            'data_atualizacao': carteira_plataforma['data_atualizacao'].isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Erro ao buscar carteira: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/carteira/sacar', methods=['POST'])
@token_required
@admin_required
def sacar_carteira_plataforma():
    try:
        data = request.json
        valor = data.get('valor')
        conta_bancaria = sanitizar_string(data.get('conta_bancaria', ''))
        
        if not valor or not conta_bancaria:
            return jsonify({'error': 'Valor e conta bancária são obrigatórios'}), 400
        
        try:
            valor = float(valor)
        except:
            return jsonify({'error': 'Valor inválido'}), 400
        
        if valor < 10:
            return jsonify({'error': 'Valor mínimo para saque é R$ 10,00'}), 400
        
        if carteira_plataforma['saldo'] < valor:
            return jsonify({'error': f'Saldo insuficiente. Disponível: R$ {carteira_plataforma["saldo"]:.2f}'}), 400
        
        carteira_plataforma['saldo'] -= valor
        carteira_plataforma['total_sacado'] += valor
        carteira_plataforma['data_atualizacao'] = datetime.now()
        
        carteira_plataforma['extrato'].append({
            'id': len(carteira_plataforma['extrato']) + 1,
            'transacao_id': f"SAQ{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(4).upper()}",
            'tipo': 'saque',
            'valor': valor,
            'conta_bancaria': conta_bancaria,
            'data': datetime.now().isoformat()
        })
        
        return jsonify({
            'message': f'Saque de R$ {valor:.2f} realizado com sucesso!',
            'saldo_restante': carteira_plataforma['saldo']
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao sacar da carteira: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# VERIFICAR ONG
# =====================================================================

@admin_bp.route('/ongs/<int:ong_id>/verificar', methods=['PUT'])
@token_required
@admin_required
def verificar_ong(ong_id):
    try:
        data = request.get_json() or {}
        ong = OngRepository.buscar_por_id(ong_id)
        
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        if ong.get('status') == 'verificado':
            return jsonify({'error': 'ONG já está verificada'}), 400
        
        if ong.get('status') == 'bloqueado':
            return jsonify({'error': 'ONG está bloqueada'}), 400
        
        OngRepository.atualizar_status(
            ong_id,
            'verificado',
            datetime.now().isoformat(),
            g.user_id
        )
        
        AuditService.registrar_evento(
            evento='ong_verificada',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'ong_id': ong_id, 'ong_nome': ong.get('nome')},
            gravidade='alta'
        )
        
        enviar_email(
            ong.get('email'),
            '✅ Sua ONG foi verificada na Doa+!',
            f'''
Olá {ong.get('nome')},

🎉 Sua ONG foi VERIFICADA com sucesso na plataforma Doa+!

✅ Agora você pode:
   • Cadastrar necessidades de doação
   • Receber doações financeiras
   • Solicitar saques para sua conta bancária

📊 Acesse seu dashboard:
   https://doa-b988.onrender.com/dashboard_ong.html

Equipe Doa+'''
        )
        
        return jsonify({
            'message': 'ONG verificada com sucesso!',
            'ong_id': ong_id,
            'status': 'verificado'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# REJEITAR ONG
# =====================================================================

@admin_bp.route('/ongs/<int:ong_id>/rejeitar', methods=['PUT'])
@token_required
@admin_required
def rejeitar_ong(ong_id):
    try:
        data = request.get_json()
        motivo = sanitizar_string(data.get('motivo', 'Documentação insuficiente'))
        
        ong = OngRepository.buscar_por_id(ong_id)
        
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        if ong.get('status') == 'verificado':
            return jsonify({'error': 'ONG já está verificada'}), 400
        
        if ong.get('status') == 'bloqueado':
            return jsonify({'error': 'ONG está bloqueada'}), 400
        
        OngRepository.atualizar(ong_id, {
            'status': 'rejeitado',
            'motivo_rejeicao': motivo
        })
        
        AuditService.registrar_evento(
            evento='ong_rejeitada',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'ong_id': ong_id, 'ong_nome': ong.get('nome'), 'motivo': motivo},
            gravidade='media'
        )
        
        enviar_email(
            ong.get('email'),
            '❌ Verificação da sua ONG foi rejeitada',
            f'''
Olá {ong.get('nome')},

Infelizmente a verificação da sua ONG na plataforma Doa+ foi rejeitada.

📋 Motivo: {motivo}

📌 Para corrigir:
   1. Revise as informações cadastradas
   2. Atualize os dados necessários
   3. Entre em contato conosco para uma nova verificação

Equipe Doa+'''
        )
        
        return jsonify({
            'message': 'ONG rejeitada com sucesso!',
            'ong_id': ong_id,
            'status': 'rejeitado'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao rejeitar ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# LISTAR ONGS
# =====================================================================

@admin_bp.route('/ongs', methods=['GET'])
@token_required
@admin_required
def listar_ongs():
    try:
        ongs = OngRepository.listar_todos()
        
        for ong in ongs:
            carteira = CarteiraRepository.buscar_por_ong(ong.get('id'))
            ong['saldo_carteira'] = carteira.get('saldo', 0) if carteira else 0
            ong['total_recebido'] = carteira.get('total_recebido', 0) if carteira else 0
            ong['total_sacado'] = carteira.get('total_sacado', 0) if carteira else 0
            
            # Buscar advertências
            ong['advertencias'] = [a for a in advertencias_db.values() if a.get('ong_id') == ong.get('id')]
        
        return jsonify({'ongs': ongs}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar ONGs: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/ongs/<int:ong_id>', methods=['GET'])
@token_required
@admin_required
def obter_ong(ong_id):
    try:
        ong = OngRepository.buscar_por_id(ong_id)
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        carteira = CarteiraRepository.buscar_por_ong(ong_id)
        ong['saldo_carteira'] = carteira.get('saldo', 0) if carteira else 0
        
        return jsonify(ong), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# BLOQUEAR/DESBLOQUEAR ONG
# =====================================================================

@admin_bp.route('/ongs/<int:ong_id>/bloquear', methods=['PUT'])
@token_required
@admin_required
def bloquear_ong(ong_id):
    try:
        ong = OngRepository.buscar_por_id(ong_id)
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        OngRepository.atualizar_status(ong_id, 'bloqueado')
        
        AuditService.registrar_evento(
            evento='ong_bloqueada',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'ong_id': ong_id, 'ong_nome': ong.get('nome')},
            gravidade='alta'
        )
        
        return jsonify({'message': 'ONG bloqueada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao bloquear ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/ongs/<int:ong_id>/desbloquear', methods=['PUT'])
@token_required
@admin_required
def desbloquear_ong(ong_id):
    try:
        ong = OngRepository.buscar_por_id(ong_id)
        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404
        
        OngRepository.atualizar_status(ong_id, 'verificado')
        
        AuditService.registrar_evento(
            evento='ong_desbloqueada',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'ong_id': ong_id, 'ong_nome': ong.get('nome')},
            gravidade='media'
        )
        
        return jsonify({'message': 'ONG desbloqueada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao desbloquear ONG: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# LISTAR DOADORES
# =====================================================================

@admin_bp.route('/doadores', methods=['GET'])
@token_required
@admin_required
def listar_doadores():
    try:
        doadores = DoadorRepository.listar_todos()
        return jsonify({'doadores': doadores}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doadores: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/doadores/<int:doador_id>', methods=['GET'])
@token_required
@admin_required
def obter_doador(doador_id):
    try:
        doador = DoadorRepository.buscar_por_id(doador_id)
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        return jsonify(doador), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter doador: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# BLOQUEAR DOADOR
# =====================================================================

@admin_bp.route('/doadores/<int:doador_id>/bloquear', methods=['PUT'])
@token_required
@admin_required
def bloquear_doador(doador_id):
    try:
        doador = DoadorRepository.buscar_por_id(doador_id)
        if not doador:
            return jsonify({'error': 'Doador não encontrado'}), 404
        
        DoadorRepository.atualizar(doador_id, {'status': 'bloqueado'})
        
        AuditService.registrar_evento(
            evento='doador_bloqueado',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'doador_id': doador_id, 'doador_nome': doador.get('nome')},
            gravidade='media'
        )
        
        return jsonify({'message': 'Doador bloqueado com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao bloquear doador: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# LISTAR ANÚNCIOS (NECESSIDADES)
# =====================================================================

@admin_bp.route('/anuncios', methods=['GET'])
@token_required
@admin_required
def listar_anuncios():
    try:
        anuncios = []
        for nec_id, nec in necessidades_db.items():
            ong = OngRepository.buscar_por_id(nec.get('ong_id'))
            if ong:
                anuncios.append({
                    'id': nec_id,
                    'ong_id': nec.get('ong_id'),
                    'ong_nome': ong.get('nome'),
                    'titulo': nec.get('titulo'),
                    'descricao': nec.get('descricao'),
                    'categoria': nec.get('categoria'),
                    'urgencia': nec.get('urgencia'),
                    'quantidade_necessaria': nec.get('quantidade_necessaria'),
                    'quantidade_recebida': nec.get('quantidade_recebida', 0),
                    'status': nec.get('status'),
                    'total_advertencias': len([a for a in advertencias_db.values() if a.get('anuncio_id') == nec_id]),
                    'data_criacao': nec.get('data_criacao'),
                    'excluido': nec.get('status') == 'excluido',
                    'advertencias': [a for a in advertencias_db.values() if a.get('anuncio_id') == nec_id]
                })
        
        return jsonify({'anuncios': anuncios}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar anúncios: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/anuncios/<int:anuncio_id>', methods=['GET'])
@token_required
@admin_required
def obter_anuncio(anuncio_id):
    try:
        nec = necessidades_db.get(anuncio_id)
        if not nec:
            return jsonify({'error': 'Anúncio não encontrado'}), 404
        
        ong = OngRepository.buscar_por_id(nec.get('ong_id'))
        
        anuncio = {
            'id': anuncio_id,
            'ong_id': nec.get('ong_id'),
            'ong_nome': ong.get('nome') if ong else 'Desconhecida',
            'titulo': nec.get('titulo'),
            'descricao': nec.get('descricao'),
            'categoria': nec.get('categoria'),
            'urgencia': nec.get('urgencia'),
            'quantidade_necessaria': nec.get('quantidade_necessaria'),
            'quantidade_recebida': nec.get('quantidade_recebida', 0),
            'status': nec.get('status'),
            'data_criacao': nec.get('data_criacao'),
            'advertencias': [a for a in advertencias_db.values() if a.get('anuncio_id') == anuncio_id]
        }
        
        return jsonify(anuncio), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter anúncio: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# EXCLUIR ANÚNCIO
# =====================================================================

@admin_bp.route('/anuncios/<int:anuncio_id>/excluir', methods=['DELETE'])
@token_required
@admin_required
def excluir_anuncio(anuncio_id):
    try:
        if anuncio_id not in necessidades_db:
            return jsonify({'error': 'Anúncio não encontrado'}), 404
        
        NecessidadeRepository.atualizar_status(anuncio_id, 'excluido')
        
        AuditService.registrar_evento(
            evento='anuncio_excluido',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'anuncio_id': anuncio_id},
            gravidade='media'
        )
        
        return jsonify({'message': 'Anúncio excluído com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao excluir anúncio: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# ADVERTÊNCIAS
# =====================================================================

@admin_bp.route('/advertencias', methods=['POST'])
@token_required
@admin_required
def adicionar_advertencia():
    global next_advertencia_id
    
    try:
        data = request.json
        anuncio_id = data.get('anuncio_id')
        ong_id = data.get('ong_id')
        motivo = data.get('motivo')
        descricao = data.get('descricao')
        acao = data.get('acao', 'apenas_advertir')
        
        if not anuncio_id or not ong_id or not motivo:
            return jsonify({'error': 'Dados incompletos'}), 400
        
        advertencia = {
            'id': next_advertencia_id,
            'anuncio_id': anuncio_id,
            'ong_id': ong_id,
            'motivo': motivo,
            'descricao': descricao,
            'data': datetime.now().isoformat(),
            'admin': g.user_id
        }
        advertencias_db[next_advertencia_id] = advertencia
        next_advertencia_id += 1
        
        ong = OngRepository.buscar_por_id(ong_id)
        if ong:
            total_advertencias = len([a for a in advertencias_db.values() if a.get('ong_id') == ong_id])
            OngRepository.atualizar(ong_id, {'total_advertencias': total_advertencias})
            
            if total_advertencias >= 3:
                OngRepository.atualizar_status(ong_id, 'bloqueado')
                enviar_email(
                    ong.get('email'),
                    '🔴 Sua ONG foi bloqueada por excesso de advertências',
                    f'''
Olá {ong.get('nome')},

Sua ONG foi BLOQUEADA na plataforma Doa+ por atingir 3 advertências.

📋 Motivo: {motivo}

📌 Para reativar sua conta, entre em contato com o suporte.

Equipe Doa+'''
                )
        
        if acao == 'remover_anuncio':
            if anuncio_id in necessidades_db:
                NecessidadeRepository.atualizar_status(anuncio_id, 'excluido')
        elif acao == 'bloquear_ong' and ong:
            OngRepository.atualizar_status(ong_id, 'bloqueado')
        
        AuditService.registrar_evento(
            evento='advertencia_aplicada',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'anuncio_id': anuncio_id, 'ong_id': ong_id, 'motivo': motivo},
            gravidade='media'
        )
        
        return jsonify({'message': 'Advertência aplicada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao adicionar advertência: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# COMUNICAÇÃO
# =====================================================================

@admin_bp.route('/comunicacao/enviar', methods=['POST'])
@token_required
@admin_required
def enviar_comunicacao():
    global next_comunicacao_id
    
    try:
        data = request.json
        tipo = data.get('tipo')
        titulo = sanitizar_string(data.get('titulo', ''))
        mensagem = sanitizar_html(data.get('mensagem', ''))
        prioridade = data.get('prioridade', 'normal')
        destinatario_id = data.get('destinatario_id')
        destinatario_tipo = data.get('destinatario_tipo')
        
        if not titulo or not mensagem:
            return jsonify({'error': 'Título e mensagem são obrigatórios'}), 400
        
        if tipo == 'especifico' and not destinatario_id:
            return jsonify({'error': 'Para envio específico, informe o ID do usuário'}), 400
        
        # Buscar nome do destinatário se for específico
        destinatario_nome = None
        if tipo == 'especifico' and destinatario_id:
            if destinatario_tipo == 'ong':
                ong = OngRepository.buscar_por_id(destinatario_id)
                if ong:
                    destinatario_nome = ong.get('nome')
            elif destinatario_tipo == 'doador':
                doador = DoadorRepository.buscar_por_id(destinatario_id)
                if doador:
                    destinatario_nome = doador.get('nome')
        
        comunicacao = {
            'id': next_comunicacao_id,
            'tipo': tipo,
            'titulo': titulo,
            'mensagem': mensagem,
            'prioridade': prioridade,
            'destinatario_id': destinatario_id,
            'destinatario_tipo': destinatario_tipo,
            'destinatario_nome': destinatario_nome,
            'admin_id': g.user_id,
            'admin_email': g.token_payload.get('email', 'admin@doamais.org'),
            'data_envio': datetime.now().isoformat(),
            'lida': False,
            'data_leitura': None
        }
        comunicacoes_db.append(comunicacao)
        next_comunicacao_id += 1
        
        AuditService.registrar_evento(
            evento='comunicacao_enviada',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'tipo': tipo, 'titulo': titulo},
            gravidade='info'
        )
        
        return jsonify({'message': 'Comunicação enviada com sucesso!', 'id': comunicacao['id']}), 201
        
    except Exception as e:
        logger.error(f"Erro ao enviar comunicação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/comunicacoes', methods=['GET'])
@token_required
@admin_required
def listar_comunicacoes_admin():
    try:
        return jsonify({'comunicacoes': comunicacoes_db}), 200
    except Exception as e:
        logger.error(f"Erro ao listar comunicações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/comunicacoes/<int:comunicacao_id>', methods=['DELETE'])
@token_required
@admin_required
def deletar_comunicacao(comunicacao_id):
    try:
        for i, c in enumerate(comunicacoes_db):
            if c.get('id') == comunicacao_id:
                del comunicacoes_db[i]
                return jsonify({'message': 'Comunicação deletada com sucesso!'}), 200
        
        return jsonify({'error': 'Comunicação não encontrada'}), 404
    except Exception as e:
        logger.error(f"Erro ao deletar comunicação: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# FEEDBACK (ADMIN)
# =====================================================================

@admin_bp.route('/feedback', methods=['GET'])
@token_required
@admin_required
def listar_feedbacks_admin():
    try:
        status = request.args.get('status')
        feedbacks = list(feedback_db.values())
        
        if status and status != 'todos':
            feedbacks = [f for f in feedbacks if f.get('status') == status]
        
        feedbacks.sort(key=lambda x: x.get('data', ''), reverse=True)
        
        return jsonify({'feedbacks': feedbacks}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar feedbacks: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/feedback/<int:feedback_id>', methods=['PUT'])
@token_required
@admin_required
def responder_feedback(feedback_id):
    try:
        data = request.json
        resposta = sanitizar_html(data.get('resposta', ''))
        status = data.get('status', 'respondido')
        
        if feedback_id not in feedback_db:
            return jsonify({'error': 'Feedback não encontrado'}), 404
        
        feedback_db[feedback_id]['resposta'] = resposta
        feedback_db[feedback_id]['status'] = status
        feedback_db[feedback_id]['data_resposta'] = datetime.now().isoformat()
        
        return jsonify({'message': 'Feedback respondido com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao responder feedback: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# SUPORTE (ADMIN)
# =====================================================================

@admin_bp.route('/suporte', methods=['GET'])
@token_required
@admin_required
def listar_suportes_admin():
    try:
        status = request.args.get('status')
        suportes = list(suporte_db.values())
        
        if status and status != 'todos':
            suportes = [s for s in suportes if s.get('status') == status]
        
        suportes.sort(key=lambda x: x.get('data', ''), reverse=True)
        
        return jsonify({'suportes': suportes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar suportes: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/suporte/<int:suporte_id>', methods=['PUT'])
@token_required
@admin_required
def responder_suporte(suporte_id):
    try:
        data = request.json
        resposta = sanitizar_html(data.get('resposta', ''))
        status = data.get('status', 'resolvido')
        
        if suporte_id not in suporte_db:
            return jsonify({'error': 'Solicitação não encontrada'}), 404
        
        suporte_db[suporte_id]['resposta'] = resposta
        suporte_db[suporte_id]['status'] = status
        suporte_db[suporte_id]['data_resposta'] = datetime.now().isoformat()
        
        return jsonify({'message': 'Solicitação respondida com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao responder suporte: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# SOLICITAÇÕES DE EXCLUSÃO
# =====================================================================

@admin_bp.route('/solicitacoes/exclusao', methods=['GET'])
@token_required
@admin_required
def listar_solicitacoes_exclusao():
    try:
        solicitacoes = list(solicitacoes_exclusao_db.values())
        return jsonify({'solicitacoes': solicitacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar solicitações de exclusão: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/solicitacoes/exclusao/<int:solicitacao_id>/confirmar', methods=['DELETE'])
@token_required
@admin_required
def confirmar_exclusao(solicitacao_id):
    try:
        solicitacao = solicitacoes_exclusao_db.get(solicitacao_id)
        if not solicitacao:
            return jsonify({'error': 'Solicitação não encontrada'}), 404
        
        user_id = solicitacao.get('usuario_id')
        user_type = solicitacao.get('usuario_tipo')
        
        if user_type == 'doador':
            if user_id in doadores_db:
                del doadores_db[user_id]
        elif user_type == 'ong':
            if user_id in ongs_db:
                del ongs_db[user_id]
        
        solicitacao['status'] = 'confirmado'
        solicitacao['data_confirmacao'] = datetime.now().isoformat()
        
        AuditService.registrar_evento(
            evento='conta_excluida',
            usuario_id=g.user_id,
            usuario_tipo='admin',
            ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            detalhes={'usuario_id': user_id, 'usuario_tipo': user_type},
            gravidade='alta'
        )
        
        return jsonify({'message': 'Conta excluída com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao confirmar exclusão: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@admin_bp.route('/solicitacoes/exclusao/<int:solicitacao_id>/cancelar', methods=['PUT'])
@token_required
@admin_required
def cancelar_exclusao(solicitacao_id):
    try:
        solicitacao = solicitacoes_exclusao_db.get(solicitacao_id)
        if not solicitacao:
            return jsonify({'error': 'Solicitação não encontrada'}), 404
        
        solicitacao['status'] = 'cancelado'
        solicitacao['data_cancelamento'] = datetime.now().isoformat()
        
        return jsonify({'message': 'Solicitação cancelada com sucesso!'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao cancelar exclusão: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# DOAÇÕES (ADMIN)
# =====================================================================

@admin_bp.route('/doacoes', methods=['GET'])
@token_required
@admin_required
def listar_doacoes_admin():
    try:
        doacoes = DoacaoRepository.listar_todos()
        
        for d in doacoes:
            doador = DoadorRepository.buscar_por_id(d.get('doador_id'))
            ong = OngRepository.buscar_por_id(d.get('ong_id'))
            necessidade = NecessidadeRepository.buscar_por_id(d.get('necessidade_id'))
            d['doador_nome'] = doador.get('nome') if doador else 'Desconhecido'
            d['ong_nome'] = ong.get('nome') if ong else 'Desconhecida'
            d['item'] = necessidade.get('titulo') if necessidade else 'Item não encontrado'
        
        doacoes.sort(key=lambda x: x.get('data_doacao', ''), reverse=True)
        
        return jsonify({'doacoes': doacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# DOAÇÕES FINANCEIRAS (ADMIN)
# =====================================================================

@admin_bp.route('/doacoes/financeiras', methods=['GET'])
@token_required
@admin_required
def listar_doacoes_financeiras_admin():
    try:
        doacoes = list(doacoes_financeiras_db.values())
        
        for d in doacoes:
            doador = DoadorRepository.buscar_por_id(d.get('doador_id'))
            ong = OngRepository.buscar_por_id(d.get('ong_id'))
            d['doador_nome'] = doador.get('nome') if doador else 'Desconhecido'
            d['ong_nome'] = ong.get('nome') if ong else 'Desconhecida'
        
        doacoes.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
        
        return jsonify({'doacoes': doacoes}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar doações financeiras: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# LOGS (ADMIN)
# =====================================================================

@admin_bp.route('/logs', methods=['GET'])
@token_required
@admin_required
def listar_logs_admin():
    try:
        limit = int(request.args.get('limit', 100))
        gravidade = request.args.get('gravidade')
        
        logs = AuditRepository.obter_logs(limit, gravidade)
        
        return jsonify({'logs': logs}), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar logs: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


# =====================================================================
# RELATÓRIOS (ADMIN)
# =====================================================================

@admin_bp.route('/relatorios/gerar', methods=['POST'])
@token_required
@admin_required
def gerar_relatorio():
    try:
        data = request.json
        tipo = data.get('tipo', 'financeiro')
        
        if tipo == 'financeiro':
            total_doacoes = len(doacoes_financeiras_db)
            total_valor = sum(d.get('valor', 0) for d in doacoes_financeiras_db.values())
            total_taxas = sum(d.get('taxa_servico', 0) for d in doacoes_financeiras_db.values())
            total_confirmadas = len([d for d in doacoes_financeiras_db.values() if d.get('status') == 'confirmado'])
            
            relatorio = {
                'data_geracao': datetime.now().isoformat(),
                'total_doacoes_financeiras': total_doacoes,
                'valor_total': total_valor,
                'total_taxas': total_taxas,
                'total_confirmadas': total_confirmadas,
                'valor_medio': total_valor / total_doacoes if total_doacoes > 0 else 0
            }
            
            return jsonify({'dados': relatorio}), 200
        
        return jsonify({'error': 'Tipo de relatório inválido'}), 400
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
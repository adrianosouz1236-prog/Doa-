# database/repositories.py - COMPLETO COM DADOS DE TESTE
from .conexao import db
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

# =====================================================================
# DADOS EM MEMÓRIA - DEFINIDOS ANTES DA FUNÇÃO
# =====================================================================

ongs_db = {}
doadores_db = {}
administradores_db = {}
necessidades_db = {}
doacoes_db = {}
doacoes_financeiras_db = {}
carteiras_db = {}
logs_db = {}
tentativas_login_db = {}
ong_fotos_db = {}
ong_eventos_db = {}
ong_parcerias_db = {}
advertencias_db = {}
feedback_db = {}
suporte_db = {}
comunicacoes_db = []
solicitacoes_exclusao_db = {}
voluntariado_db = {}
avaliacoes_db = {}
transacoes_db = {}

next_ong_id = 1
next_doador_id = 1
next_admin_id = 1
next_necessidade_id = 1
next_doacao_id = 1
next_doacao_financeira_id = 1
next_carteira_id = 1
next_log_id = 1
next_tentativa_id = 1
next_foto_id = 1
next_evento_id = 1
next_parceria_id = 1
next_advertencia_id = 1
next_feedback_id = 1
next_suporte_id = 1
next_comunicacao_id = 1
next_solicitacao_id = 1
next_vaga_id = 1
next_avaliacao_id = 1
next_transacao_id = 1


# =====================================================================
# FUNÇÃO DE INICIALIZAÇÃO
# =====================================================================

def init_test_data():
    """Inicializa dados de teste em memória"""
    from security import hash_senha
    from datetime import datetime
    
    global ongs_db, doadores_db, administradores_db, necessidades_db, doacoes_db
    global doacoes_financeiras_db, carteiras_db, ong_eventos_db, voluntariado_db
    
    if ongs_db and doadores_db and administradores_db:
        print("⚠️ Dados já inicializados")
        return
    
    print("🧪 Carregando dados de teste...")
    
    # ============================================================
    # ADMINISTRADOR
    # ============================================================
    admin_data = {
        'id': 1,
        'nome': 'Administrador',
        'email': 'admin@doamais.org',
        'senha': hash_senha('admin123'),
        'tipo': 'admin',
        'status': 'ativo',
        'data_cadastro': datetime.now().isoformat()
    }
    administradores_db[1] = admin_data
    print(f"✅ Admin criado: {admin_data['email']}")
    
    # ============================================================
    # ONG DE TESTE
    # ============================================================
    ong_data = {
        'id': 1,
        'nome': 'ONG Solidária Brasil',
        'cnpj': '12.345.678/0001-90',
        'email': 'ong@solidaria.org',
        'senha': hash_senha('Ong@123456'),
        'telefone': '(11) 99999-9999',
        'endereco': 'Rua da Solidariedade, 100',
        'cidade': 'São Paulo',
        'uf': 'SP',
        'descricao': 'ONG dedicada a ajudar pessoas em situação de vulnerabilidade social.',
        'status': 'verificado',
        'data_cadastro': datetime.now().isoformat(),
        'media_avaliacao': 4.5,
        'total_avaliacoes': 10,
        'latitude': -23.550520,
        'longitude': -46.633308,
        'endereco_completo': 'Rua da Solidariedade, 100 - São Paulo - SP',
        'logo_url': 'https://via.placeholder.com/150?text=ONG',
        'email_confirmado': True,
        'consentimento_lgpd': True,
        'conta_bancaria_criptografada': None
    }
    ongs_db[1] = ong_data
    print(f"✅ ONG criada: {ong_data['email']}")
    
    # ============================================================
    # DOADOR DE TESTE
    # ============================================================
    doador_data = {
        'id': 1,
        'nome': 'João Silva',
        'email': 'joao@email.com',
        'senha': hash_senha('Doador@123456'),
        'telefone': '(11) 98888-7777',
        'cpf': '123.456.789-00',
        'endereco': 'Rua das Flores, 123',
        'cidade': 'São Paulo',
        'uf': 'SP',
        'status': 'ativo',
        'data_cadastro': datetime.now().isoformat(),
        'total_doacoes': 5,
        'pontuacao': 150,
        'conquistas': ['primeira_doacao', 'doador_frequente'],
        'email_confirmado': True,
        'consentimento_lgpd': True
    }
    doadores_db[1] = doador_data
    print(f"✅ Doador criado: {doador_data['email']}")
    
    # ============================================================
    # CARTEIRA DA ONG
    # ============================================================
    carteiras_db[1] = {
        'ong_id': 1,
        'saldo': 150.00,
        'total_recebido': 250.00,
        'total_sacado': 100.00
    }
    print("✅ Carteira criada")
    
    # ============================================================
    # NECESSIDADE DE TESTE
    # ============================================================
    necessidades_db[1] = {
        'id': 1,
        'ong_id': 1,
        'titulo': 'Arrecadação de Alimentos',
        'descricao': 'Precisamos de alimentos não perecíveis para distribuir para 100 famílias.',
        'categoria': 'alimentos',
        'quantidade_necessaria': 500,
        'quantidade_recebida': 150,
        'urgencia': 'alta',
        'status': 'aberta',
        'data_criacao': datetime.now().isoformat()
    }
    print(f"✅ Necessidade criada: {necessidades_db[1]['titulo']}")
    
    # ============================================================
    # EVENTO DE TESTE
    # ============================================================
    ong_eventos_db[1] = {
        'id': 1,
        'ong_id': 1,
        'titulo': 'Dia da Solidariedade',
        'descricao': 'Venha participar do nosso evento de arrecadação de alimentos e roupas.',
        'data_evento': datetime.now().isoformat(),
        'local_evento': 'Parque da Cidade',
        'endereco': 'Av. Principal, 500',
        'cidade': 'São Paulo',
        'uf': 'SP',
        'status': 'ativo',
        'data_criacao': datetime.now().isoformat()
    }
    print(f"✅ Evento criado: {ong_eventos_db[1]['titulo']}")
    
    # ============================================================
    # VAGA DE VOLUNTARIADO
    # ============================================================
    voluntariado_db[1] = {
        'id': 1,
        'ong_id': 1,
        'ong_nome': 'ONG Solidária Brasil',
        'titulo': 'Voluntário para distribuição de alimentos',
        'descricao': 'Ajudar na organização e distribuição de alimentos para famílias carentes.',
        'data_evento': datetime.now().isoformat(),
        'local': 'Parque da Cidade',
        'vagas_disponiveis': 10,
        'vagas_preenchidas': 3,
        'status': 'aberta',
        'data_criacao': datetime.now().isoformat()
    }
    print(f"✅ Vaga de voluntariado criada: {voluntariado_db[1]['titulo']}")
    
    print("\n" + "="*60)
    print("✅ DADOS DE TESTE CARREGADOS COM SUCESSO!")
    print("="*60)
    print("\n🔑 CREDENCIAIS:")
    print("   👑 Admin: admin@doamais.org / admin123")
    print("   🏢 ONG:   ong@solidaria.org / Ong@123456")
    print("   👤 Doador: joao@email.com / Doador@123456")
    print("="*60 + "\n")


# =====================================================================
# REPOSITÓRIO DE ADMINISTRADOR
# =====================================================================

class AdminRepository:
    @staticmethod
    def buscar_por_email(email):
        for admin in administradores_db.values():
            if admin.get('email') == email:
                return admin
        return None
    
    @staticmethod
    def buscar_por_id(admin_id):
        return administradores_db.get(admin_id)


# =====================================================================
# REPOSITÓRIO DE ONG
# =====================================================================

class OngRepository:
    @staticmethod
    def criar(ong_data):
        global next_ong_id
        ong_id = next_ong_id
        next_ong_id += 1
        
        ong_data['id'] = ong_id
        ong_data['data_cadastro'] = datetime.now().isoformat()
        ong_data['data_atualizacao'] = datetime.now().isoformat()
        ong_data['total_advertencias'] = 0
        ong_data['media_avaliacao'] = 0
        ong_data['total_avaliacoes'] = 0
        
        ongs_db[ong_id] = ong_data
        return ong_id
    
    @staticmethod
    def buscar_por_id(ong_id):
        return ongs_db.get(ong_id)
    
    @staticmethod
    def buscar_por_email(email):
        for ong in ongs_db.values():
            if ong.get('email') == email:
                return ong
        return None
    
    @staticmethod
    def buscar_por_cnpj(cnpj):
        for ong in ongs_db.values():
            if ong.get('cnpj') == cnpj:
                return ong
        return None
    
    @staticmethod
    def listar_todos(status=None):
        ongs = list(ongs_db.values())
        if status:
            ongs = [o for o in ongs if o.get('status') == status]
        return ongs
    
    @staticmethod
    def atualizar(ong_id, dados):
        if ong_id not in ongs_db:
            return False
        ongs_db[ong_id].update(dados)
        ongs_db[ong_id]['data_atualizacao'] = datetime.now().isoformat()
        return True
    
    @staticmethod
    def atualizar_status(ong_id, status, data_verificacao=None, verificado_por=None):
        dados = {'status': status}
        if data_verificacao:
            dados['data_verificacao'] = data_verificacao
        if verificado_por:
            dados['verificado_por'] = verificado_por
        return OngRepository.atualizar(ong_id, dados)


# =====================================================================
# REPOSITÓRIO DE DOADOR
# =====================================================================

class DoadorRepository:
    @staticmethod
    def criar(doador_data):
        global next_doador_id
        doador_id = next_doador_id
        next_doador_id += 1
        
        doador_data['id'] = doador_id
        doador_data['data_cadastro'] = datetime.now().isoformat()
        doador_data['data_atualizacao'] = datetime.now().isoformat()
        doador_data['total_doacoes'] = 0
        doador_data['pontuacao'] = 0
        doador_data['conquistas'] = []
        doador_data['total_itens'] = 0
        
        doadores_db[doador_id] = doador_data
        return doador_id
    
    @staticmethod
    def buscar_por_id(doador_id):
        return doadores_db.get(doador_id)
    
    @staticmethod
    def buscar_por_email(email):
        for doador in doadores_db.values():
            if doador.get('email') == email:
                return doador
        return None
    
    @staticmethod
    def listar_todos(status=None):
        doadores = list(doadores_db.values())
        if status:
            doadores = [d for d in doadores if d.get('status') == status]
        return doadores
    
    @staticmethod
    def atualizar(doador_id, dados):
        if doador_id not in doadores_db:
            return False
        doadores_db[doador_id].update(dados)
        doadores_db[doador_id]['data_atualizacao'] = datetime.now().isoformat()
        return True


# =====================================================================
# REPOSITÓRIO DE NECESSIDADES
# =====================================================================

class NecessidadeRepository:
    @staticmethod
    def criar(necessidade_data):
        global next_necessidade_id
        necessidade_id = next_necessidade_id
        next_necessidade_id += 1
        
        necessidade_data['id'] = necessidade_id
        necessidade_data['data_criacao'] = datetime.now().isoformat()
        necessidade_data['quantidade_recebida'] = 0
        necessidade_data['status'] = 'aberta'
        
        necessidades_db[necessidade_id] = necessidade_data
        return necessidade_id
    
    @staticmethod
    def buscar_por_id(necessidade_id):
        return necessidades_db.get(necessidade_id)
    
    @staticmethod
    def buscar_por_ong(ong_id, status=None):
        necessidades = [n for n in necessidades_db.values() if n.get('ong_id') == ong_id]
        if status:
            necessidades = [n for n in necessidades if n.get('status') == status]
        return necessidades
    
    @staticmethod
    def listar_abertas():
        return [n for n in necessidades_db.values() if n.get('status') == 'aberta']
    
    @staticmethod
    def atualizar(necessidade_id, dados):
        if necessidade_id in necessidades_db:
            necessidades_db[necessidade_id].update(dados)
            return True
        return False
    
    @staticmethod
    def atualizar_quantidade_recebida(necessidade_id, quantidade):
        if necessidade_id in necessidades_db:
            necessidades_db[necessidade_id]['quantidade_recebida'] += quantidade
            return True
        return False
    
    @staticmethod
    def atualizar_status(necessidade_id, status):
        if necessidade_id in necessidades_db:
            necessidades_db[necessidade_id]['status'] = status
            return True
        return False


# =====================================================================
# REPOSITÓRIO DE DOAÇÕES
# =====================================================================

class DoacaoRepository:
    @staticmethod
    def criar(doacao_data):
        global next_doacao_id
        doacao_id = next_doacao_id
        next_doacao_id += 1
        
        doacao_data['id'] = doacao_id
        doacao_data['data_doacao'] = datetime.now().isoformat()
        necessidade = NecessidadeRepository.buscar_por_id(doacao_data['necessidade_id'])
        if necessidade:
            doacao_data['ong_id'] = necessidade.get('ong_id')
        
        doacoes_db[doacao_id] = doacao_data
        return doacao_id
    
    @staticmethod
    def buscar_por_id(doacao_id):
        return doacoes_db.get(doacao_id)
    
    @staticmethod
    def listar_por_doador(doador_id, status=None, limite=10, offset=0):
        doacoes = [d for d in doacoes_db.values() if d.get('doador_id') == doador_id]
        if status:
            doacoes = [d for d in doacoes if d.get('status') == status]
        doacoes.sort(key=lambda x: x.get('data_doacao'), reverse=True)
        return doacoes[offset:offset+limite]
    
    @staticmethod
    def listar_por_ong(ong_id, status=None, limite=10, offset=0):
        doacoes = [d for d in doacoes_db.values() if d.get('ong_id') == ong_id]
        if status:
            doacoes = [d for d in doacoes if d.get('status') == status]
        doacoes.sort(key=lambda x: x.get('data_doacao'), reverse=True)
        return doacoes[offset:offset+limite]
    
    @staticmethod
    def listar_todos():
        return list(doacoes_db.values())
    
    @staticmethod
    def atualizar_status(doacao_id, status):
        if doacao_id in doacoes_db:
            doacoes_db[doacao_id]['status'] = status
            return True
        return False


# =====================================================================
# REPOSITÓRIO DE DOAÇÕES FINANCEIRAS
# =====================================================================

class DoacaoFinanceiraRepository:
    @staticmethod
    def criar(doacao_data):
        global next_doacao_financeira_id
        doacao_id = next_doacao_financeira_id
        next_doacao_financeira_id += 1
        
        doacao_data['id'] = doacao_id
        doacao_data['data_criacao'] = datetime.now().isoformat()
        doacao_data['status'] = doacao_data.get('status', 'pendente')
        
        doacoes_financeiras_db[doacao_id] = doacao_data
        return doacao_id
    
    @staticmethod
    def buscar_por_id(doacao_id):
        return doacoes_financeiras_db.get(doacao_id)
    
    @staticmethod
    def buscar_por_external_reference(external_reference):
        for doacao in doacoes_financeiras_db.values():
            if doacao.get('external_reference') == external_reference:
                return doacao
        return None
    
    @staticmethod
    def listar_por_doador(doador_id):
        return [d for d in doacoes_financeiras_db.values() if d.get('doador_id') == doador_id]
    
    @staticmethod
    def listar_por_ong(ong_id):
        return [d for d in doacoes_financeiras_db.values() if d.get('ong_id') == ong_id]
    
    @staticmethod
    def listar_todos():
        return list(doacoes_financeiras_db.values())
    
    @staticmethod
    def atualizar_status(doacao_id, status, data_confirmacao=None):
        if doacao_id in doacoes_financeiras_db:
            doacoes_financeiras_db[doacao_id]['status'] = status
            if data_confirmacao:
                doacoes_financeiras_db[doacao_id]['data_confirmacao'] = data_confirmacao
            return True
        return False
    
    @staticmethod
    def estatisticas_por_doador(doador_id):
        doacoes = DoacaoFinanceiraRepository.listar_por_doador(doador_id)
        confirmadas = [d for d in doacoes if d.get('status') == 'confirmado']
        
        total_doacoes = len(confirmadas)
        total_valor = sum(d.get('valor', 0) for d in confirmadas)
        media_valor = total_valor / total_doacoes if total_doacoes > 0 else 0
        recorrentes = len([d for d in confirmadas if d.get('recorrente', False)])
        
        return {
            'total_doacoes': total_doacoes,
            'total_valor': total_valor,
            'media_valor': round(media_valor, 2),
            'doacoes_recorrentes': recorrentes
        }
    
    @staticmethod
    def estatisticas_por_ong(ong_id):
        doacoes = DoacaoFinanceiraRepository.listar_por_ong(ong_id)
        confirmadas = [d for d in doacoes if d.get('status') == 'confirmado']
        
        total_doacoes = len(confirmadas)
        total_valor = sum(d.get('valor_liquido', d.get('valor', 0)) for d in confirmadas)
        media_valor = total_valor / total_doacoes if total_doacoes > 0 else 0
        
        return {
            'total_doacoes': total_doacoes,
            'total_valor': total_valor,
            'media_valor': round(media_valor, 2)
        }


# =====================================================================
# REPOSITÓRIO DE CARTEIRA
# =====================================================================

class CarteiraRepository:
    @staticmethod
    def criar(ong_id):
        global next_carteira_id
        carteira_id = next_carteira_id
        next_carteira_id += 1
        
        carteira_data = {
            'id': carteira_id,
            'ong_id': ong_id,
            'saldo': 0,
            'total_recebido': 0,
            'total_sacado': 0,
            'data_criacao': datetime.now().isoformat(),
            'data_atualizacao': datetime.now().isoformat()
        }
        carteiras_db[ong_id] = carteira_data
        return carteira_id
    
    @staticmethod
    def buscar_por_ong(ong_id):
        return carteiras_db.get(ong_id)
    
    @staticmethod
    def atualizar_saldo(ong_id, valor, tipo):
        if ong_id not in carteiras_db:
            return False
        
        carteira = carteiras_db[ong_id]
        if tipo == 'entrada':
            carteira['saldo'] += valor
            carteira['total_recebido'] += valor
        elif tipo == 'saida':
            if carteira['saldo'] >= valor:
                carteira['saldo'] -= valor
                carteira['total_sacado'] += valor
            else:
                return False
        else:
            return False
        
        carteira['data_atualizacao'] = datetime.now().isoformat()
        return True


# =====================================================================
# REPOSITÓRIO DE AUDITORIA
# =====================================================================

class AuditRepository:
    @staticmethod
    def registrar_evento(evento, usuario_id, usuario_tipo, ip, user_agent,
                         detalhes=None, gravidade='info'):
        global next_log_id
        log_id = next_log_id
        next_log_id += 1
        
        log_data = {
            'id': log_id,
            'evento': evento,
            'usuario_id': usuario_id,
            'usuario_tipo': usuario_tipo,
            'ip': ip,
            'user_agent': user_agent,
            'detalhes': detalhes,
            'gravidade': gravidade,
            'data_evento': datetime.now().isoformat()
        }
        logs_db[log_id] = log_data
        return log_id
    
    @staticmethod
    def registrar_tentativa_login(email, ip, sucesso):
        global next_tentativa_id
        tentativa_id = next_tentativa_id
        next_tentativa_id += 1
        
        tentativa_data = {
            'id': tentativa_id,
            'email': email,
            'ip': ip,
            'sucesso': sucesso,
            'data_tentativa': datetime.now().isoformat()
        }
        tentativas_login_db[tentativa_id] = tentativa_data
        return tentativa_id
    
    @staticmethod
    def contar_tentativas_falhas(ip, minutos=15):
        limite = (datetime.now() - timedelta(minutes=minutos)).isoformat()
        count = 0
        for tentativa in tentativas_login_db.values():
            if (tentativa.get('ip') == ip and
                tentativa.get('sucesso') == 0 and
                tentativa.get('data_tentativa') > limite):
                count += 1
        return count
    
    @staticmethod
    def obter_logs(limite=100, gravidade=None):
        logs = list(logs_db.values())
        if gravidade:
            logs = [l for l in logs if l.get('gravidade') == gravidade]
        logs.sort(key=lambda x: x.get('data_evento'), reverse=True)
        return logs[:limite]


# =====================================================================
# INICIALIZAR DADOS AUTOMATICAMENTE
# =====================================================================

# Chamar a inicialização automaticamente ao importar
init_test_data()

# services/doacao_service.py
from database.repositories import DoacaoRepository, NecessidadeRepository, DoadorRepository

class DoacaoService:
    @staticmethod
    def registrar_doacao(doador_id, necessidade_id, quantidade, mensagem=None):
        necessidade = NecessidadeRepository.buscar_por_id(necessidade_id)
        if not necessidade:
            return {'success': False, 'error': 'Necessidade não encontrada'}
        
        if necessidade.get('status') != 'aberta':
            return {'success': False, 'error': 'Esta necessidade não está mais ativa'}
        
        doador = DoadorRepository.buscar_por_id(doador_id)
        if not doador:
            return {'success': False, 'error': 'Doador não encontrado'}
        
        doacao_data = {
            'doador_id': doador_id,
            'necessidade_id': necessidade_id,
            'quantidade': quantidade,
            'mensagem': mensagem,
            'status': 'pendente'
        }
        
        doacao_id = DoacaoRepository.criar(doacao_data)
        NecessidadeRepository.atualizar_quantidade_recebida(necessidade_id, quantidade)
        
        return {
            'success': True,
            'doacao_id': doacao_id
        }
    
    @staticmethod
    def confirmar_doacao(doacao_id, ong_id):
        doacao = DoacaoRepository.buscar_por_id(doacao_id)
        if not doacao:
            return {'success': False, 'error': 'Doação não encontrada'}
        
        if doacao.get('ong_id') != ong_id:
            return {'success': False, 'error': 'Sem permissão para confirmar esta doação'}
        
        if doacao.get('status') == 'confirmada':
            return {'success': False, 'error': 'Doação já confirmada'}
        
        DoacaoRepository.atualizar_status(doacao_id, 'confirmada')
        
        return {'success': True}
    
    @staticmethod
    def listar_doacoes_por_doador(doador_id, status=None, limite=10, offset=0):
        return DoacaoRepository.listar_por_doador(doador_id, status, limite, offset)
    
    @staticmethod
    def listar_doacoes_por_ong(ong_id, status=None, limite=10, offset=0):
        return DoacaoRepository.listar_por_ong(ong_id, status, limite, offset)
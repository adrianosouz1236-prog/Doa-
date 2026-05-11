from db.conexão import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DoacaoService:
    """Serviço para gerenciamento de doações"""
    
    def registrar_doacao(self, doador_id, necessidade_id, quantidade, mensagem=None):
        """
        Registra uma nova doação
        """
        try:
            # Verificar se a necessidade existe e está aberta
            query_necessidade = """
                SELECT id, ong_id, quantidade_necessaria, quantidade_recebida, status
                FROM necessidades
                WHERE id = %s
            """
            necessidade = db.execute_query(query_necessidade, (necessidade_id,))
            
            if not necessidade:
                return {'success': False, 'error': 'Necessidade não encontrada'}
            
            necessidade = necessidade[0]
            
            if necessidade['status'] != 'aberta':
                return {'success': False, 'error': 'Esta necessidade já está encerrada'}
            
            # Verificar se não excede a quantidade necessária
            nova_quantidade = necessidade['quantidade_recebida'] + quantidade
            if nova_quantidade > necessidade['quantidade_necessaria']:
                return {
                    'success': False, 
                    'error': f'Quantidade excede o necessário. Restam apenas {necessidade["quantidade_necessaria"] - necessidade["quantidade_recebida"]} itens'
                }
            
            # Registrar doação
            query_doacao = """
                INSERT INTO doacoes 
                (doador_id, necessidade_id, quantidade, mensagem, status, data_doacao)
                VALUES (%s, %s, %s, %s, 'pendente', %s)
            """
            
            doacao_id = db.execute_query(query_doacao, (
                doador_id,
                necessidade_id,
                quantidade,
                mensagem,
                datetime.now()
            ))
            
            # Atualizar quantidade recebida na necessidade
            query_update = """
                UPDATE necessidades
                SET quantidade_recebida = quantidade_recebida + %s
                WHERE id = %s
            """
            db.execute_query(query_update, (quantidade, necessidade_id))
            
            # Verificar se necessidade foi totalmente atendida
            if nova_quantidade >= necessidade['quantidade_necessaria']:
                db.execute_query(
                    "UPDATE necessidades SET status = 'encerrada' WHERE id = %s",
                    (necessidade_id,)
                )
            
            return {'success': True, 'doacao_id': doacao_id}
            
        except Exception as e:
            logger.error(f"Erro ao registrar doação: {e}")
            return {'success': False, 'error': str(e)}
    
    def listar_doacoes_por_doador(self, doador_id, status=None, limite=10, offset=0):
        """Lista doações de um doador específico"""
        query = """
            SELECT d.id, d.quantidade, d.mensagem, d.status, d.data_doacao,
                   n.titulo as necessidade_titulo, n.categoria,
                   o.nome as ong_nome, o.id as ong_id
            FROM doacoes d
            JOIN necessidades n ON d.necessidade_id = n.id
            JOIN ongs o ON n.ong_id = o.id
            WHERE d.doador_id = %s
        """
        params = [doador_id]
        
        if status:
            query += " AND d.status = %s"
            params.append(status)
        
        query += " ORDER BY d.data_doacao DESC LIMIT %s OFFSET %s"
        params.extend([limite, offset])
        
        return db.execute_query(query, params)
    
    def listar_doacoes_por_ong(self, ong_id, status=None, limite=10, offset=0):
        """Lista doações recebidas por uma ONG"""
        query = """
            SELECT d.id, d.quantidade, d.mensagem, d.status, d.data_doacao,
                   n.titulo as necessidade_titulo, n.categoria,
                   do.nome as doador_nome, do.email as doador_email
            FROM doacoes d
            JOIN necessidades n ON d.necessidade_id = n.id
            JOIN doadores do ON d.doador_id = do.id
            WHERE n.ong_id = %s
        """
        params = [ong_id]
        
        if status:
            query += " AND d.status = %s"
            params.append(status)
        
        query += " ORDER BY d.data_doacao DESC LIMIT %s OFFSET %s"
        params.extend([limite, offset])
        
        return db.execute_query(query, params)
    
    def confirmar_doacao(self, doacao_id, ong_id):
        """Confirma uma doação (ONG confirma recebimento)"""
        try:
            # Verificar se a doação pertence à ONG
            query_check = """
                SELECT d.id 
                FROM doacoes d
                JOIN necessidades n ON d.necessidade_id = n.id
                WHERE d.id = %s AND n.ong_id = %s AND d.status = 'pendente'
            """
            resultado = db.execute_query(query_check, (doacao_id, ong_id))
            
            if not resultado:
                return {'success': False, 'error': 'Doação não encontrada ou já confirmada'}
            
            # Confirmar doação
            query_update = """
                UPDATE doacoes 
                SET status = 'confirmada' 
                WHERE id = %s
            """
            db.execute_query(query_update, (doacao_id,))
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Erro ao confirmar doação: {e}")
            return {'success': False, 'error': str(e)}
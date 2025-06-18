from models import db, SolicitacaoCompra, ItemSolicitacaoCompra, Tarefa, CategoriaTarefa
from datetime import datetime

class SolicitacaoCompraService:
    @staticmethod
    def criar_solicitacao(solicitante_id, numero_atividade, nome_atividade, finalidade, justificativa_marca, itens):
        try:
            # Criar a solicitação
            solicitacao = SolicitacaoCompra(
                solicitante_id=solicitante_id,
                numero_atividade=numero_atividade,
                nome_atividade=nome_atividade,
                finalidade=finalidade,
                justificativa_marca=justificativa_marca
            )
            db.session.add(solicitacao)
            
            # Adicionar itens
            for item_data in itens:
                item_solicitacao = ItemSolicitacaoCompra(
                    item_id=item_data['id'],
                    quantidade=item_data['quantidade']
                )
                solicitacao.itens.append(item_solicitacao)
            
            # Criar tarefa associada
            categoria = CategoriaTarefa.query.filter_by(nome='Compras').first()
            if not categoria:
                categoria = CategoriaTarefa(nome='Compras', descricao='Tarefas relacionadas a compras')
                db.session.add(categoria)
            
            tarefa = Tarefa(
                titulo=f'Solicitação de Compra #{solicitacao.id}',
                categoria=categoria,
                resumo=f'Solicitação de compra realizada por {solicitacao.solicitante.nome}',
                solicitante_id=solicitante_id,
                prioridade='Média',
                status='Não iniciada'
            )
            db.session.add(tarefa)
            
            # Associar tarefa à solicitação
            solicitacao.tarefa = tarefa
            
            db.session.commit()
            return {'success': True, 'solicitacao': solicitacao}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def listar_minhas_solicitacoes(usuario_id):
        try:
            solicitacoes = SolicitacaoCompra.query.filter_by(
                solicitante_id=usuario_id
            ).order_by(SolicitacaoCompra.data_solicitacao.desc()).all()
            return {'success': True, 'solicitacoes': solicitacoes}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def obter_detalhes_solicitacao(solicitacao_id):
        try:
            solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
            return {'success': True, 'solicitacao': solicitacao}
        except Exception as e:
            return {'success': False, 'error': str(e)} 

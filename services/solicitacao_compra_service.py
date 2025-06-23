from models import db, SolicitacaoCompra, ItemSolicitacaoCompra, Tarefa, CategoriaTarefa, PainelContratacao
from datetime import datetime

class SolicitacaoCompraService:
    STATUS_CHOICES = [
        'Processo Iniciado',
        'Em andamento',
        'Concluído',
        'Aguardando Definições',
        'Cancelada'
    ]
    
    @staticmethod
    def criar_solicitacao(solicitante_id, numero_atividade, nome_atividade, finalidade, justificativa_marca, itens):
        try:
            # Criar a solicitação
            solicitacao = SolicitacaoCompra(
                solicitante_id=solicitante_id,
                numero_atividade=numero_atividade,
                nome_atividade=nome_atividade,
                finalidade=finalidade,
                justificativa_marca=justificativa_marca,
                status='Processo Iniciado'  # Definir status inicial explicitamente
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

    @staticmethod
    def atender_solicitacao(solicitacao_id, novo_status, dados_painel=None):
        """
        Atende uma solicitação de compra e opcionalmente cria um processo no painel
        """
        try:
            solicitacao = SolicitacaoCompra.query.get_or_404(solicitacao_id)
            
            if novo_status not in SolicitacaoCompraService.STATUS_CHOICES:
                raise ValueError("Status inválido")
                
            solicitacao.status = novo_status
            
            # Se fornecido dados do painel, cria ou atualiza o processo
            if dados_painel:
                if not solicitacao.painel_contratacao_id:
                    # Criar novo processo no painel
                    processo = PainelContratacao(
                        ano=datetime.now().year,
                        objeto=solicitacao.finalidade,
                        status=novo_status,
                        solicitante_id=solicitacao.solicitante_id,
                        # ... outros campos do painel ...
                    )
                    db.session.add(processo)
                    db.session.flush()  # Gera o ID
                    solicitacao.painel_contratacao_id = processo.id
                else:
                    # Atualiza processo existente
                    processo = solicitacao.painel_contratacao
                    processo.status = novo_status
                    # ... atualiza outros campos ...
            
            db.session.commit()
            return {'success': True, 'message': 'Solicitação atualizada com sucesso'}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)} 


from datetime import datetime
from models import db, RequisicaoMaterial, RequisicaoItem, Item, Tarefa, SaidaMaterial, SaidaItem, CategoriaTarefa, MovimentoEstoque
from sqlalchemy import desc
import logging

# Configuração do logger
logger = logging.getLogger(__name__)

class RequisicaoService:
    @staticmethod
    def criar_requisicao(solicitante_id, observacao, itens):
        """Cria uma nova requisição de material com seus itens"""
        try:
            # Buscar a categoria correta
            categoria = CategoriaTarefa.query.filter_by(nome='Requisição de Materiais').first()
            if not categoria:
                raise ValueError("Categoria 'Requisição de Materiais' não encontrada")

            # Criar a requisição
            requisicao = RequisicaoMaterial(
                solicitante_id=solicitante_id,
                observacao=observacao,
                status='PENDENTE'
            )
            db.session.add(requisicao)
            db.session.flush()  # Para obter o ID da requisição
            
            # Criar a tarefa associada
            tarefa = Tarefa(
                titulo=f"Requisição de Materiais #{requisicao.id}",
                resumo=f"Nova requisição de materiais",
                status="Não iniciada",
                prioridade="Alta",
                data_criacao=datetime.now(),
                solicitante_id=solicitante_id,
                categoria_id=5,  # ID fixo da categoria "Requisição de Materiais"
                quantidade_acoes=len(itens),
                observacoes=(
                    f"Requisição de materiais com {len(itens)} itens.\n\n"
                    f"Itens solicitados:\n" + 
                    "\n".join([f"- {item['nome']}: {item['quantidade']} unidades" for item in itens]) +
                    f"\n\nObservação do solicitante: {observacao}"
                )
            )
            db.session.add(tarefa)
            db.session.flush()
            
            # Associar tarefa à requisição
            requisicao.tarefa_id = tarefa.id
            
            # Criar os itens da requisição
            for item_data in itens:
                item = Item.query.get(item_data['id'])
                if not item:
                    raise ValueError(f"Item {item_data['id']} não encontrado")
                
                requisicao_item = RequisicaoItem(
                    requisicao_id=requisicao.id,
                    item_id=item_data['id'],
                    quantidade=item_data['quantidade']
                )
                db.session.add(requisicao_item)
            
            # Criar a saída pendente
            saida = SaidaMaterial(
                data_movimento=datetime.now().date(),
                solicitante_id=solicitante_id,
                usuario_id=solicitante_id,
                observacao=f"Saída pendente - Requisição #{requisicao.id}",
                numero_documento=f"REQ{requisicao.id:04d}/{datetime.now().year}",
                status='PENDENTE'
            )
            db.session.add(saida)
            db.session.flush()
            
            # Criar os itens da saída
            for item_data in itens:
                item = Item.query.get(item_data['id'])
                saida_item = SaidaItem(
                    saida_id=saida.id,
                    item_id=item_data['id'],
                    quantidade=item_data['quantidade'],
                    valor_unitario=item.valor_unitario
                )
                db.session.add(saida_item)
            
            # Associar saída à requisição
            requisicao.saida_id = saida.id
            
            db.session.commit()
            return {'success': True, 'requisicao_id': requisicao.id}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def listar_minhas_requisicoes(solicitante_id):
        """Lista as requisições do usuário atual"""
        try:
            requisicoes = RequisicaoMaterial.query\
                .filter_by(solicitante_id=solicitante_id)\
                .order_by(desc(RequisicaoMaterial.data_requisicao))\
                .all()
            
            return {'success': True, 'requisicoes': requisicoes}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def listar_requisicoes_pendentes():
        """Lista as requisições pendentes"""
        try:
            requisicoes = RequisicaoMaterial.query\
                .filter_by(status='PENDENTE')\
                .order_by(desc(RequisicaoMaterial.data_requisicao))\
                .all()
            
            return {'success': True, 'requisicoes': requisicoes}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def listar_requisicoes_atendidas():
        """Lista todas as requisições que foram atendidas"""
        try:
            requisicoes = RequisicaoMaterial.query\
                .filter_by(status='ATENDIDA')\
                .order_by(desc(RequisicaoMaterial.data_requisicao))\
                .all()
            
            # Em vez de atribuir a propriedade, vamos criar uma lista com os dados necessários
            requisicoes_com_estoque = []
            for req in requisicoes:
                # Verificar estoque suficiente
                tem_estoque = all(
                    item.quantidade <= item.item.estoque_atual 
                    for item in req.itens
                )
                # Adicionar a requisição e o status do estoque
                requisicoes_com_estoque.append({
                    'requisicao': req,
                    'tem_estoque_suficiente': tem_estoque
                })
            
            return {
                'success': True,
                'requisicoes': requisicoes_com_estoque
            }
        except Exception as e:
            logger.error(f"Erro ao listar requisições atendidas: {str(e)}")
            return {
                'success': False,
                'error': f"Erro ao listar requisições atendidas: {str(e)}"
            }
    
    @staticmethod
    def atender_requisicao(requisicao_id, usuario_id, tipo_atendimento='total'):
        """Atende uma requisição de material, permitindo atendimento parcial"""
        try:
            requisicao = RequisicaoMaterial.query.get_or_404(requisicao_id)
            
            if requisicao.status not in ['PENDENTE', 'PARCIALMENTE_ATENDIDA']:
                return {'success': False, 'error': 'Esta requisição não está em estado válido para atendimento'}
            
            # Atualizar a saída
            saida = requisicao.saida
            if not saida:
                return {'success': False, 'error': 'Saída não encontrada para esta requisição'}
            
            saida.usuario_id = usuario_id
            saida.data_movimento = datetime.now().date()
            
            # Variáveis para controle do atendimento
            itens_atendidos_total = 0
            itens_atendidos_parcial = 0
            total_itens = len(requisicao.itens)
            
            # Atualizar o estoque dos itens
            for req_item in requisicao.itens:
                item = req_item.item
                quantidade_pendente = req_item.quantidade - (req_item.quantidade_atendida or 0)
                
                if quantidade_pendente <= 0:
                    itens_atendidos_total += 1
                    continue
                
                # Se for atendimento parcial, atende o que tem em estoque
                # Se for total, só atende se tiver estoque suficiente
                if tipo_atendimento == 'parcial':
                    quantidade_possivel = min(quantidade_pendente, item.estoque_atual)
                else:
                    quantidade_possivel = quantidade_pendente if item.estoque_atual >= quantidade_pendente else 0
                
                if quantidade_possivel > 0:
                    # Atualizar estoque
                    item.estoque_atual -= quantidade_possivel
                    item.saldo_financeiro -= (quantidade_possivel * item.valor_unitario)
                    
                    # Atualizar quantidade atendida
                    req_item.quantidade_atendida = (req_item.quantidade_atendida or 0) + quantidade_possivel
                    
                    # Registrar movimento de estoque
                    movimento = MovimentoEstoque(
                        item_id=item.id,
                        tipo="SAIDA_REQUISICAO",
                        quantidade=quantidade_possivel,
                        usuario_id=usuario_id,
                        requisicao_item_id=req_item.id,
                        observacao=f"Atendimento {'Parcial' if tipo_atendimento == 'parcial' else 'Total'} Req. #{requisicao.id}",
                        saldo_anterior=item.estoque_atual + quantidade_possivel,
                        saldo_posterior=item.estoque_atual
                    )
                    db.session.add(movimento)
                    
                    # Contabilizar atendimento
                    if req_item.quantidade_atendida == req_item.quantidade:
                        itens_atendidos_total += 1
                    else:
                        itens_atendidos_parcial += 1
            
            # Determinar o status da requisição
            if itens_atendidos_total == total_itens:
                requisicao.status = 'ATENDIDA'
                saida.status = 'EFETIVADA'
                if requisicao.tarefa:
                    requisicao.tarefa.status = 'Concluída'
                    requisicao.tarefa.data_conclusao = datetime.now()
            elif itens_atendidos_total + itens_atendidos_parcial > 0:
                requisicao.status = 'PARCIALMENTE_ATENDIDA'
                saida.status = 'PARCIALMENTE_EFETIVADA'
                if requisicao.tarefa:
                    requisicao.tarefa.status = 'Em Andamento'
            
            requisicao.data_atendimento = datetime.now()
            
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def obter_detalhes_requisicao(requisicao_id):
        """Obtém os detalhes de uma requisição"""
        try:
            requisicao = RequisicaoMaterial.query.get(requisicao_id)
            if not requisicao:
                return {'success': False, 'error': 'Requisição não encontrada'}
            
            return {'success': True, 'requisicao': requisicao}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def cancelar_requisicao(requisicao_id, usuario_id):
        """Cancela uma requisição pendente"""
        try:
            requisicao = RequisicaoMaterial.query.get(requisicao_id)
            if not requisicao:
                return {'success': False, 'error': 'Requisição não encontrada'}
            
            if requisicao.status != 'PENDENTE':
                return {'success': False, 'error': 'Apenas requisições pendentes podem ser canceladas'}
            
            requisicao.status = 'CANCELADA'
            
            # Cancelar a saída associada
            if requisicao.saida:
                requisicao.saida.status = 'CANCELADA'
            
            # Atualizar status da tarefa
            if requisicao.tarefa:
                requisicao.tarefa.status = 'Cancelada'
                requisicao.tarefa.data_conclusao = datetime.now()
            
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}



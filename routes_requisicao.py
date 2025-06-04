from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, RequisicaoMaterial, RequisicaoItem, Item, Tarefa, SaidaMaterial, SaidaItem
from sqlalchemy import desc

requisicao_bp = Blueprint('requisicao_bp', __name__)

@requisicao_bp.route('/requisicao/consulta-estoque')
@login_required
def consulta_estoque():
    """Página para consulta de estoque e criação de requisição"""
    itens = Item.query.filter(Item.estoque_atual > 0).order_by(Item.nome).all()
    return render_template('almoxarifado/requisicao/consulta_estoque.html', itens=itens)

@requisicao_bp.route('/requisicao/nova', methods=['POST'])
@login_required
def nova_requisicao():
    """Cria uma nova requisição de material"""
    try:
        # Criar a requisição
        requisicao = RequisicaoMaterial(
            solicitante_id=current_user.id,
            observacao=request.form.get('observacao', '')
        )
        db.session.add(requisicao)
        db.session.flush()  # Para obter o ID da requisição

        # Processar itens
        itens = request.form.getlist('item_id[]')
        quantidades = request.form.getlist('quantidade[]')

        if not itens:
            raise ValueError("É necessário incluir pelo menos um item")

        for item_id, qtd in zip(itens, quantidades):
            if item_id and qtd:
                item = Item.query.get(item_id)
                if not item:
                    raise ValueError(f"Item {item_id} não encontrado")

                quantidade = int(qtd)
                if quantidade <= 0:
                    raise ValueError("Quantidade deve ser maior que zero")

                if item.estoque_atual < quantidade:
                    raise ValueError(f"Estoque insuficiente para o item {item.nome}")

                requisicao_item = RequisicaoItem(
                    requisicao_id=requisicao.id,
                    item_id=item_id,
                    quantidade=quantidade
                )
                db.session.add(requisicao_item)

        # Criar tarefa associada
        tarefa = Tarefa(
            titulo=f"Requisição de Materiais #{requisicao.id}",
            resumo=f"Nova requisição de materiais do solicitante {current_user.nome}",
            status="Não iniciada",
            prioridade="Alta",
            data_criacao=datetime.now(),
            solicitante_id=current_user.id,
            categoria_id=1,  # Categoria "Requisição de Materiais"
            unidade_local_id=current_user.unidade_local_id,
            quantidade_acoes=len(itens),
            observacoes=(
                f"Requisição de materiais com {len(itens)} itens.\n\n"
                f"Itens solicitados:\n" + 
                "\n".join([f"- {Item.query.get(item_id).nome}: {qtd} unidades" for item_id, qtd in zip(itens, quantidades)]) +
                f"\n\nObservação do solicitante: {request.form.get('observacao', '')}"
            )
        )
        db.session.add(tarefa)
        db.session.flush()

        # Associar tarefa à requisição
        requisicao.tarefa_id = tarefa.id
        
        db.session.commit()
        flash('Requisição registrada com sucesso!', 'success')
        return redirect(url_for('requisicao_bp.minhas_requisicoes'))

    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'error')
        return redirect(url_for('requisicao_bp.consulta_estoque'))
    except Exception as e:
        db.session.rollback()
        flash('Erro ao registrar requisição: ' + str(e), 'error')
        return redirect(url_for('requisicao_bp.consulta_estoque'))

@requisicao_bp.route('/requisicao/minhas')
@login_required
def minhas_requisicoes():
    """Lista as requisições do usuário atual"""
    requisicoes = RequisicaoMaterial.query\
        .filter_by(solicitante_id=current_user.id)\
        .order_by(desc(RequisicaoMaterial.data_requisicao))\
        .all()
    return render_template('almoxarifado/requisicao/minhas_requisicoes.html', requisicoes=requisicoes)

@requisicao_bp.route('/requisicao/pendentes')
@login_required
def requisicoes_pendentes():
    """Lista as requisições pendentes (para o almoxarifado)"""
    requisicoes = RequisicaoMaterial.query\
        .filter_by(status='PENDENTE')\
        .order_by(desc(RequisicaoMaterial.data_requisicao))\
        .all()
    return render_template('almoxarifado/requisicao/requisicoes_pendentes.html', requisicoes=requisicoes)

@requisicao_bp.route('/requisicao/<int:requisicao_id>/atender', methods=['POST'])
@login_required
def atender_requisicao(requisicao_id):
    """Atende uma requisição gerando uma saída de material"""
    try:
        requisicao = RequisicaoMaterial.query.get_or_404(requisicao_id)
        
        if requisicao.status != 'PENDENTE':
            raise ValueError("Esta requisição não está pendente")

        # Criar saída de material
        saida = SaidaMaterial(
            data_movimento=datetime.now().date(),
            solicitante_id=requisicao.solicitante_id,
            usuario_id=current_user.id,
            observacao=f"Atendimento da requisição #{requisicao.id}"
        )
        db.session.add(saida)
        db.session.flush()

        # Processar itens
        for req_item in requisicao.itens:
            item = req_item.item
            if item.estoque_atual < req_item.quantidade:
                raise ValueError(f"Estoque insuficiente para o item {item.nome}")

            saida_item = SaidaItem(
                saida_id=saida.id,
                item_id=req_item.item_id,
                quantidade=req_item.quantidade,
                valor_unitario=item.valor_unitario
            )
            db.session.add(saida_item)

            # Atualizar estoque
            item.estoque_atual -= req_item.quantidade
            item.saldo_financeiro -= (req_item.quantidade * item.valor_unitario)

        # Atualizar status da requisição
        requisicao.status = 'ATENDIDA'
        requisicao.saida_id = saida.id

        # Atualizar status da tarefa
        if requisicao.tarefa:
            requisicao.tarefa.status = 'Concluída'
            requisicao.tarefa.data_conclusao = datetime.now()

        db.session.commit()
        flash('Requisição atendida com sucesso!', 'success')
        return redirect(url_for('requisicao_bp.requisicoes_pendentes'))

    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'error')
        return redirect(url_for('requisicao_bp.requisicoes_pendentes'))
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atender requisição: ' + str(e), 'error')
        return redirect(url_for('requisicao_bp.requisicoes_pendentes')) 

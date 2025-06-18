from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.solicitacao_compra_service import SolicitacaoCompraService
from models import Item
import logging

solicitacao_compra_bp = Blueprint('solicitacao_compra_bp', __name__, url_prefix='/solicitacao-compra')

@solicitacao_compra_bp.route('/nova')
@login_required
def nova_solicitacao():
    """Página para criar nova solicitação de compra"""
    try:
        itens = Item.query.order_by(Item.nome).all()
        return render_template('solicitacao_compra/nova_solicitacao.html', 
                             itens=itens)
    except Exception as e:
        flash(f'Erro ao carregar página: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@solicitacao_compra_bp.route('/criar', methods=['POST'])
@login_required
def criar_solicitacao():
    """Cria uma nova solicitação de compra"""
    try:
        # Obter dados do formulário
        itens_ids = request.form.getlist('item_id[]')
        quantidades = request.form.getlist('quantidade[]')
        numero_atividade = request.form.get('numero_atividade')
        nome_atividade = request.form.get('nome_atividade')
        finalidade = request.form.get('finalidade')
        justificativa_marca = request.form.get('justificativa_marca')

        if not itens_ids:
            raise ValueError("É necessário incluir pelo menos um item")

        # Preparar lista de itens
        itens = []
        for item_id, qtd in zip(itens_ids, quantidades):
            if item_id and qtd:
                quantidade = int(qtd)
                if quantidade <= 0:
                    raise ValueError("Quantidade deve ser maior que zero")

                itens.append({
                    'id': item_id,
                    'quantidade': quantidade
                })

        # Criar solicitação
        result = SolicitacaoCompraService.criar_solicitacao(
            solicitante_id=current_user.id,
            numero_atividade=numero_atividade,
            nome_atividade=nome_atividade,
            finalidade=finalidade,
            justificativa_marca=justificativa_marca,
            itens=itens
        )

        if result['success']:
            flash('Solicitação de compra criada com sucesso!', 'success')
            return redirect(url_for('solicitacao_compra_bp.minhas_solicitacoes'))
        else:
            flash(f'Erro ao criar solicitação: {result["error"]}', 'error')
            return redirect(url_for('solicitacao_compra_bp.nova_solicitacao'))

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('solicitacao_compra_bp.nova_solicitacao'))
    except Exception as e:
        flash(f'Erro ao criar solicitação: {str(e)}', 'error')
        return redirect(url_for('solicitacao_compra_bp.nova_solicitacao'))

@solicitacao_compra_bp.route('/minhas')
@login_required
def minhas_solicitacoes():
    """Lista as solicitações do usuário atual"""
    try:
        result = SolicitacaoCompraService.listar_minhas_solicitacoes(current_user.id)
        if result['success']:
            return render_template('solicitacao_compra/minhas_solicitacoes.html', 
                                solicitacoes=result['solicitacoes'])
        else:
            flash(f'Erro ao listar solicitações: {result["error"]}', 'error')
            return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Erro ao listar solicitações: {str(e)}', 'error')
        return redirect(url_for('main.index')) 

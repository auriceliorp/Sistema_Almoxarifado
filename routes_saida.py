# routes_saida.py
# Rotas para movimentações de saída de materiais

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app_render import db
from models import Item, SaidaMaterial, SaidaItem
from datetime import date

saida_bp = Blueprint('saida_bp', __name__)

# ------------------------------ LISTA DE SAÍDAS ------------------------------ #
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    saidas = SaidaMaterial.query.order_by(SaidaMaterial.data_movimento.desc()).all()
    return render_template('lista_saida.html', saidas=saidas)

# ------------------------------ NOVA SAÍDA ------------------------------ #
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    itens = Item.query.all()

    if request.method == 'POST':
        data_movimento = request.form.get('data_movimento')
        numero_documento = request.form.get('numero_documento')
        observacao = request.form.get('observacao')

        nova_saida = SaidaMaterial(
            data_movimento=date.fromisoformat(data_movimento),
            numero_documento=numero_documento,
            observacao=observacao,
            usuario_id=current_user.id
        )

        # Adiciona a nova saída ao banco para gerar o ID
        db.session.add(nova_saida)
        db.session.flush()

        itens_ids = request.form.getlist('item_id[]')
        quantidades = request.form.getlist('quantidade[]')
        valores_unitarios = request.form.getlist('valor_unitario[]')

        for item_id, qtd_str, valor_str in zip(itens_ids, quantidades, valores_unitarios):
            if not qtd_str.strip():
                continue

            item = Item.query.get(int(item_id))
            quantidade = int(qtd_str)
            valor_unitario = float(valor_str.replace(',', '.'))

            # Verifica se há estoque suficiente
            if item.estoque_atual < quantidade:
                flash(f"Estoque insuficiente para o item '{item.nome}'. Disponível: {item.estoque_atual}, solicitado: {quantidade}", "danger")
                db.session.rollback()
                return redirect(url_for('saida_bp.nova_saida'))

            # Atualiza o estoque do item
            item.estoque_atual -= quantidade
            item.saldo_financeiro -= (quantidade * valor_unitario)

            saida_item = SaidaItem(
                item_id=item.id,
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                saida_id=nova_saida.id
            )
            db.session.add(saida_item)

        db.session.commit()
        flash("Saída registrada com sucesso!", "success")
        return redirect(url_for('saida_bp.lista_saidas'))

    return render_template('nova_saida.html', itens=itens)
# routes_estoque.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Estoque, Item

estoque_bp = Blueprint('estoque', __name__, url_prefix='/estoque')

@estoque_bp.route('/')
@login_required
def lista_estoque():
    estoques = Estoque.query.all()
    return render_template('lista_estoque.html', estoques=estoques)

@estoque_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_estoque():
    itens = Item.query.all()
    if request.method == 'POST':
        item_id = request.form['item_id']
        fornecedor = request.form['fornecedor']
        nota_fiscal = request.form['nota_fiscal']
        valor_unitario = float(request.form['valor_unitario'])
        quantidade = int(request.form['quantidade'])
        local = request.form['local']

        valor_total = valor_unitario * quantidade

        novo_estoque = Estoque(
            item_id=item_id,
            fornecedor=fornecedor,
            nota_fiscal=nota_fiscal,
            valor_unitario=valor_unitario,
            quantidade=quantidade,
            local=local,
            valor_total=valor_total
        )

        db.session.add(novo_estoque)
        db.session.commit()

        flash('Novo material cadastrado no estoque com sucesso!', 'success')
        return redirect(url_for('estoque.lista_estoque'))

    return render_template('novo_estoque.html', itens=itens)


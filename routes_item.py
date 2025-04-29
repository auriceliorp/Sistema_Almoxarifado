# routes_item.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Item, NaturezaDespesa

item_bp = Blueprint('item', __name__, url_prefix='/item')

@item_bp.route('/')
@login_required
def lista_item():
    itens = Item.query.all()
    return render_template('lista_item.html', itens=itens)

@item_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    naturezas = NaturezaDespesa.query.all()

    if request.method == 'POST':
        codigo = request.form['codigo']
        nome = request.form['nome']
        descricao = request.form['descricao']
        natureza_despesa_id = request.form['natureza_despesa_id']

        novo = Item(
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            natureza_despesa_id=natureza_despesa_id
        )
        db.session.add(novo)
        db.session.commit()
        flash('Item cadastrado com sucesso!', 'success')
        return redirect(url_for('item.lista_item'))

    return render_template('novo_item.html', naturezas=naturezas)


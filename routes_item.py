# routes_item.py corrigido

from flask import Blueprint, render_template, redirect, url_for, flash, request
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
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        natureza_despesa_id = request.form.get('natureza_despesa_id')

        novo_item = Item(codigo=codigo, nome=nome, natureza_despesa_id=natureza_despesa_id)
        db.session.add(novo_item)
        db.session.commit()

        flash('Item cadastrado com sucesso!')
        return redirect(url_for('item.lista_item'))

    return render_template('novo_item.html', naturezas=naturezas)

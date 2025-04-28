# routes_item.py atualizado

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
        natureza_despesa_id = request.form.get('natureza_despesa_id')

        novo_item = Item(codigo=codigo, nome=nome, natureza_despesa_id=natureza_despesa_id if natureza_despesa_id else None)
        db.session.add(novo_item)
        db.session.commit()

        flash('Item cadastrado com sucesso!')
        return redirect(url_for('item.lista_item'))

    return render_template('novo_item.html', naturezas=naturezas)

@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)
    naturezas = NaturezaDespesa.query.all()

    if request.method == 'POST':
        item.codigo = request.form['codigo']
        item.nome = request.form['nome']
        natureza_despesa_id = request.form.get('natureza_despesa_id')
        item.natureza_despesa_id = natureza_despesa_id if natureza_despesa_id else None

        db.session.commit()
        flash('Item atualizado com sucesso!')
        return redirect(url_for('item.lista_item'))

    return render_template('editar_item.html', item=item, naturezas=naturezas)

@item_bp.route('/excluir/<int:id>')
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()

    flash('Item excluído com sucesso!')
    return redirect(url_for('item.lista_item'))

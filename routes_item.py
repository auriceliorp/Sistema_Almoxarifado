# routes_item.py atualizado com editar e excluir
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Item, NaturezaDespesa
from database import db

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
        natureza_despesa_id = request.form['natureza_despesa_id'] or None

        novo = Item(codigo=codigo, nome=nome, descricao=descricao, natureza_despesa_id=natureza_despesa_id)
        db.session.add(novo)
        db.session.commit()
        flash('Item cadastrado com sucesso!')
        return redirect(url_for('item.lista_item'))

    return render_template('novo_item.html', naturezas=naturezas)

@item_bp.route('/editar/<int:item_id>', methods=['GET', 'POST'])
@login_required
def editar_item(item_id):
    item = Item.query.get_or_404(item_id)
    naturezas = NaturezaDespesa.query.all()
    if request.method == 'POST':
        item.codigo = request.form['codigo']
        item.nome = request.form['nome']
        item.descricao = request.form['descricao']
        item.natureza_despesa_id = request.form['natureza_despesa_id'] or None

        db.session.commit()
        flash('Item atualizado com sucesso!')
        return redirect(url_for('item.lista_item'))

    return render_template('editar_item.html', item=item, naturezas=naturezas)

@item_bp.route('/excluir/<int:item_id>')
@login_required
def excluir_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!')
    return redirect(url_for('item.lista_item'))

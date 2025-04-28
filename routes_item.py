# routes_item.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
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
        nd_id = request.form.get('nd_id')

        if not codigo or not nome or not nd_id:
            flash('Preencha todos os campos obrigatórios!')
            return redirect(url_for('item.novo_item'))

        novo_item = Item(
            codigo=codigo,
            nome=nome,
            nd_id=nd_id
        )
        db.session.add(novo_item)
        db.session.commit()
        flash('Item cadastrado com sucesso!')
        return redirect(url_for('item.lista_item'))
    
    return render_template('form_item.html', item=None, naturezas=naturezas)

@item_bp.route('/editar/<int:item_id>', methods=['GET', 'POST'])
@login_required
def editar_item(item_id):
    item = Item.query.get_or_404(item_id)
    naturezas = NaturezaDespesa.query.all()

    if request.method == 'POST':
        item.codigo = request.form.get('codigo')
        item.nome = request.form.get('nome')
        item.nd_id = request.form.get('nd_id')

        if not item.codigo or not item.nome or not item.nd_id:
            flash('Preencha todos os campos obrigatórios!')
            return redirect(url_for('item.editar_item', item_id=item_id))

        db.session.commit()
        flash('Item atualizado com sucesso!')
        return redirect(url_for('item.lista_item'))
    
    return render_template('form_item.html', item=item, naturezas=naturezas)

@item_bp.route('/excluir/<int:item_id>')
@login_required
def excluir_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!')
    return redirect(url_for('item.lista_item'))


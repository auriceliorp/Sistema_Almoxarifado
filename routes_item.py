from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from database import db
from models import Item, NaturezaDespesa

item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

@item_bp.route('/')
@login_required
def lista_itens():
    itens = Item.query.all()
    return render_template('lista_itens.html', itens=itens)

@item_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        unidade = request.form.get('unidade')
        natureza_despesa_id = request.form.get('natureza_despesa_id')

        if not all([codigo, nome, unidade, natureza_despesa_id]):
            flash('Preencha os campos obrigatórios: Código, Nome, Unidade de Medida e Natureza de Despesa.')
            return redirect(url_for('item_bp.novo_item'))

        novo = Item(
            codigo=codigo,
            nome=nome,
            descricao=descricao or '',
            unidade=unidade,
            natureza_despesa_id=natureza_despesa_id
        )
        db.session.add(novo)
        db.session.commit()
        flash('Item cadastrado com sucesso!')
        return redirect(url_for('item_bp.lista_itens'))

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.numero).all()
    return render_template('novo_item.html', naturezas=naturezas)

@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        item.codigo = request.form.get('codigo')
        item.nome = request.form.get('nome')
        item.descricao = request.form.get('descricao')
        item.unidade = request.form.get('unidade')
        item.natureza_despesa_id = request.form.get('natureza_despesa_id')

        if not all([item.codigo, item.nome, item.unidade, item.natureza_despesa_id]):
            flash('Preencha os campos obrigatórios: Código, Nome, Unidade de Medida e Natureza de Despesa.')
            return redirect(url_for('item_bp.editar_item', id=id))

        db.session.commit()
        flash('Item atualizado com sucesso!')
        return redirect(url_for('item_bp.lista_itens'))

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.numero).all()
    return render_template('editar_item.html', item=item, naturezas=naturezas)

@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!')
    return redirect(url_for('item_bp.lista_itens'))



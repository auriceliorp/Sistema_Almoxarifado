# routes_item.py atualizado
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from database import db
from models import Item, NaturezaDespesa  # adicione o import de NaturezaDespesa

item_bp = Blueprint('item', __name__, url_prefix='/item')

@item_bp.route('/')
@login_required
def lista_item():
    itens = Item.query.all()
    return render_template('lista_item.html', itens=itens)

@item_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    naturezas = NaturezaDespesa.query.all()  # <-- BUSCAR NDs cadastradas
    if request.method == 'POST':
        codigo = request.form['codigo']
        nome = request.form['nome']
        natureza_despesa_id = request.form.get('natureza_despesa_id')

        if not codigo or not nome:
            flash('Código e Nome são obrigatórios.')
        else:
            novo = Item(codigo=codigo, nome=nome, natureza_despesa_id=natureza_despesa_id)
            db.session.add(novo)
            db.session.commit()
            flash('Item cadastrado com sucesso!')
            return redirect(url_for('item.lista_item'))

    return render_template('novo_item.html', naturezas=naturezas)  # <-- envia NDs para a página


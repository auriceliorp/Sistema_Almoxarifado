from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required
from database import db
from models import Item, NaturezaDespesa
import pandas as pd

item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

# Lista de Itens com filtro por Natureza de Despesa
@item_bp.route('/itens')
@login_required
def lista_itens():
    nd_param = request.args.get('nd')
    nd_id = int(nd_param) if nd_param and nd_param.isdigit() else None

    if nd_id:
        itens = Item.query.filter_by(natureza_despesa_id=nd_id).all()
    else:
        itens = Item.query.all()

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.numero).all()
    return render_template('lista_itens.html', itens=itens, naturezas=naturezas, nd_selecionado=nd_id)

# Exportar Itens para Excel
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    nd_id = request.args.get('nd', type=int)
    if nd_id:
        itens = Item.query.filter_by(natureza_despesa_id=nd_id).all()
    else:
        itens = Item.query.all()

    dados = []
    for item in itens:
        dados.append({
            'Código': item.codigo,
            'Nome': item.nome,
            'Descrição': item.descricao,
            'Unidade': item.unidade,
            'Quantidade': item.quantidade or 0,
            'Valor Unitário': float(item.valor_unitario or 0),
            'Valor Total': float((item.quantidade or 0) * (item.valor_unitario or 0)),
            'Validade': item.data_validade.strftime('%d/%m/%Y') if item.data_validade else '',
            'ND': item.natureza.numero if item.natureza else ''
        })

    df = pd.DataFrame(dados)
    output = df.to_excel(index=False, engine='openpyxl')

    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=itens.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

# Formulário de Cadastro de Novo Item usando form_item.html
@item_bp.route('/form', methods=['GET', 'POST'])
@login_required
def form_item():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        unidade = request.form.get('unidade')
        natureza_despesa_id = request.form.get('natureza_despesa_id')

        if not all([codigo, nome, unidade, natureza_despesa_id]):
            flash('Preencha os campos obrigatórios: Código, Nome, Unidade de Medida e Natureza de Despesa.')
            return redirect(url_for('item_bp.form_item'))

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
    return render_template('form_item.html', naturezas=naturezas)

# Edição de Item
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

# Exclusão de Item
@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!')
    return redirect(url_for('item_bp.lista_itens'))

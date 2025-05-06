from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required
from database import db
from models import Item, Grupo, NaturezaDespesa
import pandas as pd
import io

item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

# Lista de Itens com filtro por ND
@item_bp.route('/itens')
@login_required
def lista_itens():
    nd_param = request.args.get('nd')
    nd_id = int(nd_param) if nd_param and nd_param.isdigit() else None

    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('lista_itens.html', itens=itens, naturezas=naturezas, nd_selecionado=nd_id)

# Exportar Itens para Excel
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    nd_id = request.args.get('nd', type=int)

    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    dados = []
    for item in itens:
        dados.append({
            'Código SAP': item.codigo_sap,
            'Código SIADS': item.codigo_siads,
            'Nome': item.nome,
            'Descrição': item.descricao,
            'Unidade': item.unidade,
            'Valor Unitário': item.valor_unitario,
            'Saldo Financeiro': item.saldo_financeiro,
            'Estoque Atual': item.estoque_atual,
            'Estoque Mínimo': item.estoque_minimo,
            'Localização': item.localizacao,
            'Grupo': item.grupo.nome if item.grupo else '',
            'ND': item.grupo.natureza_despesa.codigo if item.grupo and item.grupo.natureza_despesa else ''
        })

    df = pd.DataFrame(dados)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=itens.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response

# Formulário de Cadastro
@item_bp.route('/form', methods=['GET', 'POST'])
@login_required
def novo_item():
    if request.method == 'POST':
        codigo_sap = request.form.get('codigo_sap')
        codigo_siads = request.form.get('codigo_siads')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        unidade = request.form.get('unidade')
        grupo_id = request.form.get('grupo_id')
        valor_unitario = float(request.form.get('valor_unitario') or 0)
        saldo_financeiro = float(request.form.get('saldo_financeiro') or 0)
        estoque_atual = float(request.form.get('estoque_atual') or 0)
        estoque_minimo = float(request.form.get('estoque_minimo') or 0)
        localizacao = request.form.get('localizacao')

        if not all([codigo_sap, nome, unidade, grupo_id]):
            flash('Preencha os campos obrigatórios.')
            return redirect(url_for('item_bp.novo_item'))

        novo = Item(
            codigo_sap=codigo_sap,
            codigo_siads=codigo_siads,
            nome=nome,
            descricao=descricao or '',
            unidade=unidade,
            grupo_id=grupo_id,
            valor_unitario=valor_unitario,
            saldo_financeiro=saldo_financeiro,
            estoque_atual=estoque_atual,
            estoque_minimo=estoque_minimo,
            localizacao=localizacao
        )
        db.session.add(novo)
        db.session.commit()
        flash('Item cadastrado com sucesso!')
        return redirect(url_for('item_bp.lista_itens'))

    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template('form_item.html', grupos=grupos)

# Edição
@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        item.codigo_sap = request.form.get('codigo_sap')
        item.codigo_siads = request.form.get('codigo_siads')
        item.nome = request.form.get('nome')
        item.descricao = request.form.get('descricao')
        item.unidade = request.form.get('unidade')
        item.grupo_id = request.form.get('grupo_id')
        item.valor_unitario = float(request.form.get('valor_unitario') or 0)
        item.saldo_financeiro = float(request.form.get('saldo_financeiro') or 0)
        item.estoque_atual = float(request.form.get('estoque_atual') or 0)
        item.estoque_minimo = float(request.form.get('estoque_minimo') or 0)
        item.localizacao = request.form.get('localizacao')

        if not all([item.codigo_sap, item.nome, item.unidade, item.grupo_id]):
            flash('Preencha os campos obrigatórios.')
            return redirect(url_for('item_bp.editar_item', id=id))

        db.session.commit()
        flash('Item atualizado com sucesso!')
        return redirect(url_for('item_bp.lista_itens'))

    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template('editar_item.html', item=item, grupos=grupos)

# Exclusão
@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!')
    return redirect(url_for('item_bp.lista_itens'))

# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO  # Para arquivos em memória
import pandas as pd  # Para gerar Excel
from fpdf import FPDF  # Para gerar PDF
from datetime import datetime  # Para lidar com datas

# Importa os modelos do sistema
from models import db, Item, Grupo, NaturezaDespesa

# Criação do blueprint para o módulo de itens
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')


# ------------------------------ LISTAR ITENS ------------------------------
@item_bp.route('/itens')
@login_required
def lista_itens():
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    naturezas = NaturezaDespesa.query.all()
    nd_selecionado = int(nd_id) if nd_id else None

    return render_template('lista_itens.html', itens=itens, naturezas=naturezas, nd_selecionado=nd_selecionado)


# ------------------------------ CADASTRAR NOVO ITEM ------------------------------
@item_bp.route("/item/novo", methods=["GET", "POST"])
@login_required
def novo_item():
    form = ItemForm()

    grupos = GrupoItem.query.order_by(GrupoItem.nome).all()
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.nome).all()

    form.grupo_id.choices = [(g.id, f"{g.nome}") for g in grupos]
    form.natureza_despesa_id.choices = [(n.id, f"{n.codigo} - {n.nome}") for n in naturezas]

    if form.validate_on_submit():
        item = Item(
            codigo_sap=form.codigo_sap.data,
            codigo_siads=form.codigo_siads.data,
            nome=form.nome.data,
            descricao=form.descricao.data,
            unidade=form.unidade.data,
            grupo_id=form.grupo_id.data,
            natureza_despesa_id=form.natureza_despesa_id.data,
            valor_unitario=form.valor_unitario.data or 0,
            saldo_financeiro=0,
            estoque_atual=form.estoque_atual.data or 0,
            estoque_minimo=form.estoque_minimo.data or 0,
            localizacao=form.localizacao.data,
            data_validade=form.data_validade.data
        )
        db.session.add(item)
        db.session.commit()
        flash("Item cadastrado com sucesso!", "success")
        return redirect(url_for("item_bp.lista_itens"))

    return render_template("form_item.html", form=form)



# ------------------------------ EDITAR ITEM ------------------------------
@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        item.codigo_sap = request.form['codigo']
        item.codigo_siads = request.form['codigo_siads']
        item.nome = request.form['nome']
        item.descricao = request.form['descricao']
        item.unidade = request.form['unidade']
        item.grupo_id = request.form['grupo_id']
        item.valor_unitario = request.form.get('valor_unitario', type=float)
        item.estoque_atual = request.form.get('estoque_atual', type=float)
        item.estoque_minimo = request.form.get('estoque_minimo', type=float)
        item.localizacao = request.form['localizacao']
        data_validade_str = request.form.get('data_validade')
        item.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d') if data_validade_str else None

        db.session.commit()
        flash('Item atualizado com sucesso!', 'success')
        return redirect(url_for('item_bp.lista_itens'))

    grupos = Grupo.query.all()
    return render_template('form_item.html', item=item, grupos=grupos)


# ------------------------------ EXCLUIR ITENS ------------------------------
@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()

    flash('Item excluído com sucesso!', 'success')
    return redirect(url_for('item_bp.lista_itens'))


# ------------------------------ EXPORTAR PARA EXCEL ------------------------------
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    data = [{
        'Código SAP': item.codigo_sap,
        'Código SIADS': item.codigo_siads,
        'Nome': item.nome,
        'Descrição': item.descricao,
        'Unidade': item.unidade,
        'Grupo': item.grupo.nome if item.grupo else '',
        'Natureza de Despesa': item.grupo.natureza_despesa.nome if item.grupo and item.grupo.natureza_despesa else ''
    } for item in itens]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens')
    output.seek(0)

    return send_file(output, download_name="itens.xlsx", as_attachment=True)


# ------------------------------ EXPORTAR PARA PDF ------------------------------
@item_bp.route('/exportar_pdf')
@login_required
def exportar_pdf():
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for item in itens:
        grupo_nome = item.grupo.nome if item.grupo else ''
        nd_nome = item.grupo.natureza_despesa.nome if item.grupo and item.grupo.natureza_despesa else ''
        texto = f"{item.codigo_sap} - {item.nome} ({grupo_nome} / {nd_nome})"
        pdf.cell(0, 10, txt=texto, ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)

    return send_file(output, download_name="itens.pdf", as_attachment=True)

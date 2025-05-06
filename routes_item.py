from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from models import db, Item, NaturezaDespesa

item_bp = Blueprint('item_bp', __name__)

@item_bp.route('/item/itens')
@login_required
def lista_itens():
    nd_id = request.args.get('nd', type=int)
    if nd_id:
        itens = Item.query.filter_by(natureza_id=nd_id).all()
    else:
        itens = Item.query.all()
    naturezas = NaturezaDespesa.query.all()
    return render_template('lista_itens.html', itens=itens, naturezas=naturezas, nd_selecionado=nd_id)

@item_bp.route('/item/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    naturezas = NaturezaDespesa.query.all()
    if request.method == 'POST':
        item = Item(
            codigo_sap=request.form['codigo'],
            codigo_siads=request.form.get('codigo_siads'),
            nome=request.form['nome'],
            descricao=request.form.get('descricao'),
            unidade=request.form['unidade'],
            natureza_id=request.form['natureza_despesa_id'],
            valor_unitario=request.form.get('valor_unitario') or 0,
            estoque_atual=request.form.get('estoque_atual') or 0,
            estoque_minimo=request.form.get('estoque_minimo') or 0
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('item_bp.lista_itens'))
    return render_template('novo_item.html', naturezas=naturezas)

@item_bp.route('/item/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)
    naturezas = NaturezaDespesa.query.all()
    if request.method == 'POST':
        item.codigo_sap = request.form['codigo']
        item.codigo_siads = request.form.get('codigo_siads')
        item.nome = request.form['nome']
        item.descricao = request.form.get('descricao')
        item.unidade = request.form['unidade']
        item.natureza_id = request.form['natureza_despesa_id']
        item.valor_unitario = request.form.get('valor_unitario') or 0
        item.estoque_atual = request.form.get('estoque_atual') or 0
        item.estoque_minimo = request.form.get('estoque_minimo') or 0
        db.session.commit()
        return redirect(url_for('item_bp.lista_itens'))
    return render_template('editar_item.html', item=item, naturezas=naturezas)

@item_bp.route('/item/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('item_bp.lista_itens'))

@item_bp.route('/item/exportar_excel')
@login_required
def exportar_excel():
    nd_id = request.args.get('nd', type=int)
    if nd_id:
        itens = Item.query.filter_by(natureza_id=nd_id).all()
    else:
        itens = Item.query.all()

    data = [{
        'Código SAP': item.codigo_sap,
        'Código SIADS': item.codigo_siads,
        'Nome': item.nome,
        'Descrição': item.descricao,
        'Unidade': item.unidade,
        'Valor Unitário': item.valor_unitario,
        'Estoque Atual': item.estoque_atual,
        'Estoque Mínimo': item.estoque_minimo,
        'ND': item.natureza.nome if item.natureza else ''
    } for item in itens]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens')
    output.seek(0)

    return send_file(output, download_name='itens.xlsx', as_attachment=True)

@item_bp.route('/item/exportar_pdf')
@login_required
def exportar_pdf():
    nd_id = request.args.get('nd', type=int)
    if nd_id:
        itens = Item.query.filter_by(natureza_id=nd_id).all()
    else:
        itens = Item.query.all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Lista de Materiais/Serviços', ln=True, align='C')
    pdf.set_font('Arial', '', 10)

    for item in itens:
        pdf.cell(0, 10, txt=f"{item.codigo_sap} - {item.nome} ({item.unidade})", ln=True)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)

    return send_file(output, download_name='itens.pdf', as_attachment=True)

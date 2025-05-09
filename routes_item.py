# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from models import db, Item, Grupo, NaturezaDespesa

# Criação do blueprint
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

# ------------------------------ LISTAR ITENS ------------------------------
@item_bp.route('/itens')
@login_required
def lista_itens():
    nd_id = request.args.get('nd_id')
    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    naturezas_despesa = NaturezaDespesa.query.all()
    nd_selecionado = int(nd_id) if nd_id else None

    return render_template(
        'lista_itens.html',
        itens=itens,
        naturezas_despesa=naturezas_despesa,
        nd_selecionado=nd_selecionado
    )
    
# ------------------------------ DETALHAR ITEM ------------------------------
@item_bp.route('/detalhar/<int:id>')
@login_required
def detalhar_item(id):
    item = Item.query.get_or_404(id)
    return render_template('detalhar_item.html', item=item)

# ------------------------------ NOVO ITEM ------------------------------
@item_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    if request.method == 'POST':
        grupo = Grupo.query.get(int(request.form['grupo_id']))
        item = Item(
            codigo_sap=request.form['codigo'],
            codigo_siads=request.form['codigo_siads'],
            nome=request.form['nome'],
            descricao=request.form['descricao'],
            unidade=request.form['unidade'],
            grupo_id=grupo.id,
            natureza_despesa_id=grupo.natureza_despesa_id,
            valor_unitario=request.form.get('valor_unitario', type=float) or 0,
            saldo_financeiro=0,
            estoque_atual=request.form.get('estoque_atual', type=float) or 0,
            estoque_minimo=request.form.get('estoque_minimo', type=float) or 0,
            localizacao=request.form['localizacao'],
            data_validade=request.form.get('data_validade') or None
        )
        db.session.add(item)
        db.session.commit()
        flash('Item cadastrado com sucesso!', 'success')
        return redirect(url_for('item_bp.lista_itens'))

    grupos = Grupo.query.all()
    return render_template('form_item.html', grupos=grupos)

# ------------------------------ EDITAR ITEM ------------------------------
@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        grupo = Grupo.query.get(int(request.form['grupo_id']))
        item.codigo_sap = request.form['codigo']
        item.codigo_siads = request.form['codigo_siads']
        item.nome = request.form['nome']
        item.descricao = request.form['descricao']
        item.unidade = request.form['unidade']
        item.grupo_id = grupo.id
        item.natureza_despesa_id = grupo.natureza_despesa_id
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

# ------------------------------ EXCLUIR ITEM ------------------------------
@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item excluído com sucesso!', 'success')
    return redirect(url_for('item_bp.lista_itens'))

# ------------------------------ EXPORTAR EXCEL ------------------------------
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

# ------------------------------ EXPORTAR PDF ------------------------------
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

    pdf_bytes = BytesIO(pdf.output(dest='S').encode('latin1'))
    pdf_bytes.seek(0)

    # ------------------------------ DETALHAR ITEM ------------------------------
@item_bp.route('/detalhes/<int:id>')
@login_required
def detalhes_item(id):
    # Busca o item pelo ID
    item = Item.query.get_or_404(id)

    return render_template('detalhes_item.html', item=item)


    return send_file(pdf_bytes, download_name="itens.pdf", as_attachment=True)

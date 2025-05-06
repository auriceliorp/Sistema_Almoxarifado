from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from models import db, Item, GrupoItem, NaturezaDespesa

item_bp = Blueprint('item', __name__)

@item_bp.route('/item/itens')
@login_required
def lista_itens():
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(GrupoItem).filter(GrupoItem.natureza_id == nd_id).all()
    else:
        itens = Item.query.all()
    return render_template('itens.html', itens=itens)

@item_bp.route('/item/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    if request.method == 'POST':
        codigo = request.form['codigo']
        nome = request.form['nome']
        descricao = request.form['descricao']
        grupo_id = request.form['grupo_id']

        item = Item(codigo=codigo, nome=nome, descricao=descricao, grupo_id=grupo_id)
        db.session.add(item)
        db.session.commit()
        flash('Item cadastrado com sucesso!', 'success')
        return redirect(url_for('item.lista_itens'))

    grupos = GrupoItem.query.all()
    return render_template('form_item.html', grupos=grupos)

@item_bp.route('/item/exportar_excel')
@login_required
def exportar_excel():
    itens = Item.query.all()
    data = [{
        'Código': item.codigo,
        'Nome': item.nome,
        'Descrição': item.descricao,
        'Grupo': item.grupo.nome if item.grupo else '',
        'ND': item.grupo.natureza.nome if item.grupo and item.grupo.natureza else ''
    } for item in itens]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens')
    output.seek(0)

    return send_file(output, download_name="itens.xlsx", as_attachment=True)

@item_bp.route('/item/exportar_pdf')
@login_required
def exportar_pdf():
    itens = Item.query.all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for item in itens:
        grupo_nome = item.grupo.nome if item.grupo else ''
        nd_nome = item.grupo.natureza.nome if item.grupo and item.grupo.natureza else ''
        pdf.cell(0, 10, txt=f"{item.codigo} - {item.nome} ({grupo_nome} / {nd_nome})", ln=True)

    output = BytesIO()
    pdf.output(output, 'F')
    output.seek(0)

    return send_file(output, download_name="itens.pdf", as_attachment=True)

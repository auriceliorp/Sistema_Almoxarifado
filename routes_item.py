# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_login import login_required
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from models import db, Item, Grupo, NaturezaDespesa
import os

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
@item_bp.route('/detalhes/<int:id>')
@login_required
def detalhes_item(id):
    item = Item.query.get_or_404(id)
    return render_template('detalhar_item.html', item=item)

# ------------------------------ NOVO ITEM ------------------------------
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
    return render_template('form_item.html', grupos=grupos, item={})


# ------------------------------ EDITAR ITEM ------------------------------
@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        try:
            grupo = Grupo.query.get(int(request.form['grupo_id']))
            item.codigo_sap = request.form['codigo']
            item.codigo_siads = request.form.get('codigo_siads')
            item.nome = request.form['nome']
            item.descricao = request.form['descricao']
            item.unidade = request.form['unidade']
            item.grupo_id = grupo.id
            item.natureza_despesa_id = grupo.natureza_despesa_id
            item.estoque_minimo = request.form.get('estoque_minimo', type=float)
            item.localizacao = request.form.get('localizacao')

            data_validade_str = request.form.get('data_validade')
            if data_validade_str:
                item.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d')
            else:
                item.data_validade = None

            db.session.commit()
            flash('Item atualizado com sucesso!', 'success')
            return redirect(url_for('item_bp.lista_itens'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar item: {str(e)}', 'danger')

    grupos = Grupo.query.all()
    return render_template('editar_item.html', item=item, grupos=grupos)

# ------------------------------ EXCLUIR ITEM ------------------------------
@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)

    if item.estoque_atual > 0 or item.saldo_financeiro > 0:
        flash('Não é possível excluir o item enquanto houver saldo em estoque.', 'danger')
        return redirect(url_for('item_bp.lista_itens'))

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

# ------------------------------ EXPORTAR PDF PERSONALIZADO ------------------------------
class PDFItens(FPDF):
    def header(self):
        logo_path = os.path.join('static', 'embrapa_logo.png')
        self.image(logo_path, 10, 8, 50)
        self.set_xy(65, 10)
        self.set_fill_color(13, 110, 253)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.cell(135, 10, 'Relatório de Itens Cadastrados', border=0, ln=True, align='C', fill=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 0, 'C')

    def tabela_itens(self, dados):
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(220, 220, 220)
        headers = ['SAP', 'SIADS', 'Nome', 'Unidade', 'Estoque', 'Unit. R$', 'Saldo R$']
        col_widths = [20, 20, 65, 20, 18, 22, 25]

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, border=1, align='C', fill=True)
        self.ln()

        self.set_font('Arial', '', 9)
        self.set_text_color(0)
        for item in dados:
            self.cell(col_widths[0], 8, item.codigo_sap, border=1)
            self.cell(col_widths[1], 8, item.codigo_siads or '', border=1)
            self.cell(col_widths[2], 8, item.nome[:38], border=1)
            self.cell(col_widths[3], 8, item.unidade, border=1, align='C')
            self.cell(col_widths[4], 8, str(item.estoque_atual), border=1, align='C')
            self.cell(col_widths[5], 8, f"{item.valor_unitario:.2f}", border=1, align='R')
            self.cell(col_widths[6], 8, f"{item.saldo_financeiro:.2f}", border=1, align='R')
            self.ln()

@item_bp.route('/exportar_pdf')
@login_required
def exportar_pdf():
    try:
        itens = Item.query.order_by(Item.nome.asc()).all()

        pdf = PDFItens()
        pdf.add_page()
        pdf.tabela_itens(itens)

        caminho = "relatorio_itens.pdf"
        pdf.output(caminho)
        return send_file(caminho, as_attachment=True)

    except Exception as e:
        print("Erro ao gerar PDF:", str(e))
        flash("Erro ao gerar PDF", "danger")
        return redirect(url_for('item_bp.lista_itens'))

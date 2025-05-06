# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO  # Para arquivos em memória
import pandas as pd  # Para gerar Excel
from fpdf import FPDF  # Para gerar PDF

# Importa os modelos do sistema
from models import db, Item, Grupo, NaturezaDespesa  # Corrigido: GrupoItem -> Grupo

# Criação do blueprint para o módulo de itens
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')


# ------------------------------ LISTAR ITENS ------------------------------
@item_bp.route('/itens')  # URL completa: /item/itens
@login_required
def lista_itens():
    # Verifica se há um filtro por natureza de despesa (nd)
    nd_id = request.args.get('nd')
    if nd_id:
        # Filtra itens com base na natureza vinculada ao grupo
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        # Caso contrário, retorna todos os itens
        itens = Item.query.all()

    return render_template('lista_itens.html', itens=itens)


# ------------------------------ CADASTRAR NOVO ITEM ------------------------------
@item_bp.route('/novo', methods=['GET', 'POST'])  # URL: /item/novo
@login_required
def novo_item():
    if request.method == 'POST':
        # Obtém dados do formulário
        codigo = request.form['codigo']
        nome = request.form['nome']
        descricao = request.form['descricao']
        grupo_id = request.form['grupo_id']

        # Cria o novo item
        item = Item(codigo_sap=codigo, nome=nome, descricao=descricao, grupo_id=grupo_id)
        db.session.add(item)
        db.session.commit()

        flash('Item cadastrado com sucesso!', 'success')
        return redirect(url_for('item_bp.lista_itens'))

    # Para método GET, exibe formulário com lista de grupos
    grupos = Grupo.query.all()
    return render_template('form_item.html', grupos=grupos)


# ------------------------------ EXPORTAR PARA EXCEL ------------------------------
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    itens = Item.query.all()

    # Estrutura de dados para exportação
    data = [{
        'Código SAP': item.codigo_sap,
        'Nome': item.nome,
        'Descrição': item.descricao,
        'Grupo': item.grupo.nome if item.grupo else '',
        'Natureza de Despesa': item.grupo.natureza_despesa.nome if item.grupo and item.grupo.natureza_despesa else ''
    } for item in itens]

    df = pd.DataFrame(data)

    # Salva Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens')
    output.seek(0)

    return send_file(output, download_name="itens.xlsx", as_attachment=True)


# ------------------------------ EXPORTAR PARA PDF ------------------------------
@item_bp.route('/exportar_pdf')
@login_required
def exportar_pdf():
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
    pdf.output(output, 'F')
    output.seek(0)

    return send_file(output, download_name="itens.pdf", as_attachment=True)

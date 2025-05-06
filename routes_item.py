# Importações principais do Flask
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required  # Garante que o usuário esteja autenticado
from io import BytesIO  # Para manipular arquivos em memória (PDF, Excel)
import pandas as pd  # Biblioteca para manipulação de dados em Excel
from fpdf import FPDF  # Biblioteca para gerar arquivos PDF

# Importa os modelos necessários
from models import db, Item, GrupoItem, NaturezaDespesa  # Certifique-se de ter GrupoItem no seu models.py

# Criação do blueprint para rotas do módulo de itens
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')


# ------------------------------ LISTAR ITENS ------------------------------
@item_bp.route('/itens')  # Acessível em /item/itens
@login_required  # Só acessível se o usuário estiver logado
def lista_itens():
    # Filtra os itens por natureza de despesa, se o parâmetro 'nd' for passado na URL
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(GrupoItem).filter(GrupoItem.natureza_id == nd_id).all()
    else:
        itens = Item.query.all()
    
    # Renderiza a página com os itens encontrados
    return render_template('lista_itens.html', itens=itens)


# ------------------------------ NOVO ITEM ------------------------------
@item_bp.route('/novo', methods=['GET', 'POST'])  # Acessível em /item/novo
@login_required
def novo_item():
    if request.method == 'POST':
        # Coleta os dados enviados pelo formulário
        codigo = request.form['codigo']
        nome = request.form['nome']
        descricao = request.form['descricao']
        grupo_id = request.form['grupo_id']  # ID do grupo associado

        # Cria e salva o novo item no banco de dados
        item = Item(codigo=codigo, nome=nome, descricao=descricao, grupo_id=grupo_id)
        db.session.add(item)
        db.session.commit()

        # Mensagem de sucesso e redireciona para a lista
        flash('Item cadastrado com sucesso!', 'success')
        return redirect(url_for('item_bp.lista_itens'))

    # Se for GET, renderiza o formulário com os grupos disponíveis
    grupos = GrupoItem.query.all()
    return render_template('form_item.html', grupos=grupos)


# ------------------------------ EXPORTAR PARA EXCEL ------------------------------
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    # Busca todos os itens
    itens = Item.query.all()

    # Monta a estrutura de dados para o DataFrame
    data = [{
        'Código': item.codigo,
        'Nome': item.nome,
        'Descrição': item.descricao,
        'Grupo': item.grupo.nome if item.grupo else '',
        'ND': item.grupo.natureza.nome if item.grupo and item.grupo.natureza else ''
    } for item in itens]

    # Converte para DataFrame
    df = pd.DataFrame(data)

    # Cria arquivo Excel em memória
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Itens')
    output.seek(0)  # Move o ponteiro para o início do arquivo

    # Envia o arquivo para download
    return send_file(output, download_name="itens.xlsx", as_attachment=True)


# ------------------------------ EXPORTAR PARA PDF ------------------------------
@item_bp.route('/exportar_pdf')
@login_required
def exportar_pdf():
    # Busca todos os itens
    itens = Item.query.all()

    # Inicia o PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Adiciona uma linha para cada item
    for item in itens:
        grupo_nome = item.grupo.nome if item.grupo else ''
        nd_nome = item.grupo.natureza.nome if item.grupo and item.grupo.natureza else ''
        texto = f"{item.codigo} - {item.nome} ({grupo_nome} / {nd_nome})"
        pdf.cell(0, 10, txt=texto, ln=True)

    # Salva o PDF em memória
    output = BytesIO()
    pdf.output(output, 'F')
    output.seek(0)

    # Envia o PDF para download
    return send_file(output, download_name="itens.pdf", as_attachment=True)

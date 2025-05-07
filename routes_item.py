# ------------------------------ IMPORTAÇÕES ------------------------------
# Importações das bibliotecas Flask, extensões e utilitários usados
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO  # Para manipulação de arquivos temporários na memória
import pandas as pd      # Para exportar planilhas Excel
from fpdf import FPDF    # Para gerar relatórios PDF
from datetime import datetime  # Para manipular datas

# Importação dos modelos do banco de dados
from models import db, Item, Grupo, NaturezaDespesa

# Criação de um Blueprint para o módulo de cadastro de Itens
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

# ------------------------------ LISTAR ITENS ------------------------------
@item_bp.route('/itens')
@login_required
def lista_itens():
    # Permite filtragem por Natureza de Despesa (via Grupo)
    nd_id = request.args.get('nd')
    if nd_id:
        # Consulta itens cujo grupo está vinculado à ND filtrada
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    # Lista todas as Naturezas para exibir no filtro
    naturezas = NaturezaDespesa.query.all()
    nd_selecionado = int(nd_id) if nd_id else None

    return render_template('lista_itens.html', itens=itens, naturezas=naturezas, nd_selecionado=nd_selecionado)

# ------------------------------ CADASTRAR NOVO ITEM ------------------------------
@item_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    if request.method == 'POST':
        # Recupera o Grupo selecionado no formulário
        grupo = Grupo.query.get(int(request.form['grupo_id']))
        
        # Cria um novo Item, herdando a ND do grupo selecionado
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

    # GET: Exibe o formulário com lista de Grupos (ND é herdada)
    grupos = Grupo.query.all()
    return render_template('form_item.html', grupos=grupos)



# ------------------------------ EDITAR ITEM ------------------------------
@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        # Atualiza o grupo e herda a ND correspondente
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

    # GET: Carrega dados do item e lista de grupos
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


# ------------------------------ EXPORTAR PARA EXCEL ------------------------------
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    # Exporta os dados dos itens, filtrados ou não por ND
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    # Prepara os dados para exportação
    data = [{
        'Código SAP': item.codigo_sap,
        'Código SIADS': item.codigo_siads,
        'Nome': item.nome,
        'Descrição': item.descricao,
        'Unidade': item.unidade,
        'Grupo': item.grupo.nome if item.grupo else '',
        'Natureza de Despesa': item.grupo.natureza_despesa.nome if item.grupo and item.grupo.natureza_despesa else ''
    } for item in itens]

    # Cria e retorna o arquivo Excel
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
    # Exporta os dados para PDF, com filtragem por ND (se houver)
    nd_id = request.args.get('nd')
    if nd_id:
        itens = Item.query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id).all()
    else:
        itens = Item.query.all()

    # Geração do PDF com lista dos itens
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


    return send_file(output, download_name="itens.pdf", as_attachment=True)

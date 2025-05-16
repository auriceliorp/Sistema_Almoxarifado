# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from models import db, Item, Grupo, NaturezaDespesa
import os

# Criação do blueprint
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

# ------------------------------ LISTAR ITENS COM PAGINAÇÃO E FILTROS ------------------------------
@item_bp.route('/itens')
@login_required
def lista_itens():
    filtro = request.args.get('filtro')  # Tipo de filtro (sap, descricao, grupo, nd)
    busca = request.args.get('busca')    # Valor buscado
    nd_id = request.args.get('nd_id')    # Natureza de despesa selecionada
    page = request.args.get('page', 1, type=int)  # Página atual

    query = Item.query

    # Filtro por ND
    if nd_id:
        query = query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id)

    # Filtros adicionais
    if filtro and busca:
        busca = busca.lower()
        if filtro == 'sap':
            query = query.filter(Item.codigo_sap.ilike(f'%{busca}%'))
        elif filtro == 'descricao':
            query = query.filter(Item.nome.ilike(f'%{busca}%'))
        elif filtro == 'grupo':
            query = query.join(Grupo).filter(Grupo.nome.ilike(f'%{busca}%'))
        elif filtro == 'nd':
            query = query.join(NaturezaDespesa).filter(NaturezaDespesa.codigo.ilike(f'%{busca}%'))

    # Aplica paginação
    itens = query.order_by(Item.nome.asc()).paginate(page=page, per_page=10)

    # Naturezas para filtro
    naturezas_despesa = NaturezaDespesa.query.all()
    nd_selecionado = int(nd_id) if nd_id else None

    return render_template(
        'lista_itens.html',
        itens=itens,
        naturezas_despesa=naturezas_despesa,
        nd_selecionado=nd_selecionado,
        filtro=filtro,
        busca=busca
    )

# As demais rotas (novo_item, editar_item, excluir_item, exportar_pdf, exportar_excel) permanecem inalteradas

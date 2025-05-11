routes_relatorio.py

Relatório de Mapa de Fechamento Mensal por ND

from flask import Blueprint, render_template, request from flask_login import login_required from sqlalchemy import extract, func from app_render import db from models import NaturezaDespesa, EntradaItem, SaidaItem, Item, Grupo from datetime import datetime

relatorio_bp = Blueprint('relatorio_bp', name, template_folder='templates')

@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET']) @login_required def mapa_fechamento(): # Obtém mês e ano do filtro ou usa o mês/ano atual mes = request.args.get('mes', default=None, type=int) ano = request.args.get('ano', default=None, type=int)

# Lista de anos disponíveis (a partir de dados ou fixo)
anos_disponiveis = [ano[0] for ano in db.session.query(func.extract('year', EntradaItem.data_movimento)).distinct()]
anos_disponiveis = sorted(list(set(anos_disponiveis + [datetime.now().year])))

# Recupera todas as ND
nds = NaturezaDespesa.query.order_by(NaturezaDespesa.nome).all()
relatorio = []

# Inicializa totais gerais
total_inicial = 0
total_entradas = 0
total_saidas = 0
total_final = 0

for nd in nds:
    # Somatório de entradas no mês selecionado
    entradas_query = db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0))\
        .join(Item, EntradaItem.item_id == Item.id)\
        .join(Grupo, Item.grupo_id == Grupo.id)\
        .filter(Grupo.natureza_despesa_id == nd.id)

    if mes:
        entradas_query = entradas_query.filter(extract('month', EntradaItem.data_movimento) == mes)
    if ano:
        entradas_query = entradas_query.filter(extract('year', EntradaItem.data_movimento) == ano)

    entradas = entradas_query.scalar() or 0

    # Somatório de saídas no mês selecionado
    saidas_query = db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0))\
        .join(Item, SaidaItem.item_id == Item.id)\
        .join(Grupo, Item.grupo_id == Grupo.id)\
        .filter(Grupo.natureza_despesa_id == nd.id)

    if mes:
        saidas_query = saidas_query.filter(extract('month', SaidaItem.data_movimento) == mes)
    if ano:
        saidas_query = saidas_query.filter(extract('year', SaidaItem.data_movimento) == ano)

    saidas = saidas_query.scalar() or 0

    saldo_inicial = 0  # futura lógica poderá trazer saldos acumulados anteriores
    saldo_final = saldo_inicial + entradas - saidas

    relatorio.append({
        'nd': nd.nome,
        'inicial': saldo_inicial,
        'entradas': entradas,
        'saidas': saidas,
        'final': saldo_final
    })

    total_inicial += saldo_inicial
    total_entradas += entradas
    total_saidas += saidas
    total_final += saldo_final

return render_template('mapa_fechamento.html',
                       relatorio=relatorio,
                       mes=mes,
                       ano=ano,
                       anos_disponiveis=anos_disponiveis,
                       total_inicial=total_inicial,
                       total_entradas=total_entradas,
                       total_saidas=total_saidas,
                       total_final=total_final)


routes_relatorio.py

Rotas relacionadas ao relatório "Mapa de Fechamento Mensal"

from flask import Blueprint, render_template, request from flask_login import login_required from app_render import db from models import NaturezaDespesa, Grupo, Item, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial from sqlalchemy import extract, func

Criação do blueprint

relatorio_bp = Blueprint('relatorio_bp', name, template_folder='templates')

------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------

@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET']) @login_required def mapa_fechamento(): # Coleta mês e ano dos parâmetros ou usa o mês atual como padrão from datetime import datetime hoje = datetime.today() mes = int(request.args.get('mes', hoje.month)) ano = int(request.args.get('ano', hoje.year))

# Coleta todas as Naturezas de Despesa
nds = NaturezaDespesa.query.all()
dados = []

total_inicial = total_entradas = total_saidas = 0

for nd in nds:
    # Obtém os grupos associados a essa ND
    grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
    grupo_ids = [g.id for g in grupos]

    # Obtém os itens associados aos grupos dessa ND
    itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
    item_ids = [i.id for i in itens]

    # Entradas no mês
    entradas_q = db.session.query(
        func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0)
    ).join(EntradaMaterial).filter(
        EntradaItem.item_id.in_(item_ids),
        extract('month', EntradaMaterial.data_movimento) == mes,
        extract('year', EntradaMaterial.data_movimento) == ano
    ).scalar()

    # Saídas no mês
    saidas_q = db.session.query(
        func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0)
    ).join(SaidaMaterial).filter(
        SaidaItem.item_id.in_(item_ids),
        extract('month', SaidaMaterial.data_movimento) == mes,
        extract('year', SaidaMaterial.data_movimento) == ano
    ).scalar()

    # Saldo final atual da ND
    saldo_final = nd.valor or 0

    # Saldo inicial = final - entradas + saídas
    saldo_inicial = saldo_final - entradas_q + saidas_q

    dados.append({
        'nd': nd,
        'saldo_inicial': saldo_inicial,
        'entradas': entradas_q,
        'saidas': saidas_q,
        'saldo_final': saldo_final
    })

    total_inicial += saldo_inicial
    total_entradas += entradas_q
    total_saidas += saidas_q

total_final = total_inicial + total_entradas - total_saidas

return render_template(
    'mapa_fechamento.html',
    dados=dados,
    mes=mes,
    ano=ano,
    total_inicial=total_inicial,
    total_entradas=total_entradas,
    total_saidas=total_saidas,
    total_final=total_final
)


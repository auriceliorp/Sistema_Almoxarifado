# routes_relatorio.py
# Gera o Mapa de Fechamento Mensal por Natureza de Despesa

from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import datetime, date
from app_render import db
from models import NaturezaDespesa, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, Item, Grupo

relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')


# ------------------------ ROTA: Mapa de Fechamento Mensal ------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    # Coleta parâmetros de filtro de mês e ano
    ano = request.args.get('ano', type=int)
    mes = request.args.get('mes', type=int)

    # Se não informados, usa o mês atual
    hoje = date.today()
    ano = ano or hoje.year
    mes = mes or hoje.month

    # Define datas do início e fim do mês
    data_inicio_mes = date(ano, mes, 1)
    if mes == 12:
        data_fim_mes = date(ano + 1, 1, 1)
    else:
        data_fim_mes = date(ano, mes + 1, 1)

    # Consulta todas as ND existentes
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    resultados = []
    total_entradas = total_saidas = total_saldo_inicial = total_saldo_final = 0.0

    for nd in naturezas:
        # Encontra grupos vinculados a essa ND
        grupos = Grupo.query.filter_by(natureza_id=nd.id).all()
        grupo_ids = [g.id for g in grupos]

        # Encontra itens pertencentes a esses grupos
        itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
        item_ids = [item.id for item in itens]

        # Entradas e saídas do mês
        entradas_mes = db.session.query(db.func.coalesce(db.func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0.0))\
            .join(EntradaMaterial).filter(
                EntradaItem.item_id.in_(item_ids),
                EntradaMaterial.data_movimento >= data_inicio_mes,
                EntradaMaterial.data_movimento < data_fim_mes
            ).scalar()

        saidas_mes = db.session.query(db.func.coalesce(db.func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0.0))\
            .join(SaidaMaterial).filter(
                SaidaItem.item_id.in_(item_ids),
                SaidaMaterial.data_movimento >= data_inicio_mes,
                SaidaMaterial.data_movimento < data_fim_mes
            ).scalar()

        # Entradas e saídas anteriores (para saldo inicial)
        entradas_anteriores = db.session.query(db.func.coalesce(db.func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0.0))\
            .join(EntradaMaterial).filter(
                EntradaItem.item_id.in_(item_ids),
                EntradaMaterial.data_movimento < data_inicio_mes
            ).scalar()

        saidas_anteriores = db.session.query(db.func.coalesce(db.func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0.0))\
            .join(SaidaMaterial).filter(
                SaidaItem.item_id.in_(item_ids),
                SaidaMaterial.data_movimento < data_inicio_mes
            ).scalar()

        # Converte valores para float para evitar erro Decimal - float
        saldo_inicial = float(entradas_anteriores) - float(saidas_anteriores)
        entradas_mes = float(entradas_mes)
        saidas_mes = float(saidas_mes)
        saldo_final = saldo_inicial + entradas_mes - saidas_mes

        # Soma para totalizador geral
        total_entradas += entradas_mes
        total_saidas += saidas_mes
        total_saldo_inicial += saldo_inicial
        total_saldo_final += saldo_final

        resultados.append({
            'nd': nd.codigo,
            'nome': nd.nome,
            'saldo_inicial': saldo_inicial,
            'entradas': entradas_mes,
            'saidas': saidas_mes,
            'saldo_final': saldo_final
        })

    return render_template('mapa_fechamento.html',
                           resultados=resultados,
                           ano=ano,
                           mes=mes,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           total_saldo_inicial=total_saldo_inicial,
                           total_saldo_final=total_saldo_final)
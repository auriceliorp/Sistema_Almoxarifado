# routes_relatorio.py
# Gera o Mapa de Fechamento Mensal por Natureza de Despesa

from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import datetime, date
from app_render import db
from models import NaturezaDespesa, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, Item

relatorio_bp = Blueprint('relatorio_bp', __name__)

# ---------------- ROTA: Mapa de Fechamento Mensal ---------------- #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    # Obtém mês e ano da URL, ou usa mês atual
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)

    hoje = date.today()
    if not mes:
        mes = hoje.month
    if not ano:
        ano = hoje.year

    # Calcula intervalo de datas
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)

    # Consulta todas as naturezas de despesa ordenadas pelo código
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    resultado = []

    saldo_inicial_total = 0
    entradas_total = 0
    saidas_total = 0

    for nd in naturezas:
        # Filtra itens relacionados a essa ND via grupo
        itens_nd = Item.query.join(Item.grupo).filter_by(natureza_despesa_id=nd.id).all()
        item_ids = [item.id for item in itens_nd]

        # Valor acumulado até o início do mês (saldo inicial)
        entradas_anteriores = db.session.query(
            db.func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)
        ).join(EntradaMaterial).filter(
            EntradaItem.item_id.in_(item_ids),
            EntradaMaterial.data_movimento < data_inicio
        ).scalar() or 0

        saidas_anteriores = db.session.query(
            db.func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)
        ).join(SaidaMaterial).filter(
            SaidaItem.item_id.in_(item_ids),
            SaidaMaterial.data_movimento < data_inicio
        ).scalar() or 0

        saldo_inicial = entradas_anteriores - saidas_anteriores

        # Entradas no mês
        entradas_mes = db.session.query(
            db.func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)
        ).join(EntradaMaterial).filter(
            EntradaItem.item_id.in_(item_ids),
            EntradaMaterial.data_movimento >= data_inicio,
            EntradaMaterial.data_movimento < data_fim
        ).scalar() or 0

        # Saídas no mês
        saidas_mes = db.session.query(
            db.func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)
        ).join(SaidaMaterial).filter(
            SaidaItem.item_id.in_(item_ids),
            SaidaMaterial.data_movimento >= data_inicio,
            SaidaMaterial.data_movimento < data_fim
        ).scalar() or 0

        saldo_final = saldo_inicial + entradas_mes - saidas_mes

        resultado.append({
            'nd': nd,
            'saldo_inicial': saldo_inicial,
            'entradas': entradas_mes,
            'saidas': saidas_mes,
            'saldo_final': saldo_final
        })

        saldo_inicial_total += saldo_inicial
        entradas_total += entradas_mes
        saidas_total += saidas_mes

    saldo_final_total = saldo_inicial_total + entradas_total - saidas_total

    return render_template('mapa_fechamento.html',
                           resultado=resultado,
                           mes=mes,
                           ano=ano,
                           saldo_inicial_total=saldo_inicial_total,
                           entradas_total=entradas_total,
                           saidas_total=saidas_total,
                           saldo_final_total=saldo_final_total)
# routes_dashboard.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from models import EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial, NaturezaDespesa, Item
from extensoes import db

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    # Gráfico de entradas por mês
    entradas_por_mes = (
        db.session.query(
            extract('month', EntradaMaterial.data_movimento).label('mes'),
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario).label('total')
        )
        .join(EntradaItem, EntradaItem.entrada_id == EntradaMaterial.id)
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    # Gráfico de saídas por mês
    saidas_por_mes = (
        db.session.query(
            extract('month', SaidaMaterial.data_movimento).label('mes'),
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario).label('total')
        )
        .join(SaidaItem, SaidaItem.saida_id == SaidaMaterial.id)
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    # Subconsulta de saídas agrupadas por natureza de despesa
    subq_saidas = (
        db.session.query(
            Item.natureza_despesa_id.label('nd_id'),
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario).label('total_saida')
        )
        .join(SaidaItem, SaidaItem.item_id == Item.id)
        .group_by(Item.natureza_despesa_id)
        .subquery()
    )

    # Consulta final com junção de NaturezaDespesa, entradas e subquery de saídas
    totais_por_nd = (
        db.session.query(
            NaturezaDespesa.codigo,
            NaturezaDespesa.nome,
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario).label('entradas'),
            func.coalesce(subq_saidas.c.total_saida, 0).label('saidas')
        )
        .join(EntradaItem.item)
        .filter(Item.natureza_despesa_id == NaturezaDespesa.id)
        .outerjoin(subq_saidas, subq_saidas.c.nd_id == NaturezaDespesa.id)
        .group_by(NaturezaDespesa.codigo, NaturezaDespesa.nome, subq_saidas.c.total_saida)
        .all()
    )

    # Conversão dos dados para o template
    meses = list(range(1, 13))
    entradas = {int(mes): float(total or 0) for mes, total in entradas_por_mes}
    saidas = {int(mes): float(total or 0) for mes, total in saidas_por_mes}

    dados_entrada = [entradas.get(mes, 0) for mes in meses]
    dados_saida = [saidas.get(mes, 0) for mes in meses]

    totais = [
        {
            'codigo': codigo,
            'nome': nome,
            'entradas': float(entrada or 0),
            'saidas': float(saida or 0),
            'saldo': float((entrada or 0) - (saida or 0))
        }
        for codigo, nome, entrada, saida in totais_por_nd
    ]

    return render_template(
        'dashboard.html',
        usuario=current_user,
        meses=meses,
        dados_entrada=dados_entrada,
        dados_saida=dados_saida,
        totais=totais
    )
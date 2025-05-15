# routes_dashboard.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from modelos import EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial, NaturezaDespesa
from extensoes import db

# Criação do blueprint do dashboard
dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')


# ------------------------------ ROTA: Dashboard ------------------------------ #
@dashboard_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    # Gráfico 1: Total de entradas por mês
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

    # Gráfico 2: Total de saídas por mês
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

    # Gráfico 3: Totais por natureza de despesa
    totais_por_nd = (
        db.session.query(
            NaturezaDespesa.codigo,
            NaturezaDespesa.nome,
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario).label('entradas'),
            func.coalesce((
                db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario))
                .join(Item := SaidaItem.item)
                .filter(Item.natureza_despesa_id == NaturezaDespesa.id)
                .correlate(NaturezaDespesa)
                .scalar_subquery()
            ), 0).label('saidas')
        )
        .join(NaturezaDespesa.itens)
        .join(Item := EntradaItem.item)
        .group_by(NaturezaDespesa.codigo, NaturezaDespesa.nome)
        .all()
    )

    # Conversão dos dados para listas para uso no template
    meses = list(range(1, 13))
    entradas = {int(mes): float(total or 0) for mes, total in entradas_por_mes}
    saidas = {int(mes): float(total or 0) for mes, total in saidas_por_mes}

    dados_entrada = [entradas.get(mes, 0) for mes in meses]
    dados_saida = [saidas.get(mes, 0) for mes in meses]

    totais = [
        {
            'codigo': nd.codigo,
            'nome': nd.nome,
            'entradas': float(nd.entradas or 0),
            'saidas': float(nd.saidas or 0),
            'saldo': float((nd.entradas or 0) - (nd.saidas or 0))
        }
        for nd in totais_por_nd
    ]

    return render_template(
        'dashboard.html',
        usuario=current_user,
        meses=meses,
        dados_entrada=dados_entrada,
        dados_saida=dados_saida,
        totais=totais
    )
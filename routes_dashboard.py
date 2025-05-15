# routes_dashboard.py
# Rotas para o dashboard do sistema com gráficos alimentados por dados reais

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from datetime import datetime
from modelos import EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial, NaturezaDespesa

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

# -------------------------- ROTA DO DASHBOARD -------------------------- #
@dashboard_bp.route('/')
@login_required
def dashboard():
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    # Consulta valores totais de entrada por mês
    entradas_por_mes = (
        EntradaItem.query
        .join(EntradaMaterial)
        .with_entities(
            extract('month', EntradaMaterial.data_movimento).label('mes'),
            func.sum(EntradaItem.valor_unitario * EntradaItem.quantidade).label('total')
        )
        .filter(
            extract('year', EntradaMaterial.data_movimento) == ano_atual
        )
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    # Consulta valores totais de saída por mês
    saidas_por_mes = (
        SaidaItem.query
        .join(SaidaMaterial)
        .with_entities(
            extract('month', SaidaMaterial.data_movimento).label('mes'),
            func.sum(SaidaItem.valor_unitario * SaidaItem.quantidade).label('total')
        )
        .filter(
            extract('year', SaidaMaterial.data_movimento) == ano_atual
        )
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    # Prepara listas para os gráficos
    meses = []
    totais_entrada = []
    totais_saida = []

    for entrada in entradas_por_mes:
        meses.append(f'{int(entrada.mes):02d}')
        totais_entrada.append(float(entrada.total))

    for saida in saidas_por_mes:
        totais_saida.append(float(saida.total))

    # Dados por natureza de despesa
    nds = (
        NaturezaDespesa.query
        .with_entities(
            NaturezaDespesa.codigo,
            NaturezaDespesa.nome,
            NaturezaDespesa.valor
        )
        .order_by(NaturezaDespesa.codigo)
        .all()
    )

    return render_template(
        'dashboard.html',
        usuario=current_user,
        meses=meses,
        totais_entrada=totais_entrada,
        totais_saida=totais_saida,
        dados_nd=nds
    )
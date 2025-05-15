# routes_dashboard.py
# Rotas para visualização do Dashboard com gráficos baseados nos dados do banco de dados

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from datetime import datetime
from extensoes import db
from models import EntradaItem, EntradaMaterial

# Criação do blueprint do dashboard
dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

# ------------------------------ ROTA: Dashboard ------------------------------ #
@dashboard_bp.route('/')
@login_required
def dashboard():
    # Obtém mês e ano atual
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    # Consulta total de entradas agrupado por mês
    entradas_por_mes = (
        db.session.query(
            extract('month', EntradaMaterial.data_movimento).label('mes'),
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario).label('total')
        )
        .join(EntradaItem, EntradaItem.entrada_id == EntradaMaterial.id)
        .filter(
            extract('month', EntradaMaterial.data_movimento) == mes_atual,
            extract('year', EntradaMaterial.data_movimento) == ano_atual
        )
        .group_by('mes')
        .all()
    )

    # Prepara os dados para o gráfico
    meses = [f'{int(row.mes):02d}' for row in entradas_por_mes]
    totais = [float(row.total) for row in entradas_por_mes]

    # Renderiza a tela do dashboard com os dados
    return render_template('dashboard.html', usuario=current_user, meses=meses, totais=totais)
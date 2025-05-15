# routes_dashboard.py
# Rota do dashboard com gráficos de movimentação de materiais

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import extract, func
from datetime import datetime
from extensoes import db
from models import EntradaItem, SaidaItem, Item

# Criação do blueprint do dashboard
dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Data atual para filtro por mês
    data_atual = datetime.now()
    mes_atual = data_atual.month
    ano_atual = data_atual.year

    # Entradas por mês
    entradas_por_mes = (
        db.session.query(
            extract('month', EntradaItem.entrada_material.data_movimento).label('mes'),
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario).label('total')
        )
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    # Saídas por mês
    saidas_por_mes = (
        db.session.query(
            extract('month', SaidaItem.saida.data_movimento).label('mes'),
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario).label('total')
        )
        .group_by('mes')
        .order_by('mes')
        .all()
    )

    # Estoque atual por item
    estoque_por_item = (
        db.session.query(
            Item.nome,
            Item.estoque_atual
        )
        .order_by(Item.estoque_atual.desc())
        .limit(10)
        .all()
    )

    # Formatação para gráficos
    meses_entradas = [f'{int(m):02d}' for m, _ in entradas_por_mes]
    valores_entradas = [float(v) for _, v in entradas_por_mes]

    meses_saidas = [f'{int(m):02d}' for m, _ in saidas_por_mes]
    valores_saidas = [float(v) for _, v in saidas_por_mes]

    nomes_itens = [nome for nome, _ in estoque_por_item]
    estoques = [float(qtd) for _, qtd in estoque_por_item]

    return render_template(
        'dashboard.html',
        usuario=current_user,
        meses_entradas=meses_entradas,
        valores_entradas=valores_entradas,
        meses_saidas=meses_saidas,
        valores_saidas=valores_saidas,
        nomes_itens=nomes_itens,
        estoques=estoques
    )
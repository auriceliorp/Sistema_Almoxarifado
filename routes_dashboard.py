# routes_dashboard.py
# Rota para exibir o dashboard com gráficos de movimentações e estatísticas

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from extensoes import db
from models import EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial, NaturezaDespesa, Item, Grupo

# Criação do blueprint
dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

# -------------------- ROTA: Dashboard com gráficos -------------------- #
@dashboard_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    # Subconsulta: total de saídas por ND
    subquery_saidas = (
        db.session.query(
            Item.natureza_despesa_id.label('nd_id'),
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario).label('total_saida')
        )
        .join(SaidaItem, SaidaItem.item_id == Item.id)
        .group_by(Item.natureza_despesa_id)
        .subquery()
    )

    # Consulta principal: entradas e saídas por ND (mesmo sem movimentação)
    resultados = (
        db.session.query(
            NaturezaDespesa.codigo,
            NaturezaDespesa.nome,
            func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0).label('entradas'),
            func.coalesce(subquery_saidas.c.total_saida, 0).label('saidas')
        )
        .outerjoin(Item, Item.natureza_despesa_id == NaturezaDespesa.id)
        .outerjoin(EntradaItem, EntradaItem.item_id == Item.id)
        .outerjoin(subquery_saidas, subquery_saidas.c.nd_id == NaturezaDespesa.id)
        .group_by(NaturezaDespesa.codigo, NaturezaDespesa.nome, subquery_saidas.c.total_saida)
        .all()
    )

    # Lista para gráfico de ND
    dados_entrada = [
        {
            'codigo': row.codigo,
            'nome': row.nome,
            'entradas': float(row.entradas),
            'saidas': float(row.saidas)
        }
        for row in resultados
    ]

    # -------------------- GRÁFICO: Itens por Grupo -------------------- #
    grupo_itens = (
        db.session.query(
            Grupo.nome,
            func.count(Item.id).label('total_itens')
        )
        .outerjoin(Item, Item.grupo_id == Grupo.id)
        .group_by(Grupo.nome)
        .order_by(func.count(Item.id).desc())
        .all()
    )

    dados_grupo_itens = [
        {
            'grupo': g.nome,
            'total': g.total_itens
        }
        for g in grupo_itens
    ]

    return render_template(
        'dashboard.html',
        dados_entrada=dados_entrada,
        dados_grupo_itens=dados_grupo_itens,
        usuario=current_user
    )
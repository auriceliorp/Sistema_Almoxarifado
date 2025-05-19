# routes_dashboard.py
# Rota do painel principal com indicadores e gráficos

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from extensoes import db
from models import EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial, NaturezaDespesa, Item, Fornecedor

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

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

    # Consulta principal: entradas e saídas por ND
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

    dados_entrada = [
        {
            'codigo': row.codigo,
            'nome': row.nome,
            'entradas': float(row.entradas),
            'saidas': float(row.saidas)
        }
        for row in resultados
    ]

    # ---------------- INDICADORES ----------------
    total_itens = db.session.query(func.count(Item.id)).scalar()
    total_fornecedores = db.session.query(func.count(Fornecedor.id)).scalar()
    total_entradas = db.session.query(func.count(EntradaMaterial.id)).scalar()
    total_saidas = db.session.query(func.count(SaidaMaterial.id)).scalar()

    # ---------------- GRÁFICO DE PIZZA ----------------
    grupo_data = (
        db.session.query(
            Item.grupo_id,
            func.count(Item.id).label('quantidade')
        )
        .group_by(Item.grupo_id)
        .all()
    )

    grafico_grupo_labels = [f'Grupo {g.grupo_id}' for g in grupo_data]
    grafico_grupo_dados = [int(g.quantidade) for g in grupo_data]

    return render_template(
        'dashboard.html',
        dados_entrada=dados_entrada,
        grafico_grupo_labels=grafico_grupo_labels,
        grafico_grupo_dados=grafico_grupo_dados,
        total_itens=total_itens,
        total_fornecedores=total_fornecedores,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        usuario=current_user
    )

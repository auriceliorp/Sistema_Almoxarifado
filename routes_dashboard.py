# routes_dashboard.py
# Rota do painel principal com indicadores e gráficos

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from extensoes import db
from models import (
    EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial,
    NaturezaDespesa, Item, Fornecedor, PainelContratacao
)

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/', methods=['GET'])
@login_required
def dashboard():
    # ---------------- ENTRADAS E SAÍDAS POR NATUREZA DE DESPESA ----------------
    subquery_saidas = (
        db.session.query(
            Item.natureza_despesa_id.label('nd_id'),
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario).label('total_saida')
        )
        .join(SaidaItem, SaidaItem.item_id == Item.id)
        .group_by(Item.natureza_despesa_id)
        .subquery()
    )

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

    # ---------------- INDICADORES GERAIS ----------------
    total_itens = db.session.query(func.count(Item.id)).scalar()
    total_fornecedores = db.session.query(func.count(Fornecedor.id)).scalar()
    total_entradas = db.session.query(func.count(EntradaMaterial.id)).scalar()
    total_saidas = db.session.query(func.count(SaidaMaterial.id)).scalar()

    # ---------------- GRÁFICO DE PIZZA (DONUT) - Itens por Grupo ----------------
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

    # ---------------- ABA ALMOXARIFADO ----------------
    itens_abaixo_minimo = Item.query.filter(Item.estoque_atual < Item.estoque_minimo).all()

    itens_movimentados = Item.query.limit(10).all()
    for item in itens_movimentados:
        entradas = db.session.query(func.sum(EntradaItem.quantidade)).filter_by(item_id=item.id).scalar() or 0
        saidas = db.session.query(func.sum(SaidaItem.quantidade)).filter_by(item_id=item.id).scalar() or 0
        item.total_entradas = entradas
        item.total_saidas = saidas

    # ---------------- ABA COMPRAS ----------------
    total_processos = db.session.query(func.count()).select_from(PainelContratacao).filter_by(excluido=False).scalar()
    total_estimado = db.session.query(func.sum(PainelContratacao.valor_estimado)).filter_by(excluido=False).scalar() or 0
    total_com_sei = db.session.query(func.count()).select_from(PainelContratacao)\
        .filter(PainelContratacao.numero_sei != None, PainelContratacao.numero_sei != '', PainelContratacao.excluido == False).scalar()
    total_concluidos = db.session.query(func.count()).select_from(PainelContratacao)\
        .filter(PainelContratacao.status == 'Concluido', PainelContratacao.excluido == False).scalar()

    modalidades = db.session.query(PainelContratacao.modalidade, func.count())\
        .filter(PainelContratacao.excluido == False)\
        .group_by(PainelContratacao.modalidade).all()

    labels_modalidades = [m[0] or 'Não Informada' for m in modalidades]
    valores_modalidades = [m[1] for m in modalidades]

    ultimos_processos = db.session.query(PainelContratacao)\
        .filter(PainelContratacao.excluido == False)\
        .order_by(PainelContratacao.data_abertura.desc())\
        .limit(5).all()

    return render_template(
        'dashboard.html',
        usuario=current_user,
        dados_entrada=dados_entrada,
        grafico_grupo_labels=grafico_grupo_labels,
        grafico_grupo_dados=grafico_grupo_dados,
        total_itens=total_itens,
        total_fornecedores=total_fornecedores,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        itens_abaixo_minimo=itens_abaixo_minimo,
        itens_movimentados=itens_movimentados,
        total_processos=total_processos,
        total_estimado=total_estimado,
        total_com_sei=total_com_sei,
        total_concluidos=total_concluidos,
        labels_modalidades=labels_modalidades,
        valores_modalidades=valores_modalidades,
        ultimos_processos=ultimos_processos
    )
# ------------------------------ IMPORTAÇÕES ------------------------------ #
from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import extract, func
from datetime import datetime
from app_render import db
from models import NaturezaDespesa, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial, Grupo, Item

# ------------------------------ BLUEPRINT ------------------------------ #
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# -------------------------- ROTA: Mapa de Fechamento -------------------------- #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    # Obtém mês e ano da URL ou usa os atuais como padrão
    mes = request.args.get('mes', type=int, default=datetime.now().month)
    ano = request.args.get('ano', type=int, default=datetime.now().year)

    # Consulta todas as ND com pelo menos um grupo vinculado
    nds = db.session.query(NaturezaDespesa).join(Grupo).distinct().all()

    relatorio = []
    total_inicial = 0
    total_entradas = 0
    total_saidas = 0
    total_final = 0

    for nd in nds:
        # IDs dos grupos da ND
        grupo_ids = [g.id for g in nd.grupos]

        # IDs dos itens pertencentes a esses grupos
        item_ids = [item.id for item in Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()]

        if not item_ids:
            continue

        # Saldo inicial: entradas até o último dia do mês anterior - saídas até o mesmo período
        entradas_anteriores = db.session.query(
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)
        ).join(EntradaMaterial).filter(
            EntradaItem.item_id.in_(item_ids),
            extract('year', EntradaMaterial.data_movimento) <= ano,
            (extract('month', EntradaMaterial.data_movimento) < mes) |
            ((extract('month', EntradaMaterial.data_movimento) == mes) & (extract('year', EntradaMaterial.data_movimento) < ano))
        ).scalar() or 0

        saidas_anteriores = db.session.query(
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)
        ).join(SaidaMaterial).filter(
            SaidaItem.item_id.in_(item_ids),
            extract('year', SaidaMaterial.data_movimento) <= ano,
            (extract('month', SaidaMaterial.data_movimento) < mes) |
            ((extract('month', SaidaMaterial.data_movimento) == mes) & (extract('year', SaidaMaterial.data_movimento) < ano))
        ).scalar() or 0

        saldo_inicial = float(entradas_anteriores) - float(saidas_anteriores)

        # Entradas no mês
        entradas = db.session.query(
            func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)
        ).join(EntradaMaterial).filter(
            EntradaItem.item_id.in_(item_ids),
            extract('month', EntradaMaterial.data_movimento) == mes,
            extract('year', EntradaMaterial.data_movimento) == ano
        ).scalar() or 0

        # Saídas no mês
        saidas = db.session.query(
            func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)
        ).join(SaidaMaterial).filter(
            SaidaItem.item_id.in_(item_ids),
            extract('month', SaidaMaterial.data_movimento) == mes,
            extract('year', SaidaMaterial.data_movimento) == ano
        ).scalar() or 0

        saldo_final = saldo_inicial + float(entradas) - float(saidas)

        # Soma totais
        total_inicial += saldo_inicial
        total_entradas += float(entradas)
        total_saidas += float(saidas)
        total_final += saldo_final

        # Adiciona à lista do relatório
        relatorio.append({
            'nd': f'{nd.codigo} - {nd.nome}',
            'inicial': saldo_inicial,
            'entradas': float(entradas),
            'saidas': float(saidas),
            'final': saldo_final
        })

    # Gera lista de anos para o select
    anos_disponiveis = list(set([
        r.ano for r in db.session.query(extract('year', EntradaMaterial.data_movimento).label("ano")).distinct()
    ] + [
        r.ano for r in db.session.query(extract('year', SaidaMaterial.data_movimento).label("ano")).distinct()
    ]))
    anos_disponiveis = sorted([int(a) for a in anos_disponiveis if a is not None], reverse=True)

    return render_template(
        'mapa_fechamento.html',
        relatorio=relatorio,
        mes=mes,
        ano=ano,
        anos_disponiveis=anos_disponiveis,
        total_inicial=total_inicial,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        total_final=total_final
    )
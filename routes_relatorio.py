# routes_relatorio.py
# Rotas para geração de relatórios como o Mapa de Fechamento Mensal

from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import datetime
from sqlalchemy import extract, func
from decimal import Decimal
from app_render import db
from models import NaturezaDespesa, Grupo, Item, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial

# Criação do blueprint
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    # Obtém mês e ano via GET ou usa mês atual
    mes = request.args.get('mes', default=datetime.now().month, type=int)
    ano = request.args.get('ano', default=datetime.now().year, type=int)

    relatorio = []

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    for nd in naturezas:
        # Obtém os grupos vinculados a esta ND
        grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
        grupo_ids = [g.id for g in grupos]

        # Obtém os itens desses grupos
        itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
        item_ids = [item.id for item in itens]

        # SALDO INICIAL = Entradas - Saídas anteriores ao mês atual
        entradas_anteriores = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario))\
            .select_from(EntradaItem)\
            .join(EntradaMaterial)\
            .filter(EntradaItem.item_id.in_(item_ids))\
            .filter(
                (extract('year', EntradaMaterial.data_movimento) < ano) |
                ((extract('year', EntradaMaterial.data_movimento) == ano) &
                 (extract('month', EntradaMaterial.data_movimento) < mes))
            ).scalar() or Decimal('0.00')

        saidas_anteriores = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario))\
            .select_from(SaidaItem)\
            .join(SaidaMaterial)\
            .filter(SaidaItem.item_id.in_(item_ids))\
            .filter(
                (extract('year', SaidaMaterial.data_movimento) < ano) |
                ((extract('year', SaidaMaterial.data_movimento) == ano) &
                 (extract('month', SaidaMaterial.data_movimento) < mes))
            ).scalar() or Decimal('0.00')

        saldo_inicial = Decimal(entradas_anteriores) - Decimal(saidas_anteriores)

        # ENTRADAS NO MÊS
        entradas_mes = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario))\
            .select_from(EntradaItem)\
            .join(EntradaMaterial)\
            .filter(EntradaItem.item_id.in_(item_ids))\
            .filter(extract('year', EntradaMaterial.data_movimento) == ano)\
            .filter(extract('month', EntradaMaterial.data_movimento) == mes)\
            .scalar() or Decimal('0.00')

        # SAÍDAS NO MÊS
        saidas_mes = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario))\
            .select_from(SaidaItem)\
            .join(SaidaMaterial)\
            .filter(SaidaItem.item_id.in_(item_ids))\
            .filter(extract('year', SaidaMaterial.data_movimento) == ano)\
            .filter(extract('month', SaidaMaterial.data_movimento) == mes)\
            .scalar() or Decimal('0.00')

        # SALDO FINAL = Saldo inicial + entradas - saídas
        saldo_final = saldo_inicial + Decimal(entradas_mes) - Decimal(saidas_mes)

        relatorio.append({
            'nd': nd.codigo,
            'nome': nd.nome,
            'saldo_inicial': Decimal(saldo_inicial).quantize(Decimal('0.01')),
            'entradas': Decimal(entradas_mes).quantize(Decimal('0.01')),
            'saidas': Decimal(saidas_mes).quantize(Decimal('0.01')),
            'saldo_final': Decimal(saldo_final).quantize(Decimal('0.01'))
        })

    # Totais consolidados (também em Decimal)
    total_entrada = sum(r['entradas'] for r in relatorio)
    total_saida = sum(r['saidas'] for r in relatorio)
    total_inicial = sum(r['saldo_inicial'] for r in relatorio)
    total_final = sum(r['saldo_final'] for r in relatorio)

    return render_template('mapa_fechamento.html',
                           relatorio=relatorio,
                           mes=mes,
                           ano=ano,
                           total_entrada=total_entrada,
                           total_saida=total_saida,
                           total_inicial=total_inicial,
                           total_final=total_final)
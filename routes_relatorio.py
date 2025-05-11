# routes_relatorio.py
# Rotas para geração de relatórios, como o Mapa de Fechamento Mensal

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import func, select
from decimal import Decimal

from app_render import db
from models import NaturezaDespesa, Grupo, Item, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial

# Criação do blueprint do relatório
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento')
@login_required
def mapa_fechamento():
    # Obtém mês e ano dos parâmetros da URL ou usa o mês atual
    from datetime import date
    hoje = date.today()
    mes = int(request.args.get('mes', hoje.month))
    ano = int(request.args.get('ano', hoje.year))

    # Lista de todas as Naturezas de Despesa
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    relatorio = []

    for nd in naturezas:
        # Seleciona os grupos ligados a esta ND
        grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
        grupo_ids = [g.id for g in grupos]

        # Seleciona os itens ligados aos grupos da ND
        itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
        item_ids = [i.id for i in itens]

        # Calcula o valor total de entradas no mês (join explícito)
        entradas_mes = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario))\
            .select_from(EntradaItem)\
            .join(EntradaMaterial, EntradaItem.entrada_id == EntradaMaterial.id)\
            .filter(
                EntradaItem.item_id.in_(item_ids),
                func.extract('month', EntradaMaterial.data_movimento) == mes,
                func.extract('year', EntradaMaterial.data_movimento) == ano
            ).scalar() or Decimal('0.00')

        # Calcula o valor total de saídas no mês (join explícito)
        saidas_mes = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario))\
            .select_from(SaidaItem)\
            .join(SaidaMaterial, SaidaItem.saida_id == SaidaMaterial.id)\
            .filter(
                SaidaItem.item_id.in_(item_ids),
                func.extract('month', SaidaMaterial.data_movimento) == mes,
                func.extract('year', SaidaMaterial.data_movimento) == ano
            ).scalar() or Decimal('0.00')

        # Saldo inicial é o valor atual no início do mês
        saldo_atual = sum([i.saldo_financeiro or 0 for i in itens])
        saldo_final = Decimal(saldo_atual)
        saldo_inicial = saldo_final - Decimal(entradas_mes) + Decimal(saidas_mes)

        # Monta os dados para exibição
        relatorio.append({
            'nd': nd.codigo,
            'nome': nd.nome,
            'saldo_inicial': round(saldo_inicial, 2),
            'entradas': round(entradas_mes, 2),
            'saidas': round(saidas_mes, 2),
            'saldo_final': round(saldo_final, 2)
        })

    # Soma totalizadores
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
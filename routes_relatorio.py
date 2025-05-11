# ------------------------------ IMPORTAÇÕES ------------------------------ #
from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import extract, func
from app_render import db
from models import NaturezaDespesa, Grupo, Item, EntradaItem, SaidaItem
from datetime import datetime
from decimal import Decimal

# ------------------------------ BLUEPRINT ------------------------------ #
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento')
@login_required
def mapa_fechamento():
    # Obtem mês e ano dos parâmetros da URL ou usa o mês atual
    mes = request.args.get('mes', datetime.now().month, type=int)
    ano = request.args.get('ano', datetime.now().year, type=int)

    # Consulta todas as naturezas de despesa
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    # Inicializa lista para consolidar dados
    dados = []

    # Inicializa totais gerais
    total_inicial = Decimal('0.00')
    total_entradas = Decimal('0.00')
    total_saidas = Decimal('0.00')
    total_final = Decimal('0.00')

    # Loop por natureza de despesa
    for nd in nds:
        grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
        for grupo in grupos:
            itens = Item.query.filter_by(grupo_id=grupo.id).all()
            for item in itens:
                # Saldo inicial = saldo do item antes do mês consultado
                entradas_anteriores = db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0)).\
                    filter(EntradaItem.item_id == item.id).\
                    filter(extract('month', EntradaItem.entrada_material.has(EntradaItem.entrada_material.property.mapper.class_.data_movimento)) < mes).\
                    filter(extract('year', EntradaItem.entrada_material.has(EntradaItem.entrada_material.property.mapper.class_.data_movimento)) == ano).scalar()

                saidas_anteriores = db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0)).\
                    filter(SaidaItem.item_id == item.id).\
                    filter(extract('month', SaidaItem.saida.has(SaidaItem.saida.property.mapper.class_.data_movimento)) < mes).\
                    filter(extract('year', SaidaItem.saida.has(SaidaItem.saida.property.mapper.class_.data_movimento)) == ano).scalar()

                saldo_inicial = Decimal(entradas_anteriores) - Decimal(saidas_anteriores)

                # Entradas no mês
                entrada_valor = db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0)).\
                    join(EntradaItem.entrada_material).\
                    filter(EntradaItem.item_id == item.id).\
                    filter(extract('month', EntradaMaterial.data_movimento) == mes).\
                    filter(extract('year', EntradaMaterial.data_movimento) == ano).scalar()

                # Saídas no mês
                saida_valor = db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0)).\
                    join(SaidaItem.saida).\
                    filter(SaidaItem.item_id == item.id).\
                    filter(extract('month', SaidaMaterial.data_movimento) == mes).\
                    filter(extract('year', SaidaMaterial.data_movimento) == ano).scalar()

                saldo_final = Decimal(saldo_inicial) + Decimal(entrada_valor) - Decimal(saida_valor)

                # Soma nos totais gerais
                total_inicial += saldo_inicial
                total_entradas += Decimal(entrada_valor)
                total_saidas += Decimal(saida_valor)
                total_final += saldo_final

                dados.append({
                    'nd': nd.codigo + ' - ' + nd.nome,
                    'grupo': grupo.nome,
                    'item': item.nome,
                    'inicial': float(saldo_inicial),
                    'entrada': float(entrada_valor),
                    'saida': float(saida_valor),
                    'final': float(saldo_final)
                })

    return render_template('mapa_fechamento.html',
                           dados=dados,
                           mes=mes,
                           ano=ano,
                           total_inicial=float(total_inicial),
                           total_entradas=float(total_entradas),
                           total_saidas=float(total_saidas),
                           total_final=float(total_final))

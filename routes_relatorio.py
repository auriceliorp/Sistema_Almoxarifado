# routes_relatorio.py
# Gera o Mapa de Fechamento Mensal por Natureza de Despesa

from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import datetime, date
from app_render import db
from models import NaturezaDespesa, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, Item

relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')


# ------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET', 'POST'])
@login_required
def mapa_fechamento():
    # Define mês e ano atuais como padrão
    hoje = date.today()
    mes = int(request.form.get('mes', hoje.month))
    ano = int(request.form.get('ano', hoje.year))

    # Define início e fim do mês selecionado
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1)
    else:
        data_fim = date(ano, mes + 1, 1)

    # Busca todas as naturezas de despesa
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.nd).all()
    relatorio = []

    total_entradas = 0
    total_saidas = 0
    total_saldo_inicial = 0
    total_saldo_final = 0

    for nd in naturezas:
        entradas = 0
        saidas = 0

        # Busca entradas no mês por ND (via grupo > item > entrada_item)
        entradas_query = (
            db.session.query(EntradaItem)
            .join(Item, EntradaItem.item_id == Item.id)
            .join(EntradaMaterial, EntradaItem.entrada_id == EntradaMaterial.id)
            .filter(Item.grupo.has(natureza_despesa_id=nd.id))
            .filter(EntradaMaterial.data_movimento >= data_inicio)
            .filter(EntradaMaterial.data_movimento < data_fim)
            .all()
        )

        for ei in entradas_query:
            entradas += ei.quantidade * ei.valor_unitario

        # Busca saídas no mês por ND
        saidas_query = (
            db.session.query(SaidaItem)
            .join(Item, SaidaItem.item_id == Item.id)
            .join(SaidaMaterial, SaidaItem.saida_id == SaidaMaterial.id)
            .filter(Item.grupo.has(natureza_despesa_id=nd.id))
            .filter(SaidaMaterial.data_movimento >= data_inicio)
            .filter(SaidaMaterial.data_movimento < data_fim)
            .all()
        )

        for si in saidas_query:
            saidas += si.quantidade * si.valor_unitario

        saldo_inicial = nd.valor - entradas + saidas
        saldo_final = nd.valor

        relatorio.append({
            'nd': nd.nd,
            'nome': nd.nome,
            'entradas': entradas,
            'saidas': saidas,
            'saldo_inicial': saldo_inicial,
            'saldo_final': saldo_final
        })

        # Acumulados
        total_entradas += entradas
        total_saidas += saidas
        total_saldo_inicial += saldo_inicial
        total_saldo_final += saldo_final

    return render_template('mapa_fechamento.html',
                           relatorio=relatorio,
                           mes=mes,
                           ano=ano,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           total_saldo_inicial=total_saldo_inicial,
                           total_saldo_final=total_saldo_final)
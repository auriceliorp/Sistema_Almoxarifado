routes_relatorio.py

Gera o Mapa de Fechamento Mensal por Natureza de Despesa

from flask import Blueprint, render_template, request from flask_login import login_required from datetime import datetime, date from app_render import db from models import NaturezaDespesa, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, Item

relatorio_bp = Blueprint('relatorio_bp', name, template_folder='templates')

@relatorio_bp.route('/relatorio/fechamento', methods=['GET', 'POST']) @login_required def mapa_fechamento(): # Valores padrão: mês e ano atuais hoje = date.today() mes = hoje.month ano = hoje.year dados = [] total_entradas = 0 total_saidas = 0 total_saldo_inicial = 0 total_saldo_final = 0

if request.method == 'POST':
    mes = int(request.form.get('mes'))
    ano = int(request.form.get('ano'))

    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.nd).all()

    for nd in naturezas:
        # Calcula os valores para o mês e ano informados
        entradas = 0
        saidas = 0
        saldo_inicial = 0
        saldo_final = 0

        # Obtém os itens associados à ND via Grupo
        itens_nd = Item.query.join(Item.grupo).filter_by(natureza_id=nd.id).all()

        for item in itens_nd:
            # Soma entradas no mês
            entradas_qs = EntradaItem.query.join(EntradaMaterial).filter(
                EntradaItem.item_id == item.id,
                EntradaMaterial.data_movimento.month == mes,
                EntradaMaterial.data_movimento.year == ano
            ).all()
            entradas += sum(e.quantidade * e.valor_unitario for e in entradas_qs)

            # Soma saídas no mês
            saidas_qs = SaidaItem.query.join(SaidaMaterial).filter(
                SaidaItem.item_id == item.id,
                SaidaMaterial.data_movimento.month == mes,
                SaidaMaterial.data_movimento.year == ano
            ).all()
            saidas += sum(s.quantidade * s.valor_unitario for s in saidas_qs)

        saldo_final = nd.valor or 0
        saldo_inicial = saldo_final - entradas + saidas

        dados.append({
            'nd': nd.nd,
            'nome': nd.nome,
            'saldo_inicial': saldo_inicial,
            'entradas': entradas,
            'saidas': saidas,
            'saldo_final': saldo_final
        })

        total_entradas += entradas
        total_saidas += saidas
        total_saldo_inicial += saldo_inicial
        total_saldo_final += saldo_final

return render_template('mapa_fechamento.html', dados=dados, mes=mes, ano=ano,
                       total_entradas=total_entradas,
                       total_saidas=total_saidas,
                       total_saldo_inicial=total_saldo_inicial,
                       total_saldo_final=total_saldo_final)


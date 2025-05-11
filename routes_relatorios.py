routes_relatorio.py

Rotas para geração de relatórios do sistema

from flask import Blueprint, render_template, request from flask_login import login_required from sqlalchemy import extract, func from app_render import db from models import NaturezaDespesa, Item, Grupo, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem from datetime import datetime

relatorio_bp = Blueprint('relatorio_bp', name, template_folder='templates')

------------------------------ Mapa de Fechamento Mensal ------------------------------

@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET']) @login_required def mapa_fechamento(): # Coleta parâmetros do formulário ou define padrão ano = request.args.get('ano', datetime.now().year, type=int) mes = request.args.get('mes', datetime.now().month, type=int)

# Define intervalo de datas
data_inicio = datetime(ano, mes, 1)
if mes == 12:
    data_fim = datetime(ano + 1, 1, 1)
else:
    data_fim = datetime(ano, mes + 1, 1)

# Consulta todas as ND com algum vínculo
nds = NaturezaDespesa.query.order_by(NaturezaDespesa.nd).all()

relatorio = []
total_entrada = total_saida = total_saldo_inicial = total_saldo_final = 0

for nd in nds:
    grupos = Grupo.query.filter_by(natureza_id=nd.id).all()
    grupo_ids = [g.id for g in grupos]
    itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
    item_ids = [i.id for i in itens]

    # Entradas no mês
    entradas = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario))\
        .join(EntradaMaterial).filter(
            EntradaItem.item_id.in_(item_ids),
            EntradaMaterial.data_movimento >= data_inicio,
            EntradaMaterial.data_movimento < data_fim
        ).scalar() or 0

    # Saídas no mês
    saidas = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario))\
        .join(SaidaMaterial).filter(
            SaidaItem.item_id.in_(item_ids),
            SaidaMaterial.data_movimento >= data_inicio,
            SaidaMaterial.data_movimento < data_fim
        ).scalar() or 0

    # Saldo inicial = valor anterior ao mês
    saldo_inicial = nd.valor - entradas + saidas
    saldo_final = nd.valor

    total_entrada += entradas
    total_saida += saidas
    total_saldo_inicial += saldo_inicial
    total_saldo_final += saldo_final

    relatorio.append({
        'nd': nd.nd,
        'nome': nd.nome,
        'entrada': entradas,
        'saida': saidas,
        'saldo_inicial': saldo_inicial,
        'saldo_final': saldo_final
    })

return render_template('mapa_fechamento.html', relatorio=relatorio, 
                       total_entrada=total_entrada,
                       total_saida=total_saida,
                       total_saldo_inicial=total_saldo_inicial,
                       total_saldo_final=total_saldo_final,
                       mes=mes, ano=ano)

------------------------------ Mapa disponível ------------------------------

@relatorio_bp.route('/relatorio/meses_disponiveis') @login_required def meses_disponiveis(): anos = db.session.query(extract('year', EntradaMaterial.data_movimento)).distinct().all() anos = sorted(set([int(a[0]) for a in anos])) return {'anos': anos, 'atual': datetime.now().year}


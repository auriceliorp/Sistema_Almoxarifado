# routes_relatorio.py
# Relatório de Mapa de Fechamento Mensal

from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import datetime
from sqlalchemy import func
from app_render import db
from models import NaturezaDespesa, GrupoItem, Item, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial

# Criação do blueprint
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    # Recupera parâmetros de mês e ano
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    # Obtém todos os anos com entradas ou saídas
    anos_entrada = db.session.query(func.extract('year', EntradaMaterial.data_movimento)).distinct()
    anos_saida = db.session.query(func.extract('year', SaidaMaterial.data_movimento)).distinct()
    anos_disponiveis = sorted(set([int(a[0]) for a in anos_entrada.union(anos_saida)]), reverse=True)

    relatorio = []
    total_inicial = total_entradas = total_saidas = total_final = 0

    if mes and ano:
        mes = int(mes)
        ano = int(ano)
        # Obtém todas as ND cadastradas
        nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

        for nd in nds:
            # Recupera grupos vinculados à ND
            grupos = GrupoItem.query.filter_by(natureza_despesa_id=nd.id).all()
            grupo_ids = [g.id for g in grupos]

            if not grupo_ids:
                continue  # Pula ND sem grupo vinculado

            # Recupera itens associados aos grupos
            itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
            item_ids = [i.id for i in itens]

            if not item_ids:
                continue  # Pula ND sem itens vinculados

            # Calcula os totais
            entrada_valor = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)) \
                .join(EntradaMaterial).filter(
                    EntradaItem.item_id.in_(item_ids),
                    func.extract('month', EntradaMaterial.data_movimento) == mes,
                    func.extract('year', EntradaMaterial.data_movimento) == ano
                ).scalar() or 0

            saida_valor = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)) \
                .join(SaidaMaterial).filter(
                    SaidaItem.item_id.in_(item_ids),
                    func.extract('month', SaidaMaterial.data_movimento) == mes,
                    func.extract('year', SaidaMaterial.data_movimento) == ano
                ).scalar() or 0

            # TODO: Calcular saldo inicial corretamente (ainda não implementado)
            saldo_inicial = 0

            relatorio.append({
                'nd': f'{nd.codigo} - {nd.nome}',
                'inicial': float(saldo_inicial),
                'entradas': float(entrada_valor),
                'saidas': float(saida_valor),
                'final': float(saldo_inicial + entrada_valor - saida_valor)
            })

            total_inicial += saldo_inicial
            total_entradas += entrada_valor
            total_saidas += saida_valor
            total_final += saldo_inicial + entrada_valor - saida_valor

    return render_template('mapa_fechamento.html',
                           relatorio=relatorio,
                           anos_disponiveis=anos_disponiveis,
                           total_inicial=total_inicial,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           total_final=total_final)
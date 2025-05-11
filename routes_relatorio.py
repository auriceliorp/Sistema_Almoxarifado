# routes_relatorio.py
# Rotas para relatórios como o Mapa de Fechamento Mensal

from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import datetime
from decimal import Decimal
from app_render import db
from models import NaturezaDespesa, EntradaMaterial, EntradaItem, SaidaMaterial, SaidaItem, Item, Grupo

# Criação do blueprint do relatório
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    # Obtém mês e ano a partir da URL (GET), ou usa o mês/ano atual
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))

    # Consulta todas as naturezas de despesa ordenadas por código
    naturezas = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    dados = []

    # Para cada natureza de despesa, calcula entradas, saídas, saldo inicial e final
    for nd in naturezas:
        # Busca os grupos relacionados à natureza de despesa
        grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
        grupo_ids = [g.id for g in grupos]

        # Busca os itens relacionados aos grupos
        itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
        item_ids = [item.id for item in itens]

        # Soma das entradas no mês
        entradas_mes = (
            db.session.query(db.func.sum(EntradaItem.valor_total))
            .join(EntradaMaterial)
            .filter(
                EntradaItem.item_id.in_(item_ids),
                db.extract('month', EntradaMaterial.data_movimento) == mes,
                db.extract('year', EntradaMaterial.data_movimento) == ano
            )
            .scalar()
        ) or Decimal('0.00')

        # Soma das saídas no mês
        saidas_mes = (
            db.session.query(db.func.sum(SaidaItem.valor_total))
            .join(SaidaMaterial)
            .filter(
                SaidaItem.item_id.in_(item_ids),
                db.extract('month', SaidaMaterial.data_movimento) == mes,
                db.extract('year', SaidaMaterial.data_movimento) == ano
            )
            .scalar()
        ) or Decimal('0.00')

        # Saldo inicial fictício (caso queira implementar depois, esse campo pode vir de histórico)
        saldo_inicial = Decimal('0.00')

        # Cálculo do saldo final
        saldo_final = saldo_inicial + entradas_mes - saidas_mes

        # Adiciona ao dicionário final para enviar ao template
        dados.append({
            'nd': nd,
            'entradas': entradas_mes,
            'saidas': saidas_mes,
            'saldo_inicial': saldo_inicial,
            'saldo_final': saldo_final
        })

    # Renderiza o template do relatório com os dados calculados
    return render_template('mapa_fechamento.html', dados=dados, mes=mes, ano=ano)
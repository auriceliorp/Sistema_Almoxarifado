# routes_dashboard.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Item, EntradaItem, SaidaItem
from sqlalchemy import extract, func
from datetime import datetime
from app_render import db

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Total de itens cadastrados
    total_itens = Item.query.count()

    # Mês atual
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    # Entradas no mês
    entradas_mes = db.session.query(func.sum(EntradaItem.quantidade)).\
        join(EntradaItem.entrada).\
        filter(extract('month', EntradaItem.entrada.data_movimento) == mes_atual,
               extract('year', EntradaItem.entrada.data_movimento) == ano_atual).\
        scalar() or 0

    # Saídas no mês
    saidas_mes = db.session.query(func.sum(SaidaItem.quantidade)).\
        join(SaidaItem.saida).\
        filter(extract('month', SaidaItem.saida.data_movimento) == mes_atual,
               extract('year', SaidaItem.saida.data_movimento) == ano_atual).\
        scalar() or 0

    # Requisições pendentes (placeholder, ajustar quando houver essa lógica)
    requisicoes_pendentes = 0

    # Dados dos últimos 6 meses
    meses = []
    dados_entrada = []
    dados_saida = []

    for i in range(5, -1, -1):
        mes_ref = datetime.now().replace(day=1) - relativedelta(months=i)
        mes_label = mes_ref.strftime('%b/%y')
        meses.append(mes_label)

        entrada = db.session.query(func.sum(EntradaItem.quantidade)).\
            join(EntradaItem.entrada).\
            filter(extract('month', EntradaItem.entrada.data_movimento) == mes_ref.month,
                   extract('year', EntradaItem.entrada.data_movimento) == mes_ref.year).\
            scalar() or 0

        saida = db.session.query(func.sum(SaidaItem.quantidade)).\
            join(SaidaItem.saida).\
            filter(extract('month', SaidaItem.saida.data_movimento) == mes_ref.month,
                   extract('year', SaidaItem.saida.data_movimento) == mes_ref.year).\
            scalar() or 0

        dados_entrada.append(entrada)
        dados_saida.append(saida)

    # Itens com estoque abaixo do mínimo
    itens_baixo_estoque_query = Item.query.filter(Item.quantidade_estoque < Item.estoque_minimo).all()
    itens_baixo_estoque_labels = [item.nome for item in itens_baixo_estoque_query]
    itens_baixo_estoque_dados = [item.quantidade_estoque for item in itens_baixo_estoque_query]

    return render_template('dashboard.html',
                           usuario=current_user,
                           total_itens=total_itens,
                           entradas_mes=entradas_mes,
                           saidas_mes=saidas_mes,
                           requisicoes_pendentes=requisicoes_pendentes,
                           meses=meses,
                           dados_entrada=dados_entrada,
                           dados_saida=dados_saida,
                           itens_baixo_estoque_labels=itens_baixo_estoque_labels,
                           itens_baixo_estoque_dados=itens_baixo_estoque_dados)
routes_dashboard.py

Rota para exibir o dashboard com dados reais do banco

from flask import Blueprint, render_template from flask_login import login_required, current_user from models import Item, EntradaItem, SaidaItem from sqlalchemy import extract, func from datetime import datetime

Cria blueprint

dashboard_bp = Blueprint('dashboard_bp', name, url_prefix='/dashboard')

@dashboard_bp.route('/') @login_required def dashboard(): # Total de itens cadastrados total_itens = Item.query.count()

# Dados mensais do ano atual
ano_atual = datetime.now().year

# Entradas por mês
entradas_mes = (
    EntradaItem.query
    .join(EntradaItem.entrada)
    .with_entities(extract('month', EntradaItem.entrada.data_movimento).label('mes'), func.sum(EntradaItem.quantidade).label('total'))
    .filter(extract('year', EntradaItem.entrada.data_movimento) == ano_atual)
    .group_by('mes')
    .order_by('mes')
    .all()
)

# Saídas por mês
saidas_mes = (
    SaidaItem.query
    .join(SaidaItem.saida)
    .with_entities(extract('month', SaidaItem.saida.data_movimento).label('mes'), func.sum(SaidaItem.quantidade).label('total'))
    .filter(extract('year', SaidaItem.saida.data_movimento) == ano_atual)
    .group_by('mes')
    .order_by('mes')
    .all()
)

# Converte os dados em listas completas de 12 meses
meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
dados_entrada = [0]*12
dados_saida = [0]*12

for entrada in entradas_mes:
    dados_entrada[int(entrada.mes) - 1] = int(entrada.total)

for saida in saidas_mes:
    dados_saida[int(saida.mes) - 1] = int(saida.total)

# Itens com estoque abaixo do mínimo
itens_criticos = Item.query.filter(Item.quantidade_estoque <= Item.estoque_minimo).limit(10).all()
itens_baixo_estoque_labels = [i.nome for i in itens_criticos]
itens_baixo_estoque_dados = [i.quantidade_estoque for i in itens_criticos]

# Exemplo para requisicoes pendentes (placeholder por enquanto)
requisicoes_pendentes = 5

return render_template('dashboard.html',
                       total_itens=total_itens,
                       entradas_mes=sum(dados_entrada),
                       saidas_mes=sum(dados_saida),
                       requisicoes_pendentes=requisicoes_pendentes,
                       meses=meses,
                       dados_entrada=dados_entrada,
                       dados_saida=dados_saida,
                       itens_baixo_estoque_labels=itens_baixo_estoque_labels,
                       itens_baixo_estoque_dados=itens_baixo_estoque_dados,
                       usuario=current_user)


routes_relatorio.py

Rotas para relatórios do sistema, incluindo o Mapa de Fechamento Mensal

from flask import Blueprint, render_template, request from flask_login import login_required from sqlalchemy import extract, func from app_render import db from models import NaturezaDespesa, Grupo, Item, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial from datetime import datetime

Cria o blueprint

relatorio_bp = Blueprint('relatorio_bp', name, template_folder='templates')

------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------

@relatorio_bp.route('/relatorio/mapa_fechamento') @login_required def mapa_fechamento(): # Recupera os parâmetros de filtro de mês e ano mes = request.args.get('mes', default=datetime.now().month, type=int) ano = request.args.get('ano', default=datetime.now().year, type=int)

# Busca todas as ND do sistema (mesmo que não tenham movimentação)
nds = NaturezaDespesa.query.order_by(NaturezaDespesa.nome).all()

linhas = []
total_inicial = total_entrada = total_saida = total_final = 0.0

for nd in nds:
    # Busca todos os grupos vinculados a essa ND
    grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
    grupo_ids = [g.id for g in grupos]

    # Busca todos os itens vinculados aos grupos
    itens = Item.query.filter(Item.grupo_id.in_(grupo_ids)).all()
    item_ids = [i.id for i in itens]

    # Calcula o saldo inicial (entradas - saídas anteriores ao mês/ano)
    entradas_anteriores = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)) \
        .join(EntradaMaterial) \
        .filter(EntradaItem.item_id.in_(item_ids)) \
        .filter(
            (extract('year', EntradaMaterial.data_movimento) < ano) |
            ((extract('year', EntradaMaterial.data_movimento) == ano) & (extract('month', EntradaMaterial.data_movimento) < mes))
        ).scalar() or 0

    saidas_anteriores = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)) \
        .join(SaidaMaterial) \
        .filter(SaidaItem.item_id.in_(item_ids)) \
        .filter(
            (extract('year', SaidaMaterial.data_movimento) < ano) |
            ((extract('year', SaidaMaterial.data_movimento) == ano) & (extract('month', SaidaMaterial.data_movimento) < mes))
        ).scalar() or 0

    saldo_inicial = entradas_anteriores - saidas_anteriores

    # Calcula entradas e saídas do mês/ano atual
    entrada_valor = db.session.query(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario)) \
        .join(EntradaMaterial) \
        .filter(EntradaItem.item_id.in_(item_ids)) \
        .filter(extract('year', EntradaMaterial.data_movimento) == ano) \
        .filter(extract('month', EntradaMaterial.data_movimento) == mes).scalar() or 0

    saida_valor = db.session.query(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario)) \
        .join(SaidaMaterial) \
        .filter(SaidaItem.item_id.in_(item_ids)) \
        .filter(extract('year', SaidaMaterial.data_movimento) == ano) \
        .filter(extract('month', SaidaMaterial.data_movimento) == mes).scalar() or 0

    # Converte para float para evitar erro de operação com Decimal
    inicial_f = float(saldo_inicial)
    entrada_f = float(entrada_valor)
    saida_f = float(saida_valor)

    linha = {
        'nd': nd.nome,
        'inicial': inicial_f,
        'entrada': entrada_f,
        'saida': saida_f,
        'final': inicial_f + entrada_f - saida_f
    }
    linhas.append(linha)

    total_inicial += inicial_f
    total_entrada += entrada_f
    total_saida += saida_f
    total_final += linha['final']

return render_template('mapa_fechamento.html',
                       linhas=linhas,
                       total_inicial=total_inicial,
                       total_entrada=total_entrada,
                       total_saida=total_saida,
                       total_final=total_final,
                       mes=mes,
                       ano=ano)

--------------------------------------------------------------------------------------------


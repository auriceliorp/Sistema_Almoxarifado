# routes_relatorio.py
# Rotas para geração de relatórios

from flask import Blueprint, render_template, request
from flask_login import login_required
from app_render import db
from models import NaturezaDespesa, Grupo, EntradaItem, EntradaMaterial, SaidaItem, SaidaMaterial
from sqlalchemy import extract, func
from decimal import Decimal

# Criação do blueprint
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento', methods=['GET'])
@login_required
def mapa_fechamento():
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)

    relatorio = []

    if mes and ano:
        naturezas = NaturezaDespesa.query.all()

        for nd in naturezas:
            linha = {}
            linha['nd_id'] = nd.id
            linha['nd_nome'] = nd.nome  # CORREÇÃO ESSENCIAL

            grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
            grupo_ids = [g.id for g in grupos]

            # ENTRADAS
            entradas = (
                db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0))
                .join(EntradaMaterial)
                .join(EntradaItem.item)
                .filter(
                    EntradaItem.item.has(Grupo.id.in_(grupo_ids)),
                    extract('month', EntradaMaterial.data_movimento) == mes,
                    extract('year', EntradaMaterial.data_movimento) == ano
                )
                .scalar()
            )

            # SAÍDAS
            saidas = (
                db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0))
                .join(SaidaMaterial)
                .join(SaidaItem.item)
                .filter(
                    SaidaItem.item.has(Grupo.id.in_(grupo_ids)),
                    extract('month', SaidaMaterial.data_movimento) == mes,
                    extract('year', SaidaMaterial.data_movimento) == ano
                )
                .scalar()
            )

            entradas = float(entradas or 0)
            saidas = float(saidas or 0)

            linha['saldo_inicial'] = 0.0
            linha['entradas'] = entradas
            linha['saidas'] = saidas
            linha['saldo_final'] = entradas - saidas

            relatorio.append(linha)

        # TOTAIS GERAIS
        total_entradas = sum(r['entradas'] for r in relatorio)
        total_saidas = sum(r['saidas'] for r in relatorio)
        total_saldo_inicial = sum(r['saldo_inicial'] for r in relatorio)
        total_saldo_final = sum(r['saldo_final'] for r in relatorio)
    else:
        relatorio = []
        total_entradas = total_saidas = total_saldo_inicial = total_saldo_final = 0.0

    return render_template('mapa_fechamento.html',
                           relatorio=relatorio,
                           mes=mes,
                           ano=ano,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           total_saldo_inicial=total_saldo_inicial,
                           total_saldo_final=total_saldo_final)
# routes_relatorio.py
# Rotas para geração de relatórios, incluindo o Mapa de Fechamento Mensal

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import extract, func
from app_render import db
from models import NaturezaDespesa, Grupo, Item, EntradaItem, SaidaItem, EntradaMaterial, SaidaMaterial
from datetime import datetime
from decimal import Decimal
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from flask import send_file
import tempfile

# Criação do blueprint do relatório
relatorio_bp = Blueprint('relatorio_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Mapa de Fechamento Mensal ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento')
@login_required
def mapa_fechamento():
    # Captura mês e ano selecionados (ou padrão atual)
    from datetime import datetime
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))

    # Lista todas as NDs
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    relatorio = []

    # Totais gerais
    total_entradas = 0
    total_saidas = 0
    total_saldo_inicial = 0
    total_saldo_final = 0

    # Processa cada ND
    for nd in nds:
        grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
        entrada_valor = Decimal('0')
        saida_valor = Decimal('0')
        saldo_inicial = Decimal('0')

        # Para cada grupo, busca os itens e calcula movimentações
        for grupo in grupos:
            for item in grupo.itens:
                # Entradas no mês
                entrada = (
                    db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0))
                    .join(EntradaMaterial, EntradaItem.entrada_id == EntradaMaterial.id)
                    .filter(
                        EntradaItem.item_id == item.id,
                        extract('month', EntradaMaterial.data_movimento) == mes,
                        extract('year', EntradaMaterial.data_movimento) == ano
                    )
                    .scalar()
                )
                entrada_valor += Decimal(entrada)

                # Saídas no mês
                saida = (
                    db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0))
                    .join(SaidaMaterial, SaidaItem.saida_id == SaidaMaterial.id)
                    .filter(
                        SaidaItem.item_id == item.id,
                        extract('month', SaidaMaterial.data_movimento) == mes,
                        extract('year', SaidaMaterial.data_movimento) == ano
                    )
                    .scalar()
                )
                saida_valor += Decimal(saida)

                # Saldo inicial (entradas anteriores ao mês)
                entradas_anteriores = (
                    db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0))
                    .join(EntradaMaterial, EntradaItem.entrada_id == EntradaMaterial.id)
                    .filter(
                        EntradaItem.item_id == item.id,
                        extract('year', EntradaMaterial.data_movimento) == ano,
                        extract('month', EntradaMaterial.data_movimento) < mes
                    )
                    .scalar()
                )

                saidas_anteriores = (
                    db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0))
                    .join(SaidaMaterial, SaidaItem.saida_id == SaidaMaterial.id)
                    .filter(
                        SaidaItem.item_id == item.id,
                        extract('year', SaidaMaterial.data_movimento) == ano,
                        extract('month', SaidaMaterial.data_movimento) < mes
                    )
                    .scalar()
                )

                saldo_inicial += Decimal(entradas_anteriores) - Decimal(saidas_anteriores)

        # Soma para totais gerais
        total_entradas += float(entrada_valor)
        total_saidas += float(saida_valor)
        total_saldo_inicial += float(saldo_inicial)
        total_saldo_final += float(saldo_inicial + entrada_valor - saida_valor)

        # Adiciona ND ao relatório (mesmo sem movimentação)
        relatorio.append({
            'nd': nd,
            'entrada': float(entrada_valor),
            'saida': float(saida_valor),
            'inicial': float(saldo_inicial),
            'final': float(saldo_inicial + entrada_valor - saida_valor)
        })

    # Lista de anos para o filtro
    anos_disponiveis = list(range(2020, datetime.now().year + 1))

    return render_template('mapa_fechamento.html',
                           relatorio=relatorio,
                           mes=mes,
                           ano=ano,
                           anos_disponiveis=anos_disponiveis,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           total_saldo_inicial=total_saldo_inicial,
                           total_saldo_final=total_saldo_final)

# ------------------------------ ROTA: Impressão HTML ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento/imprimir')
@login_required
def imprimir_mapa_fechamento():
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))

    # Lógica para montar os dados (exemplo genérico, substitua conforme sua lógica real)
    relatorio = gerar_relatorio_mensal(mes, ano)
    totais = calcular_totais(relatorio)
    dados = {
        'relatorio': relatorio,
        'totais': totais,
        'mes': mes,
        'ano': ano
    }

    return render_template('mapa_fechamento_imprimir.html', **dados)

from flask import send_file
import tempfile

# Função auxiliar para gerar os dados do relatório
def gerar_relatorio_mensal(mes, ano):
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    relatorio = []

    for nd in nds:
        grupos = Grupo.query.filter_by(natureza_despesa_id=nd.id).all()
        entrada_valor = Decimal('0')
        saida_valor = Decimal('0')
        saldo_inicial = Decimal('0')

        for grupo in grupos:
            for item in grupo.itens:
                entrada = (
                    db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0))
                    .join(EntradaMaterial, EntradaItem.entrada_id == EntradaMaterial.id)
                    .filter(
                        EntradaItem.item_id == item.id,
                        extract('month', EntradaMaterial.data_movimento) == mes,
                        extract('year', EntradaMaterial.data_movimento) == ano
                    )
                    .scalar()
                )
                entrada_valor += Decimal(entrada)

                saida = (
                    db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0))
                    .join(SaidaMaterial, SaidaItem.saida_id == SaidaMaterial.id)
                    .filter(
                        SaidaItem.item_id == item.id,
                        extract('month', SaidaMaterial.data_movimento) == mes,
                        extract('year', SaidaMaterial.data_movimento) == ano
                    )
                    .scalar()
                )
                saida_valor += Decimal(saida)

                entradas_anteriores = (
                    db.session.query(func.coalesce(func.sum(EntradaItem.quantidade * EntradaItem.valor_unitario), 0))
                    .join(EntradaMaterial, EntradaItem.entrada_id == EntradaMaterial.id)
                    .filter(
                        EntradaItem.item_id == item.id,
                        extract('year', EntradaMaterial.data_movimento) == ano,
                        extract('month', EntradaMaterial.data_movimento) < mes
                    )
                    .scalar()
                )

                saidas_anteriores = (
                    db.session.query(func.coalesce(func.sum(SaidaItem.quantidade * SaidaItem.valor_unitario), 0))
                    .join(SaidaMaterial, SaidaItem.saida_id == SaidaMaterial.id)
                    .filter(
                        SaidaItem.item_id == item.id,
                        extract('year', SaidaMaterial.data_movimento) == ano,
                        extract('month', SaidaMaterial.data_movimento) < mes
                    )
                    .scalar()
                )

                saldo_inicial += Decimal(entradas_anteriores) - Decimal(saidas_anteriores)

        relatorio.append({
            'nd': nd,
            'entrada': float(entrada_valor),
            'saida': float(saida_valor),
            'inicial': float(saldo_inicial),
            'final': float(saldo_inicial + entrada_valor - saida_valor)
        })

    return relatorio


# Função auxiliar para calcular totais
def calcular_totais(relatorio):
    return {
        'entrada': sum(r['entrada'] for r in relatorio),
        'saida': sum(r['saida'] for r in relatorio),
        'inicial': sum(r['inicial'] for r in relatorio),
        'final': sum(r['final'] for r in relatorio),
    }

# ------------------------------ ROTA: Exportar Excel ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento/excel')
@login_required
def exportar_mapa_excel():
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))

    relatorio = gerar_relatorio_mensal(mes, ano)

    df = pd.DataFrame([{
        'ND': f"{r['nd'].codigo} - {r['nd'].nome}",
        'Saldo Inicial': r['inicial'],
        'Entradas': r['entrada'],
        'Saídas': r['saida'],
        'Saldo Final': r['final'],
    } for r in relatorio])

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        df.to_excel(tmp.name, index=False)
        tmp.seek(0)
        return send_file(tmp.name, as_attachment=True,
                         download_name=f'mapa_fechamento_{mes:02d}_{ano}.xlsx')

# ------------------------------ ROTA: Exportar PDF ------------------------------ #
@relatorio_bp.route('/relatorio/mapa_fechamento/pdf')
@login_required
def exportar_mapa_pdf():
    mes = int(request.args.get('mes', datetime.now().month))
    ano = int(request.args.get('ano', datetime.now().year))
    relatorio = gerar_relatorio_mensal(mes, ano)
    totais = calcular_totais(relatorio)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, f"Mapa de Fechamento Mensal - {mes:02d}/{ano}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", size=8)
    pdf.cell(60, 8, "ND", 1)
    pdf.cell(30, 8, "Inicial", 1)
    pdf.cell(30, 8, "Entradas", 1)
    pdf.cell(30, 8, "Saídas", 1)
    pdf.cell(30, 8, "Final", 1)
    pdf.ln()

    for r in relatorio:
        pdf.cell(60, 8, f"{r['nd'].codigo} - {r['nd'].nome}", 1)
        pdf.cell(30, 8, f"{r['inicial']:.2f}", 1)
        pdf.cell(30, 8, f"{r['entrada']:.2f}", 1)
        pdf.cell(30, 8, f"{r['saida']:.2f}", 1)
        pdf.cell(30, 8, f"{r['final']:.2f}", 1)
        pdf.ln()

    pdf.set_font("Arial", "B", 8)
    pdf.cell(60, 8, "Totais", 1)
    pdf.cell(30, 8, f"{totais['inicial']:.2f}", 1)
    pdf.cell(30, 8, f"{totais['entrada']:.2f}", 1)
    pdf.cell(30, 8, f"{totais['saida']:.2f}", 1)
    pdf.cell(30, 8, f"{totais['final']:.2f}", 1)

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        return send_file(tmp.name, as_attachment=True,
                         download_name=f'mapa_fechamento_{mes:02d}_{ano}.pdf')

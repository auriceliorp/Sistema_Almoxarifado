from flask import Blueprint, request, render_template, flash, redirect, url_for, make_response
from .models import Item, NaturezaDespesa, MovimentoEstoque
from .database import db
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from functools import wraps
import io
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Criar um Blueprint para as rotas de relatórios
relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")

# Decorator para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash("Acesso negado. Você precisa ser um administrador.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function

@relatorios_bp.route("/inventario", methods=["GET"])
@login_required
def relatorio_inventario():
    """Gera relatório de inventário com todos os itens ativos."""
    # Filtrar por ND se fornecido
    nd_id = request.args.get("nd_id", type=int)
    
    query = Item.query.options(
        db.joinedload(Item.natureza_despesa)
    ).filter(Item.ativo == True)
    
    if nd_id:
        query = query.filter(Item.natureza_despesa_id == nd_id)
    
    itens_estoque = query.order_by(Item.nome).all()
    
    # Obter todas as NDs para o filtro
    naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    
    # Verificar se é solicitação de PDF
    formato = request.args.get("formato")
    if formato == "pdf":
        return gerar_pdf_inventario(itens_estoque)
    
    return render_template(
        "relatorios/inventario.html", 
        itens=itens_estoque,
        naturezas_despesa=naturezas_despesa,
        nd_id=nd_id
    )

@relatorios_bp.route("/mensal_nd", methods=["GET"])
@login_required
def relatorio_mensal_nd():
    """Gera relatório mensal por Natureza de Despesa com saldo inicial e final."""
    mes_ano_str = request.args.get("mes_ano")
    
    # Se não for fornecido, usar mês anterior
    if not mes_ano_str:
        hoje = datetime.utcnow()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        mes_ano_str = ultimo_dia_mes_anterior.strftime("%Y-%m")
    
    try:
        ano, mes = map(int, mes_ano_str.split("-"))
        data_inicio_mes = datetime(ano, mes, 1)
        if mes == 12:
            data_fim_mes = datetime(ano + 1, 1, 1)
        else:
            data_fim_mes = datetime(ano, mes + 1, 1)
    except (ValueError, IndexError):
        flash("Formato de data inválido. Use o formato YYYY-MM.", "error")
        return render_template("relatorios/mensal_nd.html", relatorio=[], mes_ano=mes_ano_str)
    
    # Obter todas as NDs
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    relatorio = []
    
    for nd in nds:
        # Obter itens desta ND
        itens_nd = Item.query.filter_by(natureza_despesa_id=nd.id).all()
        item_ids = [item.id for item in itens_nd]
        
        if not item_ids:
            relatorio.append({
                "nd": nd, 
                "saldo_inicial": 0, 
                "total_entradas": 0, 
                "total_saidas": 0, 
                "saldo_final": 0, 
                "itens": []
            })
            continue
        
        # Obter saldos iniciais (último movimento antes do início do mês)
        subquery_saldo_inicial = db.session.query(
            MovimentoEstoque.item_id, 
            func.max(MovimentoEstoque.id).label("max_id")
        ).filter(
            MovimentoEstoque.item_id.in_(item_ids), 
            MovimentoEstoque.data_movimento < data_inicio_mes
        ).group_by(MovimentoEstoque.item_id).subquery()
        
        saldos_iniciais_itens = db.session.query(
            MovimentoEstoque.item_id, 
            MovimentoEstoque.saldo_posterior
        ).join(
            subquery_saldo_inicial, 
            MovimentoEstoque.id == subquery_saldo_inicial.c.max_id
        ).all()
        
        # Mapear saldos iniciais por item
        map_saldo_inicial_item = {item_id: saldo for item_id, saldo in saldos_iniciais_itens}
        saldo_inicial_nd = sum(map_saldo_inicial_item.values())
        
        # Obter movimentos do mês
        movimentos_mes = db.session.query(
            MovimentoEstoque.item_id, 
            MovimentoEstoque.tipo, 
            func.sum(MovimentoEstoque.quantidade).label("total_quantidade")
        ).filter(
            MovimentoEstoque.item_id.in_(item_ids), 
            MovimentoEstoque.data_movimento >= data_inicio_mes, 
            MovimentoEstoque.data_movimento < data_fim_mes
        ).group_by(MovimentoEstoque.item_id, MovimentoEstoque.tipo).all()
        
        # Calcular totais de entradas e saídas
        total_entradas_nd = 0
        total_saidas_nd = 0
        map_entradas_item = {item_id: 0 for item_id in item_ids}
        map_saidas_item = {item_id: 0 for item_id in item_ids}
        
        for item_id, tipo, total_quantidade in movimentos_mes:
            if tipo.startswith("ENTRADA") or tipo == "INVENTARIO_INICIAL":
                total_entradas_nd += total_quantidade
                map_entradas_item[item_id] = map_entradas_item.get(item_id, 0) + total_quantidade
            elif tipo.startswith("SAIDA"):
                total_saidas_nd += total_quantidade
                map_saidas_item[item_id] = map_saidas_item.get(item_id, 0) + total_quantidade
        
        # Calcular saldo final
        saldo_final_nd = saldo_inicial_nd + total_entradas_nd - total_saidas_nd
        
        # Detalhes por item
        itens_detalhe = []
        for item in itens_nd:
            saldo_inicial_item = map_saldo_inicial_item.get(item.id, 0)
            entradas_item = map_entradas_item.get(item.id, 0)
            saidas_item = map_saidas_item.get(item.id, 0)
            saldo_final_item = saldo_inicial_item + entradas_item - saidas_item
            
            itens_detalhe.append({
                "item": item,
                "saldo_inicial": saldo_inicial_item,
                "entradas": entradas_item,
                "saidas": saidas_item,
                "saldo_final": saldo_final_item
            })
        
        relatorio.append({
            "nd": nd,
            "saldo_inicial": saldo_inicial_nd,
            "total_entradas": total_entradas_nd,
            "total_saidas": total_saidas_nd,
            "saldo_final": saldo_final_nd,
            "itens": itens_detalhe
        })
    
    # Verificar se é solicitação de PDF
    formato = request.args.get("formato")
    if formato == "pdf":
        return gerar_pdf_mensal_nd(relatorio, mes_ano_str)
    
    return render_template("relatorios/mensal_nd.html", relatorio=relatorio, mes_ano=mes_ano_str)

def gerar_pdf_inventario(itens):
    """Gera um PDF do relatório de inventário."""
    # Preparar o HTML para o PDF
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Inventário</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h1 {
                color: #0066cc;
                text-align: center;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .footer {
                margin-top: 30px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <h1>Relatório de Inventário</h1>
        <p>Data de geração: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</p>
        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th>ND</th>
                    <th>Descrição ND</th>
                    <th>Unidade</th>
                    <th>Saldo Atual</th>
                    <th>Estoque Mínimo</th>
                    <th>Ponto de Ressuprimento</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Adicionar dados dos itens
    for item in itens:
        nd_codigo = item.natureza_despesa.codigo if item.natureza_despesa else "N/A"
        nd_descricao = item.natureza_despesa.descricao if item.natureza_despesa else "N/A"
        
        html_content += f"""
                <tr>
                    <td>{item.nome}</td>
                    <td>{nd_codigo}</td>
                    <td>{nd_descricao}</td>
                    <td>{item.unidade_medida}</td>
                    <td>{item.saldo_atual}</td>
                    <td>{item.estoque_minimo}</td>
                    <td>{item.ponto_ressuprimento}</td>
                </tr>
        """
    
    # Fechar o HTML
    html_content += """
            </tbody>
        </table>
        <div class="footer">
            Sistema de Almoxarifado - Relatório de Inventário
        </div>
    </body>
    </html>
    """
    
    # Gerar o PDF
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    css = CSS(string="""
        @page {
            size: A4;
            margin: 1cm;
        }
        @font-face {
            font-family: 'Arial';
            src: local('Arial');
        }
    """, font_config=font_config)
    
    pdf_buffer = io.BytesIO()
    html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
    pdf_buffer.seek(0)
    
    # Criar resposta com o PDF
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio_inventario.pdf'
    
    return response

def gerar_pdf_mensal_nd(relatorio, mes_ano_str):
    """Gera um PDF do relatório mensal por ND."""
    try:
        ano, mes = map(int, mes_ano_str.split("-"))
        mes_nome = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ][mes - 1]
        periodo = f"{mes_nome} de {ano}"
    except:
        periodo = mes_ano_str
    
    # Preparar o HTML para o PDF
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório Mensal por Natureza de Despesa</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h1, h2 {
                color: #0066cc;
                text-align: center;
            }
            h3 {
                color: #0066cc;
                margin-top: 30px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                margin-bottom: 30px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .footer {
                margin-top: 30px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }
            .resumo {
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <h1>Relatório Mensal por Natureza de Despesa</h1>
        <h2>""" + periodo + """</h2>
        <p>Data de geração: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</p>
    """
    
    # Adicionar dados de cada ND
    for nd_data in relatorio:
        nd = nd_data["nd"]
        html_content += f"""
        <h3>ND {nd.codigo} - {nd.descricao}</h3>
        <div class="resumo">
            <p><strong>Saldo Inicial:</strong> {nd_data["saldo_inicial"]}</p>
            <p><strong>Total de Entradas:</strong> {nd_data["total_entradas"]}</p>
            <p><strong>Total de Saídas:</strong> {nd_data["total_saidas"]}</p>
            <p><strong>Saldo Final:</strong> {nd_data["saldo_final"]}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Unidade</th>
                    <th>Saldo Inicial</th>
                    <th>Entradas</th>
                    <th>Saídas</th>
                    <th>Saldo Final</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Adicionar dados dos itens desta ND
        for item_data in nd_data["itens"]:
            item = item_data["item"]
            html_content += f"""
                <tr>
                    <td>{item.nome}</td>
                    <td>{item.unidade_medida}</td>
                    <td>{item_data["saldo_inicial"]}</td>
                    <td>{item_data["entradas"]}</td>
                    <td>{item_data["saidas"]}</td>
                    <td>{item_data["saldo_final"]}</td>
                </tr>
            """
        
        html_content += """
            </tbody>
        </table>
        """
    
    # Fechar o HTML
    html_content += """
        <div class="footer">
            Sistema de Almoxarifado - Relatório Mensal por Natureza de Despesa
        </div>
    </body>
    </html>
    """
    
    # Gerar o PDF
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    css = CSS(string="""
        @page {
            size: A4;
            margin: 1cm;
        }
        @font-face {
            font-family: 'Arial';
            src: local('Arial');
        }
    """, font_config=font_config)
    
    pdf_buffer = io.BytesIO()
    html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
    pdf_buffer.seek(0)
    
    # Criar resposta com o PDF
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_mensal_nd_{mes_ano_str}.pdf'
    
    return response

# Função para registrar o Blueprint na aplicação Flask
def init_app(app):
    app.register_blueprint(relatorios_bp)

# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from models import db, Item, Grupo, NaturezaDespesa
from sqlalchemy import func, distinct
import os

# Criação do blueprint
item_bp = Blueprint('item_bp', __name__, url_prefix='/item')

# ------------------------------ LISTAR ITENS COM PAGINAÇÃO E FILTROS ------------------------------
@item_bp.route('/itens')
@login_required
def lista_itens():
    filtro = request.args.get('filtro')
    busca = request.args.get('busca')
    busca_grupo = request.args.get('busca_grupo')
    busca_nd = request.args.get('busca_nd')
    page = request.args.get('page', 1, type=int)

    # Query base para os itens
    query = Item.query

    # Aplicar filtros
    if filtro and (busca or busca_grupo or busca_nd):
        if filtro == 'sap':
            query = query.filter(Item.codigo_sap.ilike(f'%{busca}%'))
        elif filtro == 'descricao':
            query = query.filter(Item.nome.ilike(f'%{busca}%'))
        elif filtro == 'grupo' and busca_grupo:
            query = query.filter(Item.grupo_id == busca_grupo)
        elif filtro == 'nd' and busca_nd:
            query = query.join(Grupo).filter(Grupo.natureza_despesa_id == busca_nd)

    # Carregar dados para os selects
    grupos = Grupo.query.order_by(Grupo.nome).all()
    naturezas_despesa = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()

    # Estatísticas e paginação (mantido o código existente)
    stats = db.session.query(
        func.count(distinct(Item.id)).label('total_itens'),
        func.sum(Item.valor_unitario * Item.estoque_atual).label('total_valor'),
        func.count(distinct(Item.grupo_id)).label('total_grupos'),
        func.count(distinct(Item.id)).filter(Item.estoque_atual > 0).label('total_com_estoque')
    ).first()

    itens = query.order_by(Item.nome.asc()).paginate(page=page, per_page=10)

    return render_template(
        'item/lista_itens.html',
        itens=itens,
        grupos=grupos,
        naturezas_despesa=naturezas_despesa,
        filtro=filtro,
        busca=busca,
        total_valor=stats.total_valor or 0,
        total_grupos=stats.total_grupos or 0,
        total_com_estoque=stats.total_com_estoque or 0
    )

# ------------------------------ DETALHAR ITEM ------------------------------
@item_bp.route('/detalhes/<int:id>')
@login_required
def detalhes_item(id):
    item = Item.query.get_or_404(id)
    return render_template('item/detalhar_item.html', item=item)

# ------------------------------ NOVO ITEM ------------------------------
@item_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_item():
    if request.method == 'POST':
        try:
            grupo = Grupo.query.get(int(request.form['grupo_id']))
            
            # Validações básicas
            if not request.form.get('codigo') or not request.form.get('nome'):
                flash('Código SAP e Nome são campos obrigatórios.', 'danger')
                return redirect(url_for('item_bp.novo_item'))

            item = Item(
                codigo_sap=request.form['codigo'],
                codigo_siads=request.form.get('codigo_siads'),
                nome=request.form['nome'],
                descricao=request.form.get('descricao'),
                unidade=request.form.get('unidade'),
                grupo_id=grupo.id,
                natureza_despesa_id=grupo.natureza_despesa_id,
                valor_unitario=request.form.get('valor_unitario', type=float) or 0,
                saldo_financeiro=0,
                estoque_atual=request.form.get('estoque_atual', type=float) or 0,
                estoque_minimo=request.form.get('estoque_minimo', type=float) or 0,
                localizacao=request.form.get('localizacao'),
                data_validade=datetime.strptime(request.form['data_validade'], '%Y-%m-%d') if request.form.get('data_validade') else None
            )

            # Calcula o saldo financeiro inicial
            item.saldo_financeiro = item.valor_unitario * item.estoque_atual

            db.session.add(item)
            db.session.commit()
            flash('Item cadastrado com sucesso!', 'success')
            return redirect(url_for('item_bp.lista_itens'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar item: {str(e)}', 'danger')
            return redirect(url_for('item_bp.novo_item'))

    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template('item/form_item.html', grupos=grupos, item=None)

# ------------------------------ EDITAR ITEM ------------------------------
@item_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item(id):
    item = Item.query.get_or_404(id)

    if request.method == 'POST':
        try:
            grupo = Grupo.query.get(int(request.form['grupo_id']))
            
            # Validações básicas
            if not request.form.get('codigo') or not request.form.get('nome'):
                flash('Código SAP e Nome são campos obrigatórios.', 'danger')
                return redirect(url_for('item_bp.editar_item', id=id))

            # Atualiza os dados básicos
            item.codigo_sap = request.form['codigo']
            item.codigo_siads = request.form.get('codigo_siads')
            item.nome = request.form['nome']
            item.descricao = request.form.get('descricao')
            item.unidade = request.form.get('unidade')
            item.grupo_id = grupo.id
            item.natureza_despesa_id = grupo.natureza_despesa_id
            item.estoque_minimo = request.form.get('estoque_minimo', type=float) or 0
            item.localizacao = request.form.get('localizacao')

            # Atualiza a data de validade
            data_validade_str = request.form.get('data_validade')
            if data_validade_str:
                item.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d')
            else:
                item.data_validade = None

            db.session.commit()
            flash('Item atualizado com sucesso!', 'success')
            return redirect(url_for('item_bp.lista_itens'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar item: {str(e)}', 'danger')
            return redirect(url_for('item_bp.editar_item', id=id))

    grupos = Grupo.query.order_by(Grupo.nome).all()
    return render_template('item/form_item.html', item=item, grupos=grupos)

# ------------------------------ EXCLUIR ITEM ------------------------------
@item_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_item(id):
    item = Item.query.get_or_404(id)
    try:
        if item.estoque_atual > 0 or item.saldo_financeiro > 0:
            flash('Não é possível excluir o item enquanto houver saldo em estoque.', 'danger')
            return redirect(url_for('item_bp.lista_itens'))

        db.session.delete(item)
        db.session.commit()
        flash('Item excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir item: {str(e)}', 'danger')
    
    return redirect(url_for('item_bp.lista_itens'))

# ------------------------------ EXPORTAR EXCEL ------------------------------
@item_bp.route('/exportar_excel')
@login_required
def exportar_excel():
    try:
        nd_id = request.args.get('nd')
        query = Item.query

        if nd_id:
            query = query.join(Grupo).filter(Grupo.natureza_despesa_id == nd_id)

        itens = query.order_by(Item.nome).all()

        data = [{
            'Código SAP': item.codigo_sap,
            'Código SIADS': item.codigo_siads or '',
            'Nome': item.nome,
            'Descrição': item.descricao or '',
            'Unidade': item.unidade,
            'Estoque Atual': item.estoque_atual,
            'Valor Unitário': item.valor_unitario,
            'Saldo Financeiro': item.saldo_financeiro,
            'Grupo': item.grupo.nome if item.grupo else '',
            'Natureza de Despesa': item.grupo.natureza_despesa.codigo if item.grupo and item.grupo.natureza_despesa else '',
            'Localização': item.localizacao or '',
            'Data de Validade': item.data_validade.strftime('%d/%m/%Y') if item.data_validade else ''
        } for item in itens]

        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Itens')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"itens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

    except Exception as e:
        flash(f'Erro ao exportar para Excel: {str(e)}', 'danger')
        return redirect(url_for('item_bp.lista_itens'))

# ------------------------------ EXPORTAR PDF ------------------------------
class PDFItens(FPDF):
    def header(self):
        # Logo
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 33)
        
        # Título
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Relatório de Itens', 0, 1, 'C')
        
        # Data/Hora
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'R')
        
        # Linha separadora
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def tabela_itens(self, itens):
        # Cabeçalho da tabela
        self.set_fill_color(200, 220, 255)
        self.set_font('Arial', 'B', 8)
        
        # Define larguras das colunas
        col_widths = [20, 60, 20, 20, 25, 25, 20]
        headers = ['SAP', 'Nome', 'Unid.', 'Estoque', 'Valor Unit.', 'Saldo', 'Grupo']
        
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, 'C', True)
        self.ln()

        # Dados da tabela
        self.set_font('Arial', '', 8)
        for item in itens:
            self.cell(col_widths[0], 6, item.codigo_sap, 1)
            self.cell(col_widths[1], 6, item.nome[:45], 1)
            self.cell(col_widths[2], 6, item.unidade, 1, 0, 'C')
            self.cell(col_widths[3], 6, f"{item.estoque_atual:.2f}", 1, 0, 'R')
            self.cell(col_widths[4], 6, f"R$ {item.valor_unitario:.2f}", 1, 0, 'R')
            self.cell(col_widths[5], 6, f"R$ {item.saldo_financeiro:.2f}", 1, 0, 'R')
            self.cell(col_widths[6], 6, item.grupo.nome if item.grupo else '-', 1)
            self.ln()

@item_bp.route('/exportar_pdf')
@login_required
def exportar_pdf():
    try:
        # Busca os itens
        itens = Item.query.order_by(Item.nome).all()

        # Cria o PDF
        pdf = PDFItens()
        pdf.add_page('L')  # Paisagem
        pdf.tabela_itens(itens)

        # Salva em memória
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        # Envia o arquivo
        return send_file(
            pdf_output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"itens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

    except Exception as e:
        flash(f'Erro ao gerar PDF: {str(e)}', 'danger')
        return redirect(url_for('item_bp.lista_itens'))

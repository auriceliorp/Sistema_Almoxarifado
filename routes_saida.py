# routes_saida.py
# Rotas para gerenciamento de saídas de materiais no sistema

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, SaidaMaterial, SaidaItem, Fornecedor, Item

saida_bp = Blueprint('saida_bp', __name__)

# --------------------------------------------------
# Rota para registrar nova saída de materiais
# --------------------------------------------------
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    if request.method == 'POST':
        try:
            # Coleta dados do formulário
            data_movimento = datetime.strptime(request.form['data_movimento'], '%Y-%m-%d')
            responsavel = request.form['responsavel']
            destino = request.form['destino']
            observacoes = request.form.get('observacoes')

            # Cria objeto de saída
            nova_saida = SaidaMaterial(
                data_movimento=data_movimento,
                responsavel=responsavel,
                destino=destino,
                observacoes=observacoes
            )
            db.session.add(nova_saida)
            db.session.flush()  # Garante que nova_saida.id esteja disponível

            # Coleta os itens do formulário
            itens = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            for i in range(len(itens)):
                item_id = int(itens[i])
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i])
                valor_total = quantidade * valor_unitario

                # Cria registro do item da saída
                item_saida = SaidaItem(
                    saida_id=nova_saida.id,
                    item_id=item_id,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total
                )
                db.session.add(item_saida)

                # Atualiza saldo do item
                item = Item.query.get(item_id)
                item.quantidade_estoque -= quantidade
                db.session.add(item)

            db.session.commit()
            flash('Saída registrada com sucesso.', 'success')
            return redirect(url_for('saida_bp.lista_saidas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar saída: {str(e)}', 'danger')

    # GET: exibe formulário
    itens = Item.query.order_by(Item.nome).all()
    return render_template('nova_saida.html', itens=itens)

# --------------------------------------------------
# Rota para listar todas as saídas (com filtros)
# --------------------------------------------------
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    responsavel = request.args.get('responsavel')

    # Query base
    query = SaidaMaterial.query

    # Filtro por data
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(SaidaMaterial.data_movimento >= data_inicio_dt)
        except ValueError:
            pass

    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(SaidaMaterial.data_movimento <= data_fim_dt)
        except ValueError:
            pass

    # Filtro por responsável
    if responsavel:
        query = query.filter(SaidaMaterial.responsavel.ilike(f'%{responsavel}%'))

    # Lista ordenada
    saidas = query.order_by(SaidaMaterial.data_movimento.desc()).all()

    return render_template('lista_saida.html', saidas=saidas)

# --------------------------------------------------
# Rota para visualizar a requisição de saída (PDF/HTML)
# --------------------------------------------------
@saida_bp.route('/saida/<int:saida_id>')
@login_required
def visualizar_saida(saida_id):
    saida = SaidaMaterial.query.get_or_404(saida_id)
    itens = SaidaItem.query.filter_by(saida_id=saida_id).all()
    return render_template('requisicao_saida.html', saida=saida, itens=itens)
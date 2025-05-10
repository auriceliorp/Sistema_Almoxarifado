# routes_saida.py
# Rotas para movimentações de saída de materiais

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Item, SaidaMaterial, SaidaItem
from datetime import datetime

# Criação do blueprint
saida_bp = Blueprint('saida_bp', __name__)

# -------------------- ROTA: Lista de saídas --------------------
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    # Busca todas as saídas cadastradas
    saidas = SaidaMaterial.query.order_by(SaidaMaterial.data_movimento.desc()).all()
    return render_template('lista_saida.html', saidas=saidas)

# -------------------- ROTA: Cadastro de nova saída --------------------
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    # Busca todos os itens disponíveis
    itens = Item.query.all()

    if request.method == 'POST':
        try:
            data_movimento = datetime.strptime(request.form['data_movimento'], '%Y-%m-%d')
            responsavel = request.form['responsavel']

            nova_saida = SaidaMaterial(
                data_movimento=data_movimento,
                responsavel=responsavel
            )
            db.session.add(nova_saida)
            db.session.commit()

            # Processar os itens da saída
            for i in range(len(request.form.getlist('item_id'))):
                item_id = int(request.form.getlist('item_id')[i])
                quantidade = float(request.form.getlist('quantidade')[i])
                valor_unitario = float(request.form.getlist('valor_unitario')[i])
                valor_total = quantidade * valor_unitario

                saida_item = SaidaItem(
                    saida_id=nova_saida.id,
                    item_id=item_id,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total
                )

                db.session.add(saida_item)

                # Atualizar o saldo do item (diminuindo)
                item = Item.query.get(item_id)
                item.quantidade_estoque -= quantidade
                db.session.commit()

            flash('Saída registrada com sucesso!', 'success')
            return redirect(url_for('saida_bp.lista_saidas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao registrar a saída: {str(e)}', 'danger')

    return render_template('nova_saida.html', itens=itens)

# -------------------- ROTA: Requisição de saída personalizada --------------------
@saida_bp.route('/requisicao_saida/<int:saida_id>')
@login_required
def requisicao_saida(saida_id):
    saida = SaidaMaterial.query.get_or_404(saida_id)
    itens_saida = SaidaItem.query.filter_by(saida_id=saida.id).all()
    return render_template('requisicao_saida.html', saida=saida, itens=itens_saida)
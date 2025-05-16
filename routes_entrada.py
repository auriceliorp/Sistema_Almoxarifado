# routes_entrada.py
# Rotas para entrada de materiais, incluindo atualização de saldo de itens e valor da natureza de despesa

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app_render import db
from models import Fornecedor, Item, EntradaMaterial, EntradaItem, NaturezaDespesa
from datetime import datetime
from sqlalchemy import func

# Criação do blueprint da entrada
entrada_bp = Blueprint('entrada_bp', __name__, template_folder='templates')


# ------------------------------ ROTA: Nova Entrada ------------------------------ #
@entrada_bp.route('/entrada/nova', methods=['GET', 'POST'])
@login_required
def nova_entrada():
    fornecedores = Fornecedor.query.all()
    itens = Item.query.all()

    if request.method == 'POST':
        try:
            # Coleta os dados do formulário
            data_movimento = datetime.strptime(request.form.get('data_movimento'), '%Y-%m-%d')
            data_nota_fiscal = datetime.strptime(request.form.get('data_nota_fiscal'), '%Y-%m-%d')
            numero_nota_fiscal = request.form.get('numero_nota_fiscal')
            fornecedor_id = request.form.get('fornecedor')

            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            # Cria o registro da entrada
            nova_entrada = EntradaMaterial(
                data_movimento=data_movimento,
                data_nota_fiscal=data_nota_fiscal,
                numero_nota_fiscal=numero_nota_fiscal,
                fornecedor_id=fornecedor_id,
                usuario_id=current_user.id
            )
            db.session.add(nova_entrada)
            db.session.flush()  # Garante que nova_entrada.id esteja disponível

            # Laço para adicionar itens da entrada
            for i in range(len(item_ids)):
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue

                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i])
                item = Item.query.get(item_ids[i])

                if item:
                    # Cria o item vinculado à entrada
                    entrada_item = EntradaItem(
                        entrada_id=nova_entrada.id,
                        item_id=item.id,
                        quantidade=quantidade,
                        valor_unitario=valor_unitario
                    )
                    db.session.add(entrada_item)

                    # Atualiza o saldo do item
                    item.estoque_atual += quantidade
                    item.saldo_financeiro += quantidade * valor_unitario
                    if item.estoque_atual > 0:
                        item.valor_unitario = item.saldo_financeiro / item.estoque_atual

                    # Atualiza o valor da natureza de despesa vinculada ao grupo do item
                    if item.grupo and item.grupo.natureza_despesa:
                        item.grupo.natureza_despesa.valor += quantidade * valor_unitario

            db.session.commit()
            flash('Entrada registrada com sucesso.', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar entrada: {e}', 'danger')
            print(e)

    return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens)


# ------------------------------ ROTA: Lista de Entradas ------------------------------ #
@entrada_bp.route('/entrada/lista')
@login_required
def lista_entradas():
    filtro = request.args.get('filtro')
    busca = request.args.get('busca', '').lower()

    entradas_query = EntradaMaterial.query.join(Fornecedor)

    if busca:
        if filtro == 'nota':
            entradas_query = entradas_query.filter(func.lower(EntradaMaterial.numero_nota_fiscal).like(f"%{busca}%"))
        elif filtro == 'fornecedor':
            entradas_query = entradas_query.filter(func.lower(Fornecedor.nome).like(f"%{busca}%"))
        elif filtro == 'data':
            try:
                data_formatada = datetime.strptime(busca, '%d/%m/%Y').date()
                entradas_query = entradas_query.filter(EntradaMaterial.data_movimento == data_formatada)
            except ValueError:
                flash('Formato de data inválido. Use dd/mm/aaaa.', 'warning')

    entradas = entradas_query.order_by(EntradaMaterial.data_movimento.desc()).all()
    return render_template('lista_entrada.html', entradas=entradas)


# ------------------------------ ROTA: Visualizar Entrada ------------------------------ #
@entrada_bp.route('/entrada/<int:entrada_id>')
@login_required
def visualizar_entrada(entrada_id):
    entrada = EntradaMaterial.query.get_or_404(entrada_id)
    itens = EntradaItem.query.filter_by(entrada_id=entrada_id).all()
    return render_template('visualizar_entrada.html', entrada=entrada, itens=itens)

# routes_entrada.py
# Rotas para entrada de materiais, incluindo múltiplos itens por entrada

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Fornecedor, Item, EntradaMaterial, EntradaItem

entrada_bp = Blueprint('entrada_bp', __name__, url_prefix='/entrada')

# ---------------- ROTA: Listar Entradas ---------------- #
@entrada_bp.route('/lista')
@login_required
def lista_entradas():
    entradas = EntradaMaterial.query.order_by(EntradaMaterial.data_movimento.desc()).all()
    return render_template('lista_entrada.html', entradas=entradas, usuario=current_user)

# ---------------- ROTA: Nova Entrada ---------------- #
@entrada_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_entrada():
    if request.method == 'POST':
        try:
            # Coleta os dados do formulário
            data_movimento = datetime.strptime(request.form['data_movimento'], '%Y-%m-%d')
            data_nota_fiscal = datetime.strptime(request.form['data_nota_fiscal'], '%Y-%m-%d')
            numero_nota_fiscal = request.form['numero_nota_fiscal']
            fornecedor_id = request.form['fornecedor_id']

            # Cria o registro da entrada principal
            nova_entrada = EntradaMaterial(
                data_movimento=data_movimento,
                data_nota_fiscal=data_nota_fiscal,
                numero_nota_fiscal=numero_nota_fiscal,
                fornecedor_id=fornecedor_id,
                usuario_id=current_user.id
            )
            db.session.add(nova_entrada)
            db.session.commit()

            # Coleta os dados dos itens como listas
            itens_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            # Processa cada item inserido
            for i in range(len(itens_ids)):
                if not itens_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue  # pula se algum campo estiver em branco

                item_id = int(itens_ids[i])
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i])
                valor_total = quantidade * valor_unitario

                # Cria o registro de item da entrada
                entrada_item = EntradaItem(
                    entrada_material_id=nova_entrada.id,
                    item_id=item_id,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total
                )
                db.session.add(entrada_item)

                # Atualiza o estoque e valor do item
                item = Item.query.get(item_id)
                item.quantidade_estoque += quantidade
                item.valor_unitario = valor_unitario

                # Atualiza o valor da natureza de despesa vinculada ao grupo do item
                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor += valor_total

            db.session.commit()
            flash('Entrada de material registrada com sucesso!', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar entrada: {str(e)}', 'danger')
            return redirect(url_for('entrada_bp.nova_entrada'))

    # GET: renderiza o formulário
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    itens = Item.query.order_by(Item.nome).all()
    return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens, usuario=current_user)
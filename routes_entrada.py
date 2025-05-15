# routes_entrada.py
# Rotas para entrada de materiais, incluindo múltiplos itens por entrada

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Fornecedor, Item, EntradaMaterial, EntradaItem

# Criação do blueprint da entrada
entrada_bp = Blueprint('entrada_bp', __name__, url_prefix='/entrada')

# ---------------- ROTA: Listar Entradas ---------------- #
@entrada_bp.route('/lista')
@login_required
def lista_entradas():
    """
    Rota para listar todas as entradas de material registradas no sistema.
    """
    entradas = EntradaMaterial.query.order_by(EntradaMaterial.data_movimento.desc()).all()
    return render_template('lista_entrada.html', entradas=entradas, usuario=current_user)

# ---------------- ROTA: Nova Entrada ---------------- #
@entrada_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_entrada():
    """
    Rota para registrar uma nova entrada de materiais no sistema.
    Permite múltiplos itens por entrada e atualiza o estoque e a natureza de despesa.
    """
    if request.method == 'POST':
        try:
            # Coleta os dados principais da entrada
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

            # Coleta os dados dos itens da entrada (listas de valores)
            itens_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            # Processa cada item da entrada
            for i in range(len(itens_ids)):
                if not itens_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue  # Pula se algum campo estiver vazio

                item_id = int(itens_ids[i])
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i])
                valor_total = quantidade * valor_unitario

                # Cria o registro do item da entrada
                entrada_item = EntradaItem(
                    entrada_material_id=nova_entrada.id,
                    item_id=item_id,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total
                )
                db.session.add(entrada_item)

                # Atualiza o estoque e o valor unitário do item
                item = Item.query.get(item_id)
                item.quantidade_estoque += quantidade
                item.valor_unitario = valor_unitario

                # Atualiza o valor total da Natureza de Despesa vinculada ao grupo do item
                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor += valor_total

            db.session.commit()
            flash('Entrada de material registrada com sucesso!', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar entrada: {str(e)}', 'danger')
            return redirect(url_for('entrada_bp.nova_entrada'))

    # Se for GET, renderiza o formulário com fornecedores e itens
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome).all()
    itens = Item.query.order_by(Item.nome).all()
    return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens, usuario=current_user)

# ---------------- ROTA: Visualizar Entrada ---------------- #
@entrada_bp.route('/visualizar/<int:entrada_id>')
@login_required
def visualizar_entrada(entrada_id):
    """
    Rota para exibir os detalhes de uma entrada de material específica.

    Parâmetros:
        entrada_id (int): ID da entrada a ser visualizada.

    Retorna:
        Template visualizar_entrada.html com os dados da entrada e seus itens.
    """
    # Consulta a entrada pelo ID ou retorna 404 se não existir
    entrada = EntradaMaterial.query.get_or_404(entrada_id)

    # Busca os itens relacionados à entrada
    itens = EntradaItem.query.filter_by(entrada_material_id=entrada.id).all()

    # Renderiza o template com os dados da entrada e itens
    return render_template(
        'visualizar_entrada.html',
        entrada=entrada,
        itens=itens,
        usuario=current_user
    )
# routes_entrada.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Fornecedor, Item, EntradaMaterial, EntradaItem
from datetime import datetime

# Cria o blueprint para entrada de materiais
entrada_bp = Blueprint('entrada_bp', __name__, template_folder='templates')

# Rota para exibir o formulário de nova entrada
@entrada_bp.route('/entrada/nova', methods=['GET', 'POST'])
@login_required
def nova_entrada():
    # Busca fornecedores e itens cadastrados para o formulário
    fornecedores = Fornecedor.query.all()
    itens = Item.query.all()

    if request.method == 'POST':
        try:
            # Coleta dados do formulário principal
            data_movimento = datetime.strptime(request.form.get('data_movimento'), '%Y-%m-%d')
            data_nota_fiscal = datetime.strptime(request.form.get('data_nota_fiscal'), '%Y-%m-%d')
            numero_nota_fiscal = request.form.get('numero_nota_fiscal')
            fornecedor_id = request.form.get('fornecedor')

            # Cria o registro de entrada de material
            nova_entrada = EntradaMaterial(
                data_movimento=data_movimento,
                data_nota_fiscal=data_nota_fiscal,
                numero_nota_fiscal=numero_nota_fiscal,
                fornecedor_id=fornecedor_id
            )
            db.session.add(nova_entrada)
            db.session.flush()  # Garante que nova_entrada.id esteja disponível

            # Coleta os dados dos itens
            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            for i in range(len(item_ids)):
                if item_ids[i] and quantidades[i] and valores_unitarios[i]:
                    entrada_item = EntradaItem(
                        entrada_material_id=nova_entrada.id,
                        item_id=item_ids[i],
                        quantidade=int(quantidades[i]),
                        valor_unitario=float(valores_unitarios[i])
                    )
                    db.session.add(entrada_item)

            db.session.commit()
            flash('Entrada de material registrada com sucesso.', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar entrada: {str(e)}', 'danger')

    return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens)

# Rota para listar entradas registradas
@entrada_bp.route('/entrada/lista')
@login_required
def lista_entradas():
    entradas = EntradaMaterial.query.order_by(EntradaMaterial.data_cadastro.desc()).all()
    return render_template('lista_entrada.html', entradas=entradas)

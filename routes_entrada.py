# routes_entrada.py (versão corrigida com validações e prints explicativos)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app_render import db  # Importa a instância correta do SQLAlchemy
from models import Fornecedor, Item, EntradaMaterial, EntradaItem
from datetime import datetime

# Criação do blueprint para rotas de entrada de material
entrada_bp = Blueprint('entrada_bp', __name__, template_folder='templates')

# ------------------------------ ROTA: Nova Entrada ------------------------------
@entrada_bp.route('/entrada/nova', methods=['GET', 'POST'])
@login_required
def nova_entrada():
    # Carrega dados para o formulário (fornecedores e itens disponíveis)
    fornecedores = Fornecedor.query.all()
    itens = Item.query.all()

    # Trata o envio do formulário (POST)
    if request.method == 'POST':
        try:
            # Coleta dados principais do formulário
            data_movimento_str = request.form.get('data_movimento')
            data_nota_str = request.form.get('data_nota_fiscal')
            numero_nota_fiscal = request.form.get('numero_nota_fiscal')
            fornecedor_id = request.form.get('fornecedor')

            # Conversão de datas (validação básica)
            data_movimento = datetime.strptime(data_movimento_str, '%Y-%m-%d')
            data_nota_fiscal = datetime.strptime(data_nota_str, '%Y-%m-%d')

            # Criação do registro principal da entrada
            nova_entrada = EntradaMaterial(
                data_movimento=data_movimento,
                data_nota_fiscal=data_nota_fiscal,
                numero_nota_fiscal=numero_nota_fiscal,
                fornecedor_id=fornecedor_id
            )
            db.session.add(nova_entrada)
            db.session.flush()  # Permite obter o ID da entrada antes do commit

            # Coleta e processa os itens inseridos no formulário
            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            print(">>> Itens recebidos:")
            for i in range(len(item_ids)):
                print(f"Item {i+1}: ID={item_ids[i]}, Quantidade={quantidades[i]}, Valor Unitário={valores_unitarios[i]}")

                # Ignora linhas incompletas
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    print(f"Item {i+1} incompleto. Pulando.")
                    continue

                # Validação de dados
                try:
                    quantidade = int(quantidades[i])
                    valor_unitario = float(valores_unitarios[i])
                except ValueError:
                    flash(f'Erro no item {i+1}: valor inválido.', 'danger')
                    db.session.rollback()
                    return redirect(url_for('entrada_bp.nova_entrada'))

                # Criação do item da entrada (nome correto do campo: entrada_id)
                entrada_item = EntradaItem(
                    entrada_id=nova_entrada.id,
                    item_id=item_ids[i],
                    quantidade=quantidade,
                    valor_unitario=valor_unitario
                )
                db.session.add(entrada_item)

            # Commit final da entrada e seus itens
            db.session.commit()
            flash('Entrada de material registrada com sucesso.', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro inesperado ao registrar entrada: {str(e)}', 'danger')
            print("Erro ao salvar entrada:", str(e))

    # Renderiza a página com formulário de entrada
    return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens)


# ------------------------------ ROTA: Lista de Entradas ------------------------------
@entrada_bp.route('/entrada/lista')
@login_required
def lista_entradas():
    entradas = EntradaMaterial.query.order_by(EntradaMaterial.data_movimento.desc()).all()
    return render_template('lista_entrada.html', entradas=entradas)

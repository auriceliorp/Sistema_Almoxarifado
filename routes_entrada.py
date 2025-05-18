routes_entrada.py

Rotas para entrada de materiais, com filtro, paginação e auditoria (inserção e estorno)

------------------------- IMPORTAÇÕES -------------------------

from flask import Blueprint, render_template, request, redirect, url_for, flash from flask_login import login_required, current_user from datetime import datetime

from app_render import db from models import Fornecedor, Item, EntradaMaterial, EntradaItem from utils.auditoria import registrar_auditoria

------------------------- BLUEPRINT -------------------------

entrada_bp = Blueprint('entrada_bp', name, template_folder='templates')

------------------------- ROTA: NOVA ENTRADA -------------------------

@entrada_bp.route('/entrada/nova', methods=['GET', 'POST']) @login_required def nova_entrada(): fornecedores = Fornecedor.query.all() itens = Item.query.all()

if request.method == 'POST':
    try:
        data_movimento = datetime.strptime(request.form.get('data_movimento'), '%Y-%m-%d')
        data_nota_fiscal = datetime.strptime(request.form.get('data_nota_fiscal'), '%Y-%m-%d')
        numero_nota_fiscal = request.form.get('numero_nota_fiscal')
        fornecedor_id = request.form.get('fornecedor')

        item_ids = request.form.getlist('item_id[]')
        quantidades = request.form.getlist('quantidade[]')
        valores_unitarios = request.form.getlist('valor_unitario[]')

        nova_entrada = EntradaMaterial(
            data_movimento=data_movimento,
            data_nota_fiscal=data_nota_fiscal,
            numero_nota_fiscal=numero_nota_fiscal,
            fornecedor_id=fornecedor_id,
            usuario_id=current_user.id
        )
        db.session.add(nova_entrada)
        db.session.flush()  # Garante o ID da entrada para referências

        itens_dados = []  # Lista para armazenar dados dos itens para auditoria

        for i in range(len(item_ids)):
            if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                continue

            quantidade = int(quantidades[i])
            valor_unitario = float(valores_unitarios[i])
            item = Item.query.get(item_ids[i])

            if item:
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

                # Atualiza o valor da natureza de despesa
                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor += quantidade * valor_unitario

                # Registra os dados do item para auditoria
                itens_dados.append({
                    'item_id': item.id,
                    'quantidade': quantidade,
                    'valor_unitario': valor_unitario
                })

        # Registra auditoria da inserção da entrada
        registrar_auditoria(
            acao='insercao',
            tabela='entrada_material',
            registro_id=nova_entrada.id,
            dados_antes=None,
            dados_depois={
                'entrada': {
                    'id': nova_entrada.id,
                    'numero_nota_fiscal': nova_entrada.numero_nota_fiscal,
                    'data_movimento': nova_entrada.data_movimento.strftime('%Y-%m-%d'),
                    'fornecedor_id': nova_entrada.fornecedor_id,
                    'usuario_id': nova_entrada.usuario_id
                },
                'itens': itens_dados
            }
        )

        db.session.commit()
        flash('Entrada registrada com sucesso.', 'success')
        return redirect(url_for('entrada_bp.lista_entradas'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar entrada: {e}', 'danger')
        print(e)

return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens)


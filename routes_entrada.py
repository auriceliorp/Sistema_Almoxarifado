# routes_entrada.py
# Rotas para entrada de materiais, com filtro, paginação, visualização, estorno e auditoria

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal  # ✅ Importa o Decimal!

from extensoes import db
from models import Fornecedor, Item, EntradaMaterial, EntradaItem
from utils.auditoria import registrar_auditoria

# ------------------------- BLUEPRINT ------------------------- #
entrada_bp = Blueprint('entrada_bp', __name__, template_folder='templates')


# ------------------------- ROTA: NOVA ENTRADA ------------------------- #
@entrada_bp.route('/entrada/nova', methods=['GET', 'POST'])
@login_required
def nova_entrada():
    fornecedores = Fornecedor.query.all()
    itens = Item.query.all()

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
                usuario_id=current_user.id,
                estornada=False
            )
            db.session.add(nova_entrada)
            db.session.flush()

            for i in range(len(item_ids)):
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue

                quantidade = int(quantidades[i])
                valor_unitario = Decimal(valores_unitarios[i])  # ✅ Converte para Decimal
                item = Item.query.get(item_ids[i])

                if item:
                    entrada_item = EntradaItem(
                        entrada_id=nova_entrada.id,
                        item_id=item.id,
                        quantidade=quantidade,
                        valor_unitario=valor_unitario
                    )
                    db.session.add(entrada_item)

                    # ✅ Atualiza usando Decimal
                    item.estoque_atual += quantidade
                    item.saldo_financeiro += Decimal(quantidade) * valor_unitario
                    if item.estoque_atual > 0:
                        item.valor_unitario = item.saldo_financeiro / Decimal(item.estoque_atual)
                        item.valor_medio = item.valor_unitario

                    if item.grupo and item.grupo.natureza_despesa:
                        item.grupo.natureza_despesa.valor += Decimal(quantidade) * valor_unitario

            db.session.commit()
            flash('Entrada registrada com sucesso.', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar entrada: {e}', 'danger')
            print(e)

    return render_template('nova_entrada.html', fornecedores=fornecedores, itens=itens)


# ------------------------- ROTA: LISTA DE ENTRADAS ------------------------- #
@entrada_bp.route('/entrada/lista')
@login_required
def lista_entradas():
    page = request.args.get('page', 1, type=int)
    filtro = request.args.get('filtro', 'nota')
    busca = request.args.get('busca', '').strip().lower()
    ordenar_por = request.args.get('ordenar_por', 'data_movimento')
    direcao = request.args.get('direcao', 'desc')

    query = EntradaMaterial.query.join(Fornecedor)

    if busca:
        if filtro == 'nota':
            query = query.filter(EntradaMaterial.numero_nota_fiscal.ilike(f'%{busca}%'))
        elif filtro == 'fornecedor':
            query = query.filter(Fornecedor.nome.ilike(f'%{busca}%'))
        elif filtro == 'data':
            try:
                data = datetime.strptime(busca, '%d/%m/%Y').date()
                query = query.filter(EntradaMaterial.data_movimento == data)
            except ValueError:
                flash("Data inválida. Use o formato dd/mm/aaaa.", 'warning')

    if ordenar_por == 'nota_fiscal':
        campo = EntradaMaterial.numero_nota_fiscal
    elif ordenar_por == 'fornecedor':
        campo = Fornecedor.nome
    else:
        campo = EntradaMaterial.data_movimento

    query = query.order_by(campo.asc() if direcao == 'asc' else campo.desc())

    entradas = query.paginate(page=page, per_page=10)

    return render_template(
        'lista_entrada.html',
        entradas=entradas,
        filtro=filtro,
        busca=busca,
        ordenar_por=ordenar_por,
        direcao=direcao
    )


# ------------------------- ROTA: VISUALIZAR ENTRADA ------------------------- #
@entrada_bp.route('/entrada/<int:entrada_id>')
@login_required
def visualizar_entrada(entrada_id):
    entrada = EntradaMaterial.query.get_or_404(entrada_id)
    itens = EntradaItem.query.filter_by(entrada_id=entrada_id).all()
    return render_template('visualizar_entrada.html', entrada=entrada, itens=itens)


# ------------------------- ROTA: ESTORNAR ENTRADA COM AUDITORIA ------------------------- #
@entrada_bp.route('/entrada/estornar/<int:entrada_id>', methods=['POST'])
@login_required
def estornar_entrada(entrada_id):
    entrada = EntradaMaterial.query.get_or_404(entrada_id)

    if entrada.estornada:
        flash('Esta entrada já foi estornada anteriormente.', 'warning')
        return redirect(url_for('entrada_bp.lista_entradas'))

    itens = EntradaItem.query.filter_by(entrada_id=entrada_id).all()

    try:
        dados_antes = {
            'entrada': {
                'id': entrada.id,
                'numero_nota_fiscal': entrada.numero_nota_fiscal,
                'data_movimento': entrada.data_movimento.strftime('%Y-%m-%d'),
                'fornecedor_id': entrada.fornecedor_id,
                'usuario_id': entrada.usuario_id
            },
            'itens': [
                {
                    'item_id': ei.item_id,
                    'quantidade': ei.quantidade,
                    'valor_unitario': float(ei.valor_unitario)
                } for ei in itens
            ]
        }

        for entrada_item in itens:
            item = Item.query.get(entrada_item.item_id)
            if item:
                if item.estoque_atual < entrada_item.quantidade:
                    flash(f'Estoque insuficiente para estornar item {item.nome}.', 'danger')
                    return redirect(url_for('entrada_bp.lista_entradas'))

                item.estoque_atual -= entrada_item.quantidade
                item.saldo_financeiro -= Decimal(entrada_item.quantidade) * entrada_item.valor_unitario
                if item.estoque_atual > 0:
                    item.valor_unitario = item.saldo_financeiro / Decimal(item.estoque_atual)
                    item.valor_medio = item.valor_unitario
                else:
                    item.valor_unitario = 0.0
                    item.valor_medio = 0.0

                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor -= Decimal(entrada_item.quantidade) * entrada_item.valor_unitario

        entrada.estornada = True

        registrar_auditoria(
            acao='estorno',
            tabela='entrada_material',
            registro_id=entrada.id,
            dados_antes=dados_antes,
            dados_depois=None
        )

        db.session.commit()
        flash('Entrada estornada com sucesso.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao estornar entrada: {e}', 'danger')
        print(e)

    return redirect(url_for('entrada_bp.lista_entradas'))

# ------------------------- ROTA: EDITAR ENTRADA COM AUDITORIA ------------------------- #
@entrada_bp.route('/entrada/editar/<int:entrada_id>', methods=['GET', 'POST'])
@login_required
def editar_entrada(entrada_id):
    entrada = EntradaMaterial.query.get_or_404(entrada_id)
    fornecedores = Fornecedor.query.all()
    itens = Item.query.all()
    itens_entrada = EntradaItem.query.filter_by(entrada_id=entrada_id).all()

    if request.method == 'POST':
        try:
            # Salva o estado atual antes da edição
            dados_antes = {
                'data_movimento': entrada.data_movimento.strftime('%Y-%m-%d'),
                'data_nota_fiscal': entrada.data_nota_fiscal.strftime('%Y-%m-%d'),
                'numero_nota_fiscal': entrada.numero_nota_fiscal,
                'fornecedor_id': entrada.fornecedor_id,
                'usuario_id': entrada.usuario_id,
            }

            # Atualiza os campos da entrada
            entrada.data_movimento = datetime.strptime(request.form.get('data_movimento'), '%Y-%m-%d')
            entrada.data_nota_fiscal = datetime.strptime(request.form.get('data_nota_fiscal'), '%Y-%m-%d')
            entrada.numero_nota_fiscal = request.form.get('numero_nota_fiscal')
            entrada.fornecedor_id = request.form.get('fornecedor')

            # Monta o estado depois da edição
            dados_depois = {
                'data_movimento': entrada.data_movimento.strftime('%Y-%m-%d'),
                'data_nota_fiscal': entrada.data_nota_fiscal.strftime('%Y-%m-%d'),
                'numero_nota_fiscal': entrada.numero_nota_fiscal,
                'fornecedor_id': entrada.fornecedor_id,
                'usuario_id': entrada.usuario_id,
            }

            # Registra a auditoria
            registrar_auditoria(
                acao='edicao',
                tabela='entrada_material',
                registro_id=entrada.id,
                dados_antes=dados_antes,
                dados_depois=dados_depois
            )

            db.session.commit()
            flash('Entrada atualizada com sucesso.', 'success')
            return redirect(url_for('entrada_bp.lista_entradas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao editar entrada: {e}', 'danger')
            print(e)

    return render_template('editar_entrada.html', entrada=entrada, fornecedores=fornecedores, itens=itens, itens_entrada=itens_entrada)


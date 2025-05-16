# routes_saida.py
# Rotas para saída de materiais com geração automática de número de documento, débito em ND e paginação com filtros no backend

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app_render import db
from models import Item, SaidaMaterial, SaidaItem, Usuario, UnidadeLocal
from datetime import date

# Criação do blueprint
saida_bp = Blueprint('saida_bp', __name__)

# ------------------------------ LISTAR SAÍDAS COM PAGINAÇÃO E FILTRO ------------------------------ #
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    # Parâmetros de filtro
    filtro = request.args.get('filtro', '')
    busca = request.args.get('busca', '').lower()
    page = request.args.get('page', 1, type=int)

    # Base da consulta
    query = SaidaMaterial.query.join(Usuario, SaidaMaterial.solicitante).outerjoin(UnidadeLocal, Usuario.unidade_local)

    # Aplicação dos filtros
    if filtro and busca:
        if filtro == 'id':
            query = query.filter(SaidaMaterial.id == busca)
        elif filtro == 'data':
            try:
                dia, mes, ano = map(int, busca.split('/'))
                query = query.filter(SaidaMaterial.data_movimento == date(ano, mes, dia))
            except:
                flash("Data inválida. Use o formato DD/MM/AAAA.", "warning")
        elif filtro == 'responsavel':
            query = query.join(SaidaMaterial.usuario).filter(Usuario.nome.ilike(f'%{busca}%'))
        elif filtro == 'solicitante':
            query = query.filter(Usuario.nome.ilike(f'%{busca}%'))
        elif filtro == 'setor':
            query = query.filter(UnidadeLocal.descricao.ilike(f'%{busca}%'))

    # Ordenação e paginação
    saidas = query.order_by(SaidaMaterial.data_movimento.desc()).paginate(page=page, per_page=10)

    return render_template(
        'lista_saida.html',
        saidas=saidas,
        filtro=filtro,
        busca=busca
    )

# ------------------------------ NOVA SAÍDA ------------------------------ #
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    itens = Item.query.all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    if request.method == 'POST':
        try:
            # Dados do formulário
            data_movimento = date.fromisoformat(request.form.get('data_movimento'))
            numero_documento = request.form.get('numero_documento')
            observacao = request.form.get('observacao')
            solicitante_id = int(request.form.get('solicitante'))

            # Criação da saída
            nova_saida = SaidaMaterial(
                data_movimento=data_movimento,
                numero_documento=numero_documento,
                observacao=observacao,
                usuario_id=current_user.id,
                solicitante_id=solicitante_id
            )
            db.session.add(nova_saida)
            db.session.flush()  # necessário para pegar o ID da saída

            # Itens enviados
            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            for i in range(len(item_ids)):
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue

                item = Item.query.get(int(item_ids[i]))
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i].replace(',', '.'))

                # Validação do estoque
                if item.estoque_atual < quantidade:
                    flash(f"Estoque insuficiente para '{item.nome}'", 'danger')
                    db.session.rollback()
                    return redirect(url_for('saida_bp.nova_saida'))

                # Atualização de estoque e saldo financeiro
                item.estoque_atual -= quantidade
                item.saldo_financeiro -= quantidade * valor_unitario

                # Débito na natureza de despesa
                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor -= quantidade * valor_unitario

                # Criação do item de saída
                saida_item = SaidaItem(
                    item_id=item.id,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    saida_id=nova_saida.id
                )
                db.session.add(saida_item)

            db.session.commit()
            flash('Saída registrada com sucesso.', 'success')
            return redirect(url_for('saida_bp.lista_saidas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar saída: {e}', 'danger')
            print(e)

    # Geração automática do número do documento (ex: 001/2025)
    ano_atual = date.today().year
    ultima_saida = SaidaMaterial.query.order_by(SaidaMaterial.id.desc()).first()
    if ultima_saida and ultima_saida.numero_documento and '/' in ultima_saida.numero_documento:
        try:
            ultimo_num = int(ultima_saida.numero_documento.split('/')[0])
            numero_documento = f"{ultimo_num + 1:03}/{ano_atual}"
        except:
            numero_documento = f"001/{ano_atual}"
    else:
        numero_documento = f"001/{ano_atual}"

    return render_template(
        'nova_saida.html',
        itens=itens,
        usuarios=usuarios,
        numero_documento=numero_documento
    )

# ------------------------------ REQUISIÇÃO (IMPRESSÃO) ------------------------------ #
@saida_bp.route('/requisicao/<int:saida_id>')
@login_required
def requisicao_saida(saida_id):
    saida = SaidaMaterial.query.get_or_404(saida_id)
    return render_template('requisicao_saida.html', saida=saida)

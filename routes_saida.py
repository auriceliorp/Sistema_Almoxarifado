# routes_saida.py
# Rotas para saída de materiais com geração automática de número de documento e débito na natureza de despesa

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app_render import db
from models import Item, SaidaMaterial, SaidaItem, Usuario
from datetime import date

# Define o blueprint para as rotas de saída
saida_bp = Blueprint('saida_bp', __name__)

# Rota para listar todas as saídas registradas
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    saidas = SaidaMaterial.query.order_by(SaidaMaterial.data_movimento.desc()).all()
    return render_template('lista_saida.html', saidas=saidas)

# Rota para registrar uma nova saída de material
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    itens = Item.query.all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    # Processa o envio do formulário
    if request.method == 'POST':
        try:
            data_movimento = date.fromisoformat(request.form.get('data_movimento'))
            numero_documento = request.form.get('numero_documento')
            observacao = request.form.get('observacao')
            solicitante_id = int(request.form.get('solicitante'))

            # Cria a saída principal
            nova_saida = SaidaMaterial(
                data_movimento=data_movimento,
                numero_documento=numero_documento,
                observacao=observacao,
                usuario_id=current_user.id,      # quem está operando
                solicitante_id=solicitante_id    # quem está solicitando
            )
            db.session.add(nova_saida)
            db.session.flush()  # necessário para obter o ID da nova saída

            # Recupera dados dos itens
            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            # Itera sobre os itens
            for i in range(len(item_ids)):
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue

                item = Item.query.get(int(item_ids[i]))
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i].replace(',', '.'))

                # Valida o estoque
                if item.estoque_atual < quantidade:
                    flash(f"Estoque insuficiente para '{item.nome}'", 'danger')
                    db.session.rollback()
                    return redirect(url_for('saida_bp.nova_saida'))

                # Atualiza o item (estoque e saldo)
                item.estoque_atual -= quantidade
                item.saldo_financeiro -= quantidade * valor_unitario

                # Debita da natureza de despesa associada ao grupo do item
                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor -= quantidade * valor_unitario

                # Cria o item da saída
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

    # Geração automática do número do documento no formato 001/ANO
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

    # Renderiza o formulário de nova saída
    return render_template(
        'nova_saida.html',
        itens=itens,
        usuarios=usuarios,
        numero_documento=numero_documento
    )

# Gera o HTML da requisição de saída (com visualização para impressão)
@saida_bp.route('/requisicao/<int:saida_id>')
@login_required
def requisicao_saida(saida_id):
    saida = SaidaMaterial.query.get_or_404(saida_id)
    return render_template('requisicao_saida.html', saida=saida)

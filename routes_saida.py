# routes_saida.py
# Rotas para saída de materiais com débito na natureza de despesa e registro de solicitante

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app_render import db
from models import Item, SaidaMaterial, SaidaItem, Usuario
from datetime import date

saida_bp = Blueprint('saida_bp', __name__)

# ------------------------------ LISTAGEM DAS SAÍDAS ------------------------------ #
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    saidas = SaidaMaterial.query.order_by(SaidaMaterial.data_movimento.desc()).all()
    return render_template('lista_saida.html', saidas=saidas)

# ------------------------------ NOVA SAÍDA DE MATERIAL ------------------------------ #
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    itens = Item.query.all()
    usuarios = Usuario.query.order_by(Usuario.nome).all()

    if request.method == 'POST':
        try:
            # Coleta os dados do formulário
            data_movimento = date.fromisoformat(request.form.get('data_movimento'))
            observacao = request.form.get('observacao')
            solicitante_id = request.form.get('solicitante_id')

            # Geração automática do número do documento
            ano_atual = date.today().year
            ultima_saida = (
                SaidaMaterial.query
                .filter(db.extract('year', SaidaMaterial.data_movimento) == ano_atual)
                .order_by(SaidaMaterial.id.desc())
                .first()
            )
            proximo_numero = 1 if not ultima_saida else ultima_saida.id + 1
            numero_documento = f'{proximo_numero:03d}/{ano_atual}'

            nova_saida = SaidaMaterial(
                data_movimento=data_movimento,
                numero_documento=numero_documento,
                observacao=observacao,
                usuario_id=current_user.id,       # quem operou
                solicitante_id=solicitante_id     # quem solicitou
            )
            db.session.add(nova_saida)
            db.session.flush()  # gera nova_saida.id

            # Processa os itens
            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            for i in range(len(item_ids)):
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue

                item = Item.query.get(int(item_ids[i]))
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i].replace(',', '.'))

                # Verifica se há estoque suficiente
                if item.estoque_atual < quantidade:
                    flash(f"Estoque insuficiente para '{item.nome}'", 'danger')
                    db.session.rollback()
                    return redirect(url_for('saida_bp.nova_saida'))

                # Atualiza estoque e saldo
                item.estoque_atual -= quantidade
                item.saldo_financeiro -= quantidade * valor_unitario

                # Atualiza valor na natureza de despesa
                if item.grupo and item.grupo.natureza_despesa:
                    item.grupo.natureza_despesa.valor -= quantidade * valor_unitario

                # Registra o item da saída
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
            flash(f'Erro: {e}', 'danger')
            print(e)

    return render_template('nova_saida.html', itens=itens, usuarios=usuarios)

# ------------------------------ REQUISIÇÃO DE SAÍDA (VISUALIZAÇÃO) ------------------------------ #
@saida_bp.route('/requisicao/<int:saida_id>')
@login_required
def requisicao_saida(saida_id):
    saida = SaidaMaterial.query.get_or_404(saida_id)
    return render_template('requisicao_saida.html', saida=saida)

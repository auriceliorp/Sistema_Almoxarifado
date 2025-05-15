# routes_saida.py
# Rotas para saída de materiais com débito na natureza de despesa

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app_render import db
from models import Item, SaidaMaterial, SaidaItem
from datetime import date, datetime

saida_bp = Blueprint('saida_bp', __name__)

# ------------------------------ LISTAGEM DE SAÍDAS ------------------------------ #
@saida_bp.route('/saidas')
@login_required
def lista_saidas():
    saidas = SaidaMaterial.query.order_by(SaidaMaterial.data_movimento.desc()).all()
    return render_template('lista_saida.html', saidas=saidas)

# ------------------------------ NOVA SAÍDA ------------------------------ #
@saida_bp.route('/nova_saida', methods=['GET', 'POST'])
@login_required
def nova_saida():
    itens = Item.query.all()

    # ---------------------- PROCESSAMENTO DO FORMULÁRIO ---------------------- #
    if request.method == 'POST':
        try:
            data_movimento = date.fromisoformat(request.form.get('data_movimento'))
            numero_documento = request.form.get('numero_documento')
            observacao = request.form.get('observacao')

            # Cria a nova saída
            nova_saida = SaidaMaterial(
                data_movimento=data_movimento,
                numero_documento=numero_documento,
                observacao=observacao,
                usuario_id=current_user.id
            )
            db.session.add(nova_saida)
            db.session.flush()

            # Captura os itens enviados
            item_ids = request.form.getlist('item_id[]')
            quantidades = request.form.getlist('quantidade[]')
            valores_unitarios = request.form.getlist('valor_unitario[]')

            for i in range(len(item_ids)):
                if not item_ids[i] or not quantidades[i] or not valores_unitarios[i]:
                    continue

                item = Item.query.get(int(item_ids[i]))
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i].replace(',', '.'))

                # Verifica estoque disponível
                if item.estoque_atual < quantidade:
                    flash(f"Estoque insuficiente para '{item.nome}'", 'danger')
                    db.session.rollback()
                    return redirect(url_for('saida_bp.nova_saida'))

                # Atualiza os dados do item
                item.estoque_atual -= quantidade
                item.saldo_financeiro -= quantidade * valor_unitario

                # Atualiza a Natureza de Despesa (débito)
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
            flash(f'Erro ao registrar saída: {e}', 'danger')
            print(e)

    # ---------------------- GERAR NÚMERO AUTOMÁTICO ---------------------- #
    ano_atual = datetime.now().year
    total_ano = SaidaMaterial.query.filter(
        db.extract('year', SaidaMaterial.data_movimento) == ano_atual
    ).count()
    numero_gerado = f"{total_ano + 1:03d}/{ano_atual}"

    return render_template(
        'nova_saida.html',
        itens=itens,
        current_user=current_user,
        numero_documento=numero_gerado,
        data_hoje=date.today().isoformat()
    )

# ------------------------------ VISUALIZAR REQUISIÇÃO ------------------------------ #
@saida_bp.route('/requisicao/<int:saida_id>')
@login_required
def requisicao_saida(saida_id):
    saida = SaidaMaterial.query.get_or_404(saida_id)
    return render_template('requisicao_saida.html', saida=saida)

# routes_saida.py
# Rotas para a funcionalidade de saída de materiais no sistema Flask

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, SaidaMaterial, SaidaItem, Item
from datetime import date

# -------------------- Cria o Blueprint --------------------
saida_bp = Blueprint('saida_bp', __name__, url_prefix='/saida')

# -------------------- Lista todas as saídas registradas --------------------
@saida_bp.route('/')
@login_required
def lista_saidas():
    saidas = SaidaMaterial.query.order_by(SaidaMaterial.data_movimento.desc()).all()
    return render_template('lista_saida.html', saidas=saidas)

# -------------------- Exibe o formulário de nova saída --------------------
@saida_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_saida():
    itens = Item.query.all()

    if request.method == 'POST':
        # Coleta os dados do formulário
        data_movimento = request.form.get('data_movimento') or date.today()
        numero_documento = request.form.get('numero_documento')
        observacao = request.form.get('observacao')

        # Cria o objeto de Saída
        nova_saida = SaidaMaterial(
            data_movimento=data_movimento,
            numero_documento=numero_documento,
            observacao=observacao,
            usuario_id=current_user.id
        )
        db.session.add(nova_saida)
        db.session.flush()  # Garante que nova_saida.id esteja disponível

        # Coleta os itens e registra cada um
        for i in range(1, 21):  # Permite até 20 itens por saída
            item_id = request.form.get(f'item_{i}')
            quantidade = request.form.get(f'quantidade_{i}')
            valor_unitario = request.form.get(f'valor_unitario_{i}')

            if item_id and quantidade and valor_unitario:
                item = Item.query.get(int(item_id))

                # Atualiza o estoque (lógica inversa: subtrai)
                item.quantidade_estoque -= int(quantidade)
                db.session.add(item)

                saida_item = SaidaItem(
                    item_id=item.id,
                    quantidade=int(quantidade),
                    valor_unitario=float(valor_unitario),
                    saida_id=nova_saida.id
                )
                db.session.add(saida_item)

        db.session.commit()
        flash('Saída registrada com sucesso!', 'success')
        return redirect(url_for('saida_bp.lista_saidas'))

    return render_template('nova_saida.html', itens=itens)
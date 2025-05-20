# routes_nd.py
# Rotas para gerenciamento de Natureza de Despesa (ND)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import NaturezaDespesa

# Criação do blueprint
nd_bp = Blueprint('nd_bp', __name__, url_prefix='/nd')


# ------------------------------ LISTAGEM ------------------------------ #
@nd_bp.route('/')
@login_required
def lista_nd():
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('partials/nd/lista_nd.html', nds=nds)


# ------------------------------ NOVA ND ------------------------------ #
@nd_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def nova_nd():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')

        if not codigo or not nome:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('nd_bp.nova_nd'))

        nova = NaturezaDespesa(codigo=codigo, nome=nome)
        db.session.add(nova)
        db.session.commit()
        flash('Natureza de Despesa cadastrada com sucesso!')
        return redirect(url_for('main.dashboard_organizacao'))

    return render_template('partials/nd/form_nd.html', nd=None)


# ------------------------------ EDITAR ND ------------------------------ #
@nd_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)

    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')

        if not codigo or not nome:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('nd_bp.editar_nd', id=id))

        nd.codigo = codigo
        nd.nome = nome
        db.session.commit()
        flash('Natureza de Despesa atualizada com sucesso!')
        return redirect(url_for('main.dashboard_organizacao'))

    return render_template('partials/nd/form_nd.html', nd=nd)


# ------------------------------ EXCLUIR ND ------------------------------ #
@nd_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    db.session.delete(nd)
    db.session.commit()
    flash('Natureza de Despesa excluída com sucesso!')
    return redirect(url_for('main.dashboard_organizacao'))


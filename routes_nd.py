# routes_nd.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import NaturezaDespesa

# Criação do blueprint da natureza de despesa
nd_bp = Blueprint('nd_bp', __name__, url_prefix='/nd')

# ------------------------- ROTA: LISTAR ND ------------------------- #
@nd_bp.route('/')
@login_required
def lista_nd():
    """
    Lista todas as Naturezas de Despesa cadastradas.
    """
    nds = NaturezaDespesa.query.all()
    return render_template('partials/nd/lista_nd.html', nds=nds)

# ------------------------- ROTA: NOVA ND ------------------------- #
@nd_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_nd():
    """
    Cadastra uma nova Natureza de Despesa.
    """
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        if not codigo or not nome:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('nd_bp.novo_nd'))
        nova_nd = NaturezaDespesa(codigo=codigo, nome=nome)
        db.session.add(nova_nd)
        db.session.commit()
        flash('Natureza de Despesa cadastrada com sucesso!')
        return redirect(url_for('nd_bp.lista_nd'))
    return render_template('partials/nd/form_nd.html')

# ------------------------- ROTA: EDITAR ND ------------------------- #
@nd_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_nd(id):
    """
    Edita uma Natureza de Despesa existente.
    """
    nd = NaturezaDespesa.query.get_or_404(id)
    if request.method == 'POST':
        nd.codigo = request.form.get('codigo')
        nd.nome = request.form.get('nome')
        db.session.commit()
        flash('Natureza de Despesa atualizada com sucesso!')
        return redirect(url_for('nd_bp.lista_nd'))
    return render_template('partials/nd/form_nd.html', nd=nd)


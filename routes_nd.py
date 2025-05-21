# routes_nd.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from extensoes import db
from models import NaturezaDespesa

# Criação do blueprint da natureza de despesa
nd_bp = Blueprint('nd_bp', __name__, url_prefix='/nd')


# ------------------------- ROTA: LISTAR ND ------------------------- #
@nd_bp.route('/')
@login_required
def lista_nd():
    """
    Lista todas as Naturezas de Despesa cadastradas.
    Esta rota é carregada dinamicamente via AJAX na aba de Organização.
    """
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('partials/nd/lista_nd.html', nds=nds)


# ------------------------- ROTA: NOVA ND ------------------------- #
@nd_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_nd():
    """
    Exibe o formulário e cadastra uma nova ND.
    """
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')

        if not codigo or not nome:
            flash('Preencha todos os campos obrigatórios.')
            return render_template('partials/nd/form_nd.html')

        # Verifica se já existe ND com mesmo código
        existente = NaturezaDespesa.query.filter_by(codigo=codigo).first()
        if existente:
            flash('Já existe uma Natureza de Despesa com este código.')
            return render_template('partials/nd/form_nd.html')

        try:
            nova_nd = NaturezaDespesa(codigo=codigo, nome=nome)
            db.session.add(nova_nd)
            db.session.commit()
            nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
            flash('Natureza de Despesa cadastrada com sucesso!')
            return render_template('partials/nd/lista_nd.html', nds=nds)
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar ND: {e}')
            return render_template('partials/nd/form_nd.html')

    return render_template('partials/nd/form_nd.html')


# ------------------------- ROTA: EDITAR ND ------------------------- #
@nd_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_nd(id):
    """
    Exibe o formulário e atualiza uma ND existente.
    """
    nd = NaturezaDespesa.query.get_or_404(id)

    if request.method == 'POST':
        nd.codigo = request.form.get('codigo')
        nd.nome = request.form.get('nome')

        try:
            db.session.commit()
            nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
            flash('Natureza de Despesa atualizada com sucesso!')
            return render_template('partials/nd/lista_nd.html', nds=nds)
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar ND: {e}')
            return render_template('partials/nd/form_nd.html', nd=nd)

    return render_template('partials/nd/form_nd.html', nd=nd)

# ------------------------- ROTA: EXCLUIR ND ------------------------- #
@nd_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    try:
        db.session.delete(nd)
        db.session.commit()
        flash('Natureza de Despesa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir ND: {e}', 'danger')
    return redirect(url_for('nd_bp.lista_nd'))



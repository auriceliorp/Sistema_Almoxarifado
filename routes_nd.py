# routes_nd.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from database import db
from models import NaturezaDespesa

nd_bp = Blueprint('nd_bp', __name__, url_prefix='/nd')

@nd_bp.route('/')
@login_required
def lista_nd():
    nds = NaturezaDespesa.query.all()
    return render_template('lista_nd.html', nds=nds)

@nd_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_nd():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')

        if not codigo or not nome:
            flash('Preencha todos os campos obrigatórios!')
            return redirect(url_for('nd_bp.novo_nd'))

        nova_nd = NaturezaDespesa(codigo=codigo, nome=nome)
        db.session.add(nova_nd)
        db.session.commit()
        flash('Natureza de Despesa cadastrada com sucesso!')
        return redirect(url_for('nd_bp.lista_nd'))
    
    return render_template('form_nd.html', nd=None)

@nd_bp.route('/editar/<int:nd_id>', methods=['GET', 'POST'])
@login_required
def editar_nd(nd_id):
    nd = NaturezaDespesa.query.get_or_404(nd_id)

    if request.method == 'POST':
        nd.codigo = request.form.get('codigo')
        nd.nome = request.form.get('nome')

        if not nd.codigo or not nd.nome:
            flash('Preencha todos os campos obrigatórios!')
            return redirect(url_for('nd_bp.editar_nd', nd_id=nd_id))

        db.session.commit()
        flash('Natureza de Despesa atualizada com sucesso!')
        return redirect(url_for('nd_bp.lista_nd'))
    
    return render_template('form_nd.html', nd=nd)

@nd_bp.route('/excluir/<int:nd_id>')
@login_required
def excluir_nd(nd_id):
    nd = NaturezaDespesa.query.get_or_404(nd_id)
    db.session.delete(nd)
    db.session.commit()
    flash('Natureza de Despesa excluída com sucesso!')
    return redirect(url_for('nd_bp.lista_nd'))

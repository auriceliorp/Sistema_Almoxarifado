# routes_nd.py atualizado

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import NaturezaDespesa

nd_bp = Blueprint('nd', __name__, url_prefix='/nd')

@nd_bp.route('/')
@login_required
def lista_nd():
    nds = NaturezaDespesa.query.all()
    return render_template('nd/lista.html', nds=nds)

@nd_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_nd():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')
        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao)
        db.session.add(nova_nd)
        db.session.commit()
        flash('Natureza de Despesa cadastrada com sucesso!')
        return redirect(url_for('nd.lista_nd'))
    return render_template('nd/cadastrar.html')

@nd_bp.route('/editar/<int:nd_id>', methods=['GET', 'POST'])
@login_required
def editar_nd(nd_id):
    nd = NaturezaDespesa.query.get_or_404(nd_id)
    if request.method == 'POST':
        nd.codigo = request.form.get('codigo')
        nd.descricao = request.form.get('descricao')
        db.session.commit()
        flash('Natureza de Despesa atualizada com sucesso!')
        return redirect(url_for('nd.lista_nd'))
    return render_template('nd/editar.html', nd=nd)

@nd_bp.route('/excluir/<int:nd_id>', methods=['POST'])
@login_required
def excluir_nd(nd_id):
    nd = NaturezaDespesa.query.get_or_404(nd_id)
    db.session.delete(nd)
    db.session.commit()
    flash('Natureza de Despesa excluída com sucesso!')
    return redirect(url_for('nd.lista_nd'))

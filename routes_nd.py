# routes_nd.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from database import db
from models import NaturezaDespesa

nd = Blueprint('nd', __name__, url_prefix='/nd')

@nd.route('/')
@login_required
def lista_nd():
    nds = NaturezaDespesa.query.all()
    return render_template('lista_nd.html', nds=nds)

@nd.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_nd():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')

        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao)
        db.session.add(nova_nd)
        db.session.commit()

        flash('ND cadastrada com sucesso!', 'success')
        return redirect(url_for('nd.lista_nd'))

    return render_template('form_nd.html', nd=None)

@nd.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)

    if request.method == 'POST':
        nd.codigo = request.form.get('codigo')
        nd.descricao = request.form.get('descricao')
        db.session.commit()

        flash('ND atualizada com sucesso!', 'success')
        return redirect(url_for('nd.lista_nd'))

    return render_template('form_nd.html', nd=nd)

@nd.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_nd(id):
    nd = NaturezaDespesa.query.get_or_404(id)
    db.session.delete(nd)
    db.session.commit()

    flash('ND excluída com sucesso!', 'success')
    return redirect(url_for('nd.lista_nd'))

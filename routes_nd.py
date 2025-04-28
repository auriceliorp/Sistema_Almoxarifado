# routes_nd.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
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

        if not codigo or not descricao:
            flash('Código e descrição são obrigatórios.', 'danger')
            return redirect(url_for('nd.cadastrar_nd'))

        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao)
        db.session.add(nova_nd)
        db.session.commit()

        flash('Natureza de Despesa cadastrada com sucesso!', 'success')
        return redirect(url_for('nd.lista_nd'))

    return render_template('cadastrar_nd.html')

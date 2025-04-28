# routes_nd.py corrigido

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import NaturezaDespesa
from database import db

nd_bp = Blueprint('nd', __name__, url_prefix='/nd')

# Rota para listar todas as ND cadastradas
@nd_bp.route('/')
@login_required
def lista_nd():
    nds = NaturezaDespesa.query.order_by(NaturezaDespesa.codigo).all()
    return render_template('lista_nd.html', nds=nds)

# Rota para cadastrar nova ND
@nd_bp.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar_nd():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        descricao = request.form.get('descricao')

        if not codigo or not descricao:
            flash('Preencha todos os campos.')
            return redirect(url_for('nd.cadastrar_nd'))

        if NaturezaDespesa.query.filter_by(codigo=codigo).first():
            flash('Código de ND já cadastrado.')
            return redirect(url_for('nd.cadastrar_nd'))

        nova_nd = NaturezaDespesa(codigo=codigo, descricao=descricao)
        db.session.add(nova_nd)
        db.session.commit()

        flash('Natureza de Despesa cadastrada com sucesso!')
        return redirect(url_for('nd.lista_nd'))

    return render_template('cadastrar_nd.html')


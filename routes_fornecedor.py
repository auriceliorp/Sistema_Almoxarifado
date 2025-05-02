# routes_fornecedor.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Fornecedor  # Importa corretamente o modelo já definido

fornecedor_bp = Blueprint('fornecedor_bp', __name__, url_prefix='/fornecedor')

@fornecedor_bp.route('/')
@login_required
def lista_fornecedor():
    fornecedores = Fornecedor.query.all()
    return render_template('lista_fornecedor.html', fornecedores=fornecedores)

@fornecedor_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_fornecedor():
    if request.method == 'POST':
        nome = request.form['nome']
        cnpj = request.form['cnpj']

        if not nome or not cnpj:
            flash('Preencha todos os campos obrigatórios.')
            return redirect(url_for('fornecedor.novo_fornecedor'))

        fornecedor = Fornecedor(nome=nome, cnpj=cnpj)
        db.session.add(fornecedor)
        db.session.commit()
        flash('Fornecedor cadastrado com sucesso.')
        return redirect(url_for('fornecedor.lista_fornecedor'))

    return render_template('novo_fornecedor.html')

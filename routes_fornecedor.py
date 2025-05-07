# ------------------------------ IMPORTAÇÕES ------------------------------ #
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Fornecedor
import re  # Para validação de CNPJ


# ------------------------------ CRIAÇÃO DO BLUEPRINT ------------------------------ #
fornecedor_bp = Blueprint('fornecedor_bp', __name__, url_prefix='/fornecedor')


# ------------------------------ LISTAR FORNECEDORES ------------------------------ #
@fornecedor_bp.route('/')
@login_required
def lista_fornecedor():
    fornecedores = Fornecedor.query.all()
    return render_template('lista_fornecedor.html', fornecedores=fornecedores)


# ------------------------------ CADASTRAR NOVO FORNECEDOR ------------------------------ #
@fornecedor_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_fornecedor():
    if request.method == 'POST':
        # Coleta os dados do formulário
        nome = request.form['nome']
        cnpj = request.form['cnpj']
        email = request.form['email']
        telefone = request.form['telefone']
        celular = request.form['celular']
        endereco = request.form['endereco']
        numero = request.form['numero']
        complemento = request.form['complemento']
        cep = request.form['cep']
        inscricao_estadual = request.form['inscricao_estadual']
        inscricao_municipal = request.form['inscricao_municipal']

        # Verifica se os campos obrigatórios estão preenchidos
        if not nome or not cnpj:
            flash('Preencha os campos obrigatórios: Nome e CNPJ.', 'warning')
            return redirect(url_for('fornecedor_bp.novo_fornecedor'))

        # Validação de CNPJ simples (apenas formato)
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        if len(cnpj_limpo) != 14:
            flash('CNPJ inválido.', 'danger')
            return redirect(url_for('fornecedor_bp.novo_fornecedor'))

        # Cria o objeto fornecedor
        fornecedor = Fornecedor(
            nome=nome,
            cnpj=cnpj,
            email=email,
            telefone=telefone,
            celular=celular,
            endereco=endereco,
            numero=numero,
            complemento=complemento,
            cep=cep,
            inscricao_estadual=inscricao_estadual,
            inscricao_municipal=inscricao_municipal
        )

        # Salva no banco de dados
        db.session.add(fornecedor)
        db.session.commit()

        flash('Fornecedor cadastrado com sucesso!', 'success')
        return redirect(url_for('fornecedor_bp.lista_fornecedor'))

    return render_template('novo_fornecedor.html')


# ------------------------------ EDITAR FORNECEDOR ------------------------------ #
@fornecedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)

    if request.method == 'POST':
        fornecedor.nome = request.form['nome']
        fornecedor.cnpj = request.form['cnpj']
        fornecedor.email = request.form['email']
        fornecedor.telefone = request.form['telefone']
        fornecedor.celular = request.form['celular']
        fornecedor.endereco = request.form['endereco']
        fornecedor.numero = request.form['numero']
        fornecedor.complemento = request.form['complemento']
        fornecedor.cep = request.form['cep']
        fornecedor.inscricao_estadual = request.form['inscricao_estadual']
        fornecedor.inscricao_municipal = request.form['inscricao_municipal']

        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('fornecedor_bp.lista_fornecedor'))

    return render_template('editar_fornecedor.html', fornecedor=fornecedor)


# ------------------------------ EXCLUIR FORNECEDOR ------------------------------ #
@fornecedor_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    db.session.delete(fornecedor)
    db.session.commit()
    flash('Fornecedor excluído com sucesso!', 'success')
    return redirect(url_for('fornecedor_bp.lista_fornecedor'))


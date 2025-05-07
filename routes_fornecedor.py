# ------------------------------ IMPORTAÇÕES ------------------------------
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Fornecedor  # Importa o banco e o modelo Fornecedor

# ------------------------------ BLUEPRINT ------------------------------
# Cria o blueprint para rotas de fornecedor
fornecedor_bp = Blueprint('fornecedor_bp', __name__, url_prefix='/fornecedor')


# ------------------------------ LISTAR FORNECEDORES ------------------------------
@fornecedor_bp.route('/')
@login_required
def lista_fornecedor():
    # Consulta todos os fornecedores cadastrados
    fornecedores = Fornecedor.query.all()
    return render_template('lista_fornecedor.html', fornecedores=fornecedores)


# ------------------------------ CADASTRAR NOVO FORNECEDOR ------------------------------
@fornecedor_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_fornecedor():
    if request.method == 'POST':
        # Coleta dados do formulário
        nome = request.form['nome']
        cnpj = request.form['cnpj']
        email = request.form.get('email')
        telefone = request.form.get('telefone')

        # Validação mínima
        if not nome or not cnpj:
            flash('Preencha os campos obrigatórios: Nome e CNPJ.', 'warning')
            return redirect(url_for('fornecedor_bp.novo_fornecedor'))

        # Cria e salva o fornecedor
        fornecedor = Fornecedor(nome=nome, cnpj=cnpj, email=email, telefone=telefone)
        db.session.add(fornecedor)
        db.session.commit()

        flash('Fornecedor cadastrado com sucesso.', 'success')
        return redirect(url_for('fornecedor_bp.lista_fornecedor'))

    return render_template('novo_fornecedor.html')


# ------------------------------ EDITAR FORNECEDOR ------------------------------
@fornecedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)

    if request.method == 'POST':
        fornecedor.nome = request.form['nome']
        fornecedor.cnpj = request.form['cnpj']
        fornecedor.email = request.form.get('email')
        fornecedor.telefone = request.form.get('telefone')

        db.session.commit()
        flash('Fornecedor atualizado com sucesso.')
        return redirect(url_for('fornecedor_bp.lista_fornecedor'))

    return render_template('editar_fornecedor.html', fornecedor=fornecedor)


# ------------------------------ EXCLUIR FORNECEDOR ------------------------------
@fornecedor_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    db.session.delete(fornecedor)
    db.session.commit()
    flash('Fornecedor excluído com sucesso.')
    return redirect(url_for('fornecedor_bp.lista_fornecedor'))


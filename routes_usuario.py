# routes_usuario.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Usuario, Perfil
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import joinedload

usuario_bp = Blueprint('usuario_bp', __name__, url_prefix='/usuario')

# ------------------- LISTAGEM DE USUÁRIOS -------------------
@usuario_bp.route('/')
@login_required
def lista_usuario():
    # joinedload força o carregamento da relação 'perfil'
    usuarios = Usuario.query.options(joinedload(Usuario.perfil)).all()
    return render_template('lista_usuario.html', usuarios=usuarios)

# ------------------- CADASTRO DE NOVO USUÁRIO -------------------
@usuario_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    perfis = Perfil.query.all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        matricula = request.form.get('matricula')
        perfil_id = request.form.get('perfil_id')

        if not (nome and email and senha and perfil_id):
            flash('Todos os campos obrigatórios devem ser preenchidos!', 'warning')
            return redirect(url_for('usuario_bp.novo_usuario'))

        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash,
            matricula=matricula,
            perfil_id=perfil_id
        )

        db.session.add(novo_usuario)
        db.session.commit()

        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('usuario_bp.lista_usuario'))

    return render_template('novo_usuario.html', perfis=perfis)

# ------------------- EDIÇÃO DE USUÁRIO -------------------
@usuario_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    perfis = Perfil.query.all()

    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.matricula = request.form.get('matricula')
        usuario.perfil_id = request.form.get('perfil_id')

        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)

        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('usuario_bp.lista_usuario'))

    return render_template('editar_usuario.html', usuario=usuario, perfis=perfis)


# ------------------- EXCLUSÃO DE USUÁRIO -------------------
@usuario_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('usuario_bp.lista_usuario'))

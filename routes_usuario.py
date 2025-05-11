# routes_usuario.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from werkzeug.security import generate_password_hash
from app_render import db
from models import Usuario, Perfil, UnidadeLocal

# Criação do blueprint para rotas de usuários
usuario_bp = Blueprint('usuario_bp', __name__, url_prefix='/usuario')

# ------------------- LISTAGEM DE USUÁRIOS -------------------
@usuario_bp.route('/')
@login_required
def lista_usuarios():
    usuarios = Usuario.query.all()
    return render_template('lista_usuarios.html', usuarios=usuarios)

# ------------------- ROTA: Cadastrar Novo Usuário ------------------- #
@usuario_bp.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    perfis = Perfil.query.all()
    uls = UnidadeLocal.query.all()

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        matricula = request.form.get('matricula')
        ramal = request.form.get('ramal')
        perfil_id = request.form.get('perfil_id')
        unidade_local_id = request.form.get('unidade_local_id')

        # Verifica se o e-mail já está cadastrado
        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado. Use outro e-mail.', 'warning')
            return render_template('novo_usuario.html', usuario=None, perfis=perfis, uls=uls)

        novo = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            matricula=matricula,
            ramal=ramal,
            perfil_id=perfil_id,
            unidade_local_id=unidade_local_id,
            senha_temporaria=True
        )
        db.session.add(novo)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('usuario_bp.lista_usuarios'))

    return render_template('novo_usuario.html', usuario=None, perfis=perfis, uls=uls)


# ------------------- ROTA: Editar Usuário ------------------- #
@usuario_bp.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    perfis = Perfil.query.all()
    uls = UnidadeLocal.query.all()

    if request.method == 'POST':
        usuario.nome = request.form.get('nome')
        usuario.email = request.form.get('email')
        usuario.matricula = request.form.get('matricula')
        usuario.ramal = request.form.get('ramal')
        usuario.perfil_id = request.form.get('perfil_id')
        usuario.unidade_local_id = request.form.get('unidade_local_id')

        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)
            usuario.senha_temporaria = True

        db.session.commit()
        flash('Usuário atualizado com sucesso!')
        return redirect(url_for('usuario_bp.lista_usuarios'))

    return render_template('novo_usuario.html', usuario=usuario, perfis=perfis, uls=uls)


# ------------------- EXCLUSÃO DE USUÁRIO -------------------
@usuario_bp.route('/excluir/<int:id>', methods=['GET'])
@login_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('usuario_bp.lista_usuarios'))

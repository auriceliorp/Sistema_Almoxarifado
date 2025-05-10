# routes_usuario.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from werkzeug.security import generate_password_hash
from database import db
from models import Usuario, Perfil, UnidadeLocal

# Criação do blueprint para rotas de usuários
usuario_bp = Blueprint('usuario_bp', __name__, url_prefix='/usuario')

# ------------------- LISTAGEM DE USUÁRIOS -------------------
@usuario_bp.route('/')
@login_required
def lista_usuarios():
    usuarios = Usuario.query.all()
    return render_template('lista_usuarios.html', usuarios=usuarios)

# ------------------- CRIAÇÃO DE NOVO USUÁRIO -------------------
@usuario_bp.route('/novo', methods=['GET', 'POST'])
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
        perfil_id = request.form.get('perfil_id', type=int)
        unidade_local_id = request.form.get('unidade_local_id', type=int)

        if not (nome and email and senha and matricula and perfil_id and unidade_local_id):
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('usuario_bp.novo_usuario'))

        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            matricula=matricula,
            ramal=ramal,
            perfil_id=perfil_id,
            unidade_local_id=unidade_local_id,
            senha_temporaria=False
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('usuario_bp.lista_usuarios'))

    return render_template('novo_usuario.html', perfis=perfis, uls=uls)

# ------------------- EDIÇÃO DE USUÁRIO -------------------
@usuario_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
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
        usuario.perfil_id = request.form.get('perfil_id', type=int)
        usuario.unidade_local_id = request.form.get('unidade_local_id', type=int)

        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
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
# routes_usuario.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from werkzeug.security import generate_password_hash
from database import db
from models import Usuario, Perfil

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuario')

@usuario_bp.route('/')
@login_required
def lista_usuario():
    usuarios = Usuario.query.all()
    return render_template('lista_usuario.html', usuarios=usuarios)

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

        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return redirect(url_for('usuario.novo_usuario'))

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha),
            matricula=matricula,
            perfil_id=perfil_id
        )
        db.session.add(novo_usuario)
        db.session.commit()

        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('usuario.lista_usuario'))

    return render_template('novo_usuario.html', perfis=perfis)

@usuario_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!')
    return redirect(url_for('usuario.lista_usuario'))

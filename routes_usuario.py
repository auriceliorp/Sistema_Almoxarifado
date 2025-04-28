# routes_usuario.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from models import Usuario, Perfil
from database import db
from werkzeug.security import generate_password_hash

usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuario')

@usuario_bp.route('/')
@login_required
def lista_usuario():
    usuarios = Usuario.query.all()
    return render_template('lista_usuario.html', usuarios=usuarios)

@usuario_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo_usuario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        matricula = request.form.get('matricula')
        senha = request.form.get('senha')
        perfil_id = request.form.get('perfil_id')

        senha_hash = generate_password_hash(senha)

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            matricula=matricula,
            senha=senha_hash,
            perfil_id=perfil_id
        )
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('usuario.lista_usuario'))

    perfis = Perfil.query.all()
    return render_template('novo_usuario.html', perfis=perfis)

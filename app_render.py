# app_render.py

from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import db
from models import Usuario, Perfil, NaturezaDespesa, Item
from sqlalchemy import text, inspect

# Login Manager
login_manager = LoginManager()
login_manager.login_view = "main.login"

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None and str(user_id).isdigit():
        return Usuario.query.get(int(user_id))
    return None

# Blueprint principal
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            if getattr(usuario, 'senha_temporaria', False):
                return redirect(url_for('main.trocar_senha'))
            return redirect(url_for('main.home'))
        else:
            flash('E-mail ou senha inválidos.')
    return render_template('login.html')

@main.route('/trocar_s

